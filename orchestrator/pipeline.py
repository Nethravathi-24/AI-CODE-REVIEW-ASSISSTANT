"""Pipeline Orchestrator connecting input handling, static analyzers, and review reporting."""

import time
from typing import List, Optional

from analyzers import BaseAnalyzer, get_default_analyzers
from core.interfaces import (
    AIReviewerProtocol,
    FusionServiceProtocol,
    ReportBuilderProtocol,
    StaticAnalyzerProtocol,
)
from core.issue_model import (
    CategoryEnum,
    CodeQualityScore,
    DimensionScore,
    Issue,
    PipelineError,
    PipelineResult,
    ReviewResult,
    ReviewSummary,
    SeverityEnum,
)
from input_handling import process_input


class CodeReviewPipeline:
    """Orchestrates the end-to-end code review process using input handling and static analyzers."""

    def __init__(
        self,
        analyzers: Optional[List[StaticAnalyzerProtocol]] = None,
        ai_reviewer: Optional[AIReviewerProtocol] = None,
        fusion_service: Optional[FusionServiceProtocol] = None,
        report_builder: Optional[ReportBuilderProtocol] = None,
    ) -> None:
        self.analyzers = analyzers if analyzers is not None else get_default_analyzers()
        self.ai_reviewer = ai_reviewer
        self.fusion_service = fusion_service
        self.report_builder = report_builder

    def run_pipeline(
        self,
        code: str,
        filename: str = "submitted_snippet",
        language_override: Optional[str] = None,
    ) -> PipelineResult:
        """Executes the complete static review pipeline returning a structured PipelineResult.

        Flow:
        1. Input Validation & Preprocessing (size, encoding, binary safety, AST parse)
        2. Language Detection
        3. Deterministic Static Analysis Execution (AST, Pyflakes, Bandit, Radon, Pycodestyle)
        4. Severity aggregation & Quality Scoring

        Args:
            code: Raw code text to analyze.
            filename: Identifier or filename for tracking.
            language_override: Optional manual language selection.

        Returns:
            PipelineResult: Structured execution output containing ReviewResult or PipelineError.
        """
        start_time = time.time()

        # 1. Input Handling & Preprocessing
        input_result = process_input(
            code=code,
            filename=filename,
            manual_override=language_override,
        )

        if not input_result.is_valid:
            err_type = (
                input_result.validation.error_type.value
                if input_result.validation.error_type
                else "validation_error"
            )
            return PipelineResult(
                success=False,
                errors=[
                    PipelineError(
                        error_type=err_type,
                        message=input_result.error_message or "Input validation failed",
                        stage="input_validation",
                        is_fatal=True,
                    )
                ],
                execution_time_seconds=round(time.time() - start_time, 3),
            )

        preprocessed = input_result.preprocessed
        normalized_code = preprocessed.normalized_code if preprocessed else code

        # 2. Static Analysis Execution
        static_issues: List[Issue] = []

        # Include syntax error issue if AST parsing failed during preprocessing
        if preprocessed and preprocessed.syntax_error:
            static_issues.append(preprocessed.syntax_error)

        for analyzer in self.analyzers:
            try:
                found_issues = analyzer.analyze(normalized_code, filename=filename)
                static_issues.extend(found_issues)
            except Exception as e:
                # Fault isolation: individual analyzer failure does not crash pipeline
                continue

        # Deduplicate issues with identical line_start, category, and description
        seen_keys = set()
        unique_issues: List[Issue] = []
        for issue in static_issues:
            key = (issue.line_start, issue.category, issue.description)
            if key not in seen_keys:
                seen_keys.add(key)
                unique_issues.append(issue)

        # 3. Severity & Issue Counting
        crit_count = sum(1 for i in unique_issues if i.severity == SeverityEnum.CRITICAL)
        high_count = sum(1 for i in unique_issues if i.severity == SeverityEnum.HIGH)
        med_count = sum(1 for i in unique_issues if i.severity == SeverityEnum.MEDIUM)
        low_count = sum(1 for i in unique_issues if i.severity == SeverityEnum.LOW)
        info_count = sum(1 for i in unique_issues if i.severity == SeverityEnum.INFORMATIONAL)
        total_count = len(unique_issues)

        # 4. Code Quality Score Calculation
        deductions = (crit_count * 25.0) + (high_count * 15.0) + (med_count * 5.0) + (low_count * 2.0) + (info_count * 0.5)
        overall_score = max(0.0, min(100.0, 100.0 - deductions))

        if overall_score >= 90.0:
            score_label = "Excellent"
        elif overall_score >= 75.0:
            score_label = "Good"
        elif overall_score >= 50.0:
            score_label = "Needs Improvement"
        else:
            score_label = "Poor"

        dimensions = [
            DimensionScore(
                dimension_name="Correctness",
                score=max(0.0, 100.0 - (crit_count * 30.0 + high_count * 20.0)),
                weight=0.25,
                deductions=crit_count * 30.0 + high_count * 20.0,
                issue_count=crit_count + high_count,
            ),
            DimensionScore(
                dimension_name="Security",
                score=max(
                    0.0,
                    100.0
                    - sum(
                        15.0
                        for i in unique_issues
                        if i.category == CategoryEnum.SECURITY
                    ),
                ),
                weight=0.25,
                deductions=sum(
                    15.0 for i in unique_issues if i.category == CategoryEnum.SECURITY
                ),
                issue_count=sum(
                    1 for i in unique_issues if i.category == CategoryEnum.SECURITY
                ),
            ),
            DimensionScore(
                dimension_name="Maintainability",
                score=max(
                    0.0,
                    100.0
                    - sum(
                        10.0
                        for i in unique_issues
                        if i.category
                        in (CategoryEnum.MAINTAINABILITY, CategoryEnum.CODE_QUALITY)
                    ),
                ),
                weight=0.20,
                deductions=sum(
                    10.0
                    for i in unique_issues
                    if i.category
                    in (CategoryEnum.MAINTAINABILITY, CategoryEnum.CODE_QUALITY)
                ),
                issue_count=sum(
                    1
                    for i in unique_issues
                    if i.category
                    in (CategoryEnum.MAINTAINABILITY, CategoryEnum.CODE_QUALITY)
                ),
            ),
            DimensionScore(
                dimension_name="Readability",
                score=max(
                    0.0,
                    100.0
                    - sum(
                        5.0
                        for i in unique_issues
                        if i.category
                        in (CategoryEnum.READABILITY, CategoryEnum.BEST_PRACTICE)
                    ),
                ),
                weight=0.15,
                deductions=sum(
                    5.0
                    for i in unique_issues
                    if i.category
                    in (CategoryEnum.READABILITY, CategoryEnum.BEST_PRACTICE)
                ),
                issue_count=sum(
                    1
                    for i in unique_issues
                    if i.category
                    in (CategoryEnum.READABILITY, CategoryEnum.BEST_PRACTICE)
                ),
            ),
        ]

        score_model = CodeQualityScore(
            overall_score=round(overall_score, 1),
            label=score_label,
            dimensions=dimensions,
            summary_notes=f"Calculated deterministically from {total_count} static analysis findings.",
        )

        summary_model = ReviewSummary(
            total_issues=total_count,
            critical_count=crit_count,
            high_count=high_count,
            medium_count=med_count,
            low_count=low_count,
            informational_count=info_count,
            executive_summary=(
                "Clean scan — no static analysis issues detected."
                if total_count == 0
                else f"Static analysis identified {total_count} issue(s) across {len(set(i.category for i in unique_issues))} category/categories."
            ),
        )

        detected_lang = (
            input_result.language.language
            if input_result.language
            else "python"
        )

        review_result = ReviewResult(
            issues=unique_issues,
            score=score_model,
            summary=summary_model,
            language=detected_lang,
            submitted_code=code,
        )

        return PipelineResult(
            success=True,
            review_result=review_result,
            execution_time_seconds=round(time.time() - start_time, 3),
        )

    def review_code(
        self,
        code: str,
        filename: str = "submitted_snippet",
        language_override: Optional[str] = None,
    ) -> ReviewResult:
        """Helper entry point executing review and returning ReviewResult directly."""
        pipeline_res = self.run_pipeline(
            code=code, filename=filename, language_override=language_override
        )
        if pipeline_res.review_result:
            return pipeline_res.review_result

        # If validation error occurred, raise clean ValueError
        error_msg = (
            pipeline_res.errors[0].message
            if pipeline_res.errors
            else "Code review pipeline failed."
        )
        raise ValueError(error_msg)


def run_pipeline(
    code: str,
    filename: str = "submitted_snippet",
    language_override: Optional[str] = None,
) -> PipelineResult:
    """Public helper executing pipeline and returning PipelineResult."""
    pipeline = CodeReviewPipeline()
    return pipeline.run_pipeline(
        code=code, filename=filename, language_override=language_override
    )


def review_code(
    code: str,
    filename: str = "submitted_snippet",
    language_override: Optional[str] = None,
) -> ReviewResult:
    """Public helper entry point returning ReviewResult."""
    pipeline = CodeReviewPipeline()
    return pipeline.review_code(
        code=code, filename=filename, language_override=language_override
    )
