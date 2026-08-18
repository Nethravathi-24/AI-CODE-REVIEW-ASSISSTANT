"""Pipeline Orchestrator coordinating input handling, static analysis, severity calculation, and result assembly."""

import logging
import time
from typing import List, Optional, Union

from analyzers import get_default_analyzers
from core.interfaces import (
    AIReviewerProtocol,
    FusionServiceProtocol,
    ReportBuilderProtocol,
    StaticAnalyzerProtocol,
)
from core.issue_model import (
    CodeQualityScore,
    DetectionSourceEnum,
    DimensionScore,
    Issue,
    PipelineError,
    PipelineResult,
    ReviewResult,
    ReviewSummary,
    SeverityEnum,
)
from core.severity import calculate_severity
from input_handling import (
    InputProcessingResult,
    PreprocessedCode,
    process_input,
)

logger = logging.getLogger(__name__)


def _compute_score_and_summary(issues: List[Issue]) -> tuple[CodeQualityScore, ReviewSummary]:
    """Computes code quality score and review summary counters from a list of issues."""
    critical_count = sum(1 for i in issues if i.severity == SeverityEnum.CRITICAL)
    high_count = sum(1 for i in issues if i.severity == SeverityEnum.HIGH)
    medium_count = sum(1 for i in issues if i.severity == SeverityEnum.MEDIUM)
    low_count = sum(1 for i in issues if i.severity == SeverityEnum.LOW)
    informational_count = sum(1 for i in issues if i.severity == SeverityEnum.INFORMATIONAL)
    total_issues = len(issues)

    # Calculate overall deductions
    # Deductions: Critical: 25, High: 15, Medium: 8, Low: 3, Informational: 1
    deductions = (
        critical_count * 25.0
        + high_count * 15.0
        + medium_count * 8.0
        + low_count * 3.0
        + informational_count * 1.0
    )
    overall_score = max(0.0, min(100.0, round(100.0 - deductions, 2)))

    if overall_score >= 90.0:
        label = "Excellent"
    elif overall_score >= 75.0:
        label = "Good"
    elif overall_score >= 50.0:
        label = "Fair"
    else:
        label = "Needs Improvement"

    # Category dimension grouping
    dimension_names = ["Correctness", "Security", "Maintainability", "Readability"]
    dimension_scores = []
    for dim_name in dimension_names:
        dim_issues = [i for i in issues if dim_name.lower() in i.category.value.lower()]
        dim_issue_count = len(dim_issues)
        dim_deductions = sum(
            25.0 if i.severity == SeverityEnum.CRITICAL
            else (15.0 if i.severity == SeverityEnum.HIGH
            else (8.0 if i.severity == SeverityEnum.MEDIUM
            else (3.0 if i.severity == SeverityEnum.LOW else 1.0)))
            for i in dim_issues
        )
        dim_score_val = max(0.0, min(100.0, round(100.0 - dim_deductions, 2)))
        dimension_scores.append(
            DimensionScore(
                dimension_name=dim_name,
                score=dim_score_val,
                weight=0.25,
                deductions=dim_deductions,
                issue_count=dim_issue_count,
            )
        )

    score = CodeQualityScore(
        overall_score=overall_score,
        label=label,
        dimensions=dimension_scores,
        summary_notes=(
            "Clean code review execution."
            if not issues
            else f"Static analysis completed with {total_issues} issue(s) detected."
        ),
    )

    summary = ReviewSummary(
        total_issues=total_issues,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        informational_count=informational_count,
        executive_summary=(
            f"Review completed. {total_issues} issue(s) detected across static analyzers."
            if issues
            else "Review completed successfully with no static issues detected."
        ),
    )

    return score, summary


