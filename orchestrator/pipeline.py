"""Pipeline Orchestrator coordinating validation, preprocessing, and tools."""

import logging
from typing import List, Optional

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
    DimensionScore,
    Issue,
    ReviewResult,
    ReviewSummary,
    SeverityEnum,
)
from input_handling import detect_language, preprocess_code, validate_input

logger = logging.getLogger(__name__)


def _compute_score_and_summary(
    fused_issues: List[Issue],
) -> tuple[CodeQualityScore, ReviewSummary]:
    """Computes deterministic quality scores and summary metrics."""
    critical_count = sum(
        1 for i in fused_issues if i.severity == SeverityEnum.CRITICAL
    )
    high_count = sum(
        1 for i in fused_issues if i.severity == SeverityEnum.HIGH
    )
    medium_count = sum(
        1 for i in fused_issues if i.severity == SeverityEnum.MEDIUM
    )
    low_count = sum(
        1 for i in fused_issues if i.severity == SeverityEnum.LOW
    )
    info_count = sum(
        1 for i in fused_issues if i.severity == SeverityEnum.INFORMATIONAL
    )

    total_issues = len(fused_issues)

    deductions = (
        critical_count * 25.0
        + high_count * 15.0
        + medium_count * 8.0
        + low_count * 3.0
        + info_count * 1.0
    )

    overall_score = max(0.0, min(100.0, 100.0 - deductions))

    if overall_score >= 90.0:
        label = "Excellent"
    elif overall_score >= 75.0:
        label = "Good"
    elif overall_score >= 50.0:
        label = "Needs Improvement"
    else:
        label = "Poor"

    # Group issue counts by dimension
    dim_security = sum(
        1 for i in fused_issues if i.category == CategoryEnum.SECURITY
    )
    dim_correctness = sum(
        1
        for i in fused_issues
        if i.category
        in (
            CategoryEnum.SYNTAX_ERROR,
            CategoryEnum.LOGICAL_BUG,
            CategoryEnum.RUNTIME_PROBLEM,
        )
    )
    dim_maintainability = sum(
        1
        for i in fused_issues
        if i.category
        in (
            CategoryEnum.MAINTAINABILITY,
            CategoryEnum.CODE_QUALITY,
            CategoryEnum.RESOURCE_MANAGEMENT,
        )
    )
    dim_readability = sum(
        1
        for i in fused_issues
        if i.category
        in (CategoryEnum.READABILITY, CategoryEnum.BEST_PRACTICE)
    )

    dimensions = [
        DimensionScore(
            dimension_name="Correctness",
            score=max(0.0, 100.0 - dim_correctness * 20.0),
            weight=0.35,
            deductions=dim_correctness * 20.0,
            issue_count=dim_correctness,
        ),
        DimensionScore(
            dimension_name="Security",
            score=max(0.0, 100.0 - dim_security * 25.0),
            weight=0.30,
            deductions=dim_security * 25.0,
            issue_count=dim_security,
        ),
        DimensionScore(
            dimension_name="Maintainability",
            score=max(0.0, 100.0 - dim_maintainability * 10.0),
            weight=0.20,
            deductions=dim_maintainability * 10.0,
            issue_count=dim_maintainability,
        ),
        DimensionScore(
            dimension_name="Readability & Style",
            score=max(0.0, 100.0 - dim_readability * 5.0),
            weight=0.15,
            deductions=dim_readability * 5.0,
            issue_count=dim_readability,
        ),
    ]

    summary = ReviewSummary(
        total_issues=total_issues,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        informational_count=info_count,
        executive_summary=(
            f"Static code review completed. Identified {total_issues} "
            f"finding(s) ({critical_count} critical, {high_count} high, "
            f"{medium_count} medium, {low_count} low)."
        ),
    )

    score = CodeQualityScore(
        overall_score=overall_score,
        label=label,
        dimensions=dimensions,
        summary_notes=(
            f"Code quality score: {overall_score:.1f}/100 ({label})."
        ),
    )

    return score, summary


