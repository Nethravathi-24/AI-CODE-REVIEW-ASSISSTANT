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
    CategoryEnum,
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


from core.scoring import compute_score_and_summary

# Alias for internal backwards compatibility
_compute_score_and_summary = compute_score_and_summary


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
        """Executes the full code review pipeline returning a comprehensive PipelineResult."""
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

        static_issues: List[Issue] = []

        # Check for syntax error during preprocessing
        if not preprocessed.is_valid_syntax and preprocessed.syntax_error:
            static_issues.append(preprocessed.syntax_error)
            warnings.append(
                f"Syntax error detected on line {preprocessed.syntax_error.line_start}: "
                f"{preprocessed.syntax_error.description}"
            )
            is_partial_analysis = True

        # Stage 4: Static Analyzers Execution
        if preprocessed.is_valid_syntax:
            for analyzer in self.analyzers:
                analyzer_name = getattr(analyzer, "name", type(analyzer).__name__)
                try:
                    analyzer_issues = analyzer.analyze(effective_code, filename=filename)
                    if analyzer_issues:
                        static_issues.extend(analyzer_issues)
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

        # Stage 5: AI Review Execution (Optional / Graceful Degrade)
        ai_issues: List[Issue] = []
        if self.ai_reviewer and preprocessed.is_valid_syntax:
            try:
                ai_issues = self.ai_reviewer.review(effective_code, static_issues=static_issues)
            except Exception as exc:
                logger.error("AI Reviewer failed: %s", exc, exc_info=True)
                warnings.append(f"AI review skipped due to execution error: {exc}")

        # Stage 6: Result Fusion & Deduplication
        from fusion import FusionService
        fusion_svc = self.fusion_service or FusionService()
        collected_issues = fusion_svc.fuse(static_issues, ai_issues)

        # Stage 7: Severity Recalculation
        for issue in collected_issues:
            is_corroborated = issue.detection_source == DetectionSourceEnum.BOTH
            issue.severity = calculate_severity(
                category=issue.category,
                confidence=issue.confidence,
                is_corroborated=is_corroborated,
            )

        # Stage 8: Remediation (Fix & Test Generation)
        from remediation import FixGenerator, TestGenerator
        fix_gen = FixGenerator()
        test_gen = TestGenerator()

        for issue in collected_issues:
            if not issue.fix:
                issue.fix = fix_gen.generate_fix(issue, effective_code)
            if not issue.generated_test:
                issue.generated_test = test_gen.generate_test(issue, effective_code)

        # Stage 9: 7-Dimension Quality Scoring & Summary
        score, summary = _compute_score_and_summary(collected_issues)

        # Stage 10: ReviewResult Assembly
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