class CodeReviewPipeline:
    """Orchestrates the end-to-end code review process using injected component protocols."""

    def __init__(
        self,
        analyzers: Optional[List[StaticAnalyzerProtocol]] = None,
        ai_reviewer: Optional[AIReviewerProtocol] = None,
        fusion_service: Optional[FusionServiceProtocol] = None,
        report_builder: Optional[ReportBuilderProtocol] = None,
    ) -> None:
        self.analyzers: List[StaticAnalyzerProtocol] = (
            analyzers if analyzers is not None else get_default_analyzers()
        )
        self.ai_reviewer = ai_reviewer
        self.fusion_service = fusion_service
        self.report_builder = report_builder

    def run(
        self,
        code: Union[str, bytes, None],
        filename: str = "submitted_snippet",
        manual_override: Optional[str] = None,
        language_override: Optional[str] = None,
    ) -> PipelineResult:
        """Executes the full code review pipeline returning a comprehensive PipelineResult.

        Pipeline Stages:
        1. Input validation (stops immediately if invalid, without running analyzers)
        2. Language detection
        3. Code preprocessing (line normalization & AST syntax check)
        4. Static analysis execution (with isolated error handling per analyzer)
        5. Severity processing & scoring
        6. Result assembly into ReviewResult and PipelineResult
        """
        override_lang = manual_override or language_override
        start_time = time.perf_counter()
        errors: List[PipelineError] = []
        warnings: List[str] = []
        is_partial_analysis = False

        # Stage 1-3: Input Handling (Validation -> Language Detection -> Preprocessing)
        input_result: InputProcessingResult = process_input(
            code=code,
            filename=filename,
            manual_override=override_lang,
        )

        # 1. Validation check: stop immediately if invalid
        if not input_result.is_valid:
            error_type = (
                input_result.validation.error_type.value
                if input_result.validation.error_type
                else "ValidationError"
            )
            err_msg = input_result.error_message or "Input validation failed."
            errors.append(
                PipelineError(
                    error_type=error_type,
                    message=err_msg,
                    stage="input_validation",
                    is_fatal=True,
                )
            )
            elapsed = round(time.perf_counter() - start_time, 4)
            return PipelineResult(
                success=False,
                review_result=None,
                errors=errors,
                warnings=warnings,
                is_partial_analysis=False,
                execution_time_seconds=elapsed,
            )

        detected_language = (
            input_result.language.language if input_result.language else "python"
        )
        preprocessed: PreprocessedCode = input_result.preprocessed
        effective_code = preprocessed.normalized_code
        submitted_code = input_result.validation.raw_code

        collected_issues: List[Issue] = []

        # Check for syntax error during preprocessing
        if not preprocessed.is_valid_syntax and preprocessed.syntax_error:
            collected_issues.append(preprocessed.syntax_error)
            warnings.append(
                f"Syntax error detected on line {preprocessed.syntax_error.line_start}: "
                f"{preprocessed.syntax_error.description}"
            )
            is_partial_analysis = True

        # Stage 4: Static Analyzers Execution with Error Isolation (executed for syntactically valid code)
        if preprocessed.is_valid_syntax:
            for analyzer in self.analyzers:
                analyzer_name = getattr(analyzer, "name", type(analyzer).__name__)
                try:
                    analyzer_issues = analyzer.analyze(effective_code, filename=filename)
                    if analyzer_issues:
                        collected_issues.extend(analyzer_issues)
                except Exception as exc:
                    logger.error(
                        "Static analyzer '%s' failed during execution: %s",
                        analyzer_name,
                        exc,
                        exc_info=True,
                    )
                    warnings.append(f"Static analyzer '{analyzer_name}' failed: {exc}")
                    errors.append(
                        PipelineError(
                            error_type=type(exc).__name__,
                            message=str(exc),
                            stage="static_analysis",
                            is_fatal=False,
                        )
                    )
                    is_partial_analysis = True

        # Stage 5: Severity Processing
        for issue in collected_issues:
            is_corroborated = issue.detection_source == DetectionSourceEnum.BOTH
            issue.severity = calculate_severity(
                category=issue.category,
                confidence=issue.confidence,
                is_corroborated=is_corroborated,
            )

        # Stage 6: Scoring & Summary Computation
        score, summary = _compute_score_and_summary(collected_issues)

        # Stage 7: Assemble ReviewResult & PipelineResult
        review_result = ReviewResult(
            issues=collected_issues,
            score=score,
            summary=summary,
            language=detected_language,
            submitted_code=submitted_code,
        )

        elapsed = round(time.perf_counter() - start_time, 4)
        return PipelineResult(
            success=True,
            review_result=review_result,
            errors=errors,
            warnings=warnings,
            is_partial_analysis=is_partial_analysis,
            execution_time_seconds=elapsed,
        )

    def run_pipeline(
        self,
        code: Union[str, bytes, None],
        filename: str = "submitted_snippet",
        manual_override: Optional[str] = None,
        language_override: Optional[str] = None,
    ) -> PipelineResult:
        """Alias method for run()."""
        return self.run(
            code=code,
            filename=filename,
            manual_override=manual_override,
            language_override=language_override,
        )

    def review_code(
        self,
        code: Union[str, bytes, None],
        filename: str = "submitted_snippet",
        manual_override: Optional[str] = None,
        language_override: Optional[str] = None,
    ) -> ReviewResult:
        """Executes the standard review flow and directly returns the ReviewResult.

        Raises:
            ValueError: If input validation fails.
        """
        pipeline_res = self.run(
            code,
            filename=filename,
            manual_override=manual_override,
            language_override=language_override,
        )
        if not pipeline_res.success or pipeline_res.review_result is None:
            err_msg = (
                pipeline_res.errors[0].message
                if pipeline_res.errors
                else "Input validation failed."
            )
            raise ValueError(err_msg)
        return pipeline_res.review_result


def run_pipeline(
    code: Union[str, bytes, None],
    filename: str = "submitted_snippet",
    manual_override: Optional[str] = None,
    language_override: Optional[str] = None,
) -> PipelineResult:
    """Public helper entry point executing pipeline and returning full PipelineResult."""
    pipeline = CodeReviewPipeline()
    return pipeline.run(
        code=code,
        filename=filename,
        manual_override=manual_override,
        language_override=language_override,
    )


def review_code(
    code: Union[str, bytes, None],
    filename: str = "submitted_snippet",
    manual_override: Optional[str] = None,
    language_override: Optional[str] = None,
) -> ReviewResult:
    """Public helper entry point executing pipeline and returning ReviewResult."""
    pipeline = CodeReviewPipeline()
    return pipeline.review_code(
        code=code,
        filename=filename,
        manual_override=manual_override,
        language_override=language_override,
    )