class CodeReviewPipeline:
    """Orchestrates the end-to-end review process using component protocols."""

    def __init__(
        self,
        analyzers: Optional[List[StaticAnalyzerProtocol]] = None,
        ai_reviewer: Optional[AIReviewerProtocol] = None,
        fusion_service: Optional[FusionServiceProtocol] = None,
        report_builder: Optional[ReportBuilderProtocol] = None,
    ) -> None:
        self.analyzers = (
            analyzers if analyzers is not None else get_default_analyzers()
        )
        self.ai_reviewer = ai_reviewer
        self.fusion_service = fusion_service
        self.report_builder = report_builder

    def review_code(
        self, code: str, filename: str = "submitted_snippet"
    ) -> ReviewResult:
        """Executes the standard multi-stage code review flow.

        Pipeline Stages:
        1. Input validation
        2. Language detection
        3. Preprocessing & syntax checking
        4. Static analysis execution (isolated per analyzer)
        5. AI reasoning execution (optional)
        6. Finding fusion & deduplication (optional)
        7. Code quality scoring & summary calculation
        8. ReviewResult assembly
        """
        # Stage 1: Input Validation
        is_valid, error_msg = validate_input(code)
        if not is_valid:
            score = CodeQualityScore(
                overall_score=0.0,
                label="Invalid",
                summary_notes=error_msg or "Validation rejected the input.",
            )
            summary = ReviewSummary(
                total_issues=0,
                executive_summary=error_msg or "Input validation failed.",
            )
            return ReviewResult(
                issues=[],
                score=score,
                summary=summary,
                language="python",
                submitted_code=code or "",
            )

        # Stage 2: Language Detection
        detected_language = detect_language(code, filename=filename)

        # Stage 3: Preprocessing & Normalization
        normalized_code, syntax_issue = preprocess_code(
            code, filename=filename
        )

        # Stage 4: Static Analysis Execution
        static_issues: List[Issue] = []
        if syntax_issue is not None:
            static_issues.append(syntax_issue)

        for analyzer in self.analyzers:
            try:
                findings = analyzer.analyze(
                    normalized_code, filename=filename
                )
                if findings:
                    # Filter duplicate syntax errors
                    if syntax_issue is not None:
                        filtered = [
                            f
                            for f in findings
                            if f.category != CategoryEnum.SYNTAX_ERROR
                        ]
                        static_issues.extend(filtered)
                    else:
                        static_issues.extend(findings)
            except Exception as e:
                analyzer_name = getattr(
                    analyzer, "name", type(analyzer).__name__
                )
                logger.error(
                    f"Analyzer '{analyzer_name}' failed during analysis "
                    f"of {filename}: {e}",
                    exc_info=True,
                )

        # Stage 5: AI Reasoning Execution (optional boundary)
        ai_issues: List[Issue] = []
        if self.ai_reviewer:
            try:
                ai_issues = self.ai_reviewer.review(
                    normalized_code, static_issues=static_issues
                )
            except Exception as e:
                logger.error(
                    f"AI Reviewer execution error: {e}", exc_info=True
                )

        # Stage 6: Finding Fusion & Deduplication
        if self.fusion_service and (static_issues or ai_issues):
            try:
                fused_issues = self.fusion_service.fuse(
                    static_issues, ai_issues
                )
            except Exception as e:
                logger.error(f"Fusion service error: {e}", exc_info=True)
                fused_issues = static_issues + ai_issues
        else:
            fused_issues = static_issues + ai_issues

        # Stage 7 & 8: Scoring, Summary & Assembly
        score, summary = _compute_score_and_summary(fused_issues)

        return ReviewResult(
            issues=fused_issues,
            score=score,
            summary=summary,
            language=detected_language,
            submitted_code=normalized_code,
        )


def review_code(code: str) -> ReviewResult:
    """Public helper entry point for single-call code reviews."""
    pipeline = CodeReviewPipeline()
    return pipeline.review_code(code)
