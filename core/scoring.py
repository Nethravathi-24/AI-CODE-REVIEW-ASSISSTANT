"""PRD Part 15 7-Dimension Code Quality Scoring & Executive Summary Engine."""

from typing import List, Tuple
from core.issue_model import (
    CategoryEnum,
    CodeQualityScore,
    DimensionScore,
    Issue,
    ReviewSummary,
    SeverityEnum,
)

# Severity Point Deduction Table per PRD Part 15.2
SEVERITY_DEDUCTIONS = {
    SeverityEnum.CRITICAL: 25.0,
    SeverityEnum.HIGH: 15.0,
    SeverityEnum.MEDIUM: 8.0,
    SeverityEnum.LOW: 3.0,
    SeverityEnum.INFORMATIONAL: 1.0,
}

# 7-Dimension Specs per PRD Part 15.1 (Dimension Name, Weight, Target Categories)
DIMENSION_SPECS = [
    (
        "Correctness",
        0.25,
        {
            CategoryEnum.SYNTAX_ERROR,
            CategoryEnum.LOGICAL_BUG,
            CategoryEnum.RUNTIME_PROBLEM,
            CategoryEnum.ERROR_HANDLING,
            CategoryEnum.RESOURCE_MANAGEMENT,
        },
    ),
    (
        "Security",
        0.25,
        {CategoryEnum.SECURITY},
    ),
    (
        "Maintainability",
        0.15,
        {
            CategoryEnum.MAINTAINABILITY,
            CategoryEnum.CODE_QUALITY,
            CategoryEnum.DUPLICATE_LOGIC,
        },
    ),
    (
        "Readability",
        0.10,
        {CategoryEnum.READABILITY},
    ),
    (
        "Performance",
        0.10,
        {CategoryEnum.PERFORMANCE},
    ),
    (
        "Best Practices",
        0.10,
        {CategoryEnum.BEST_PRACTICE},
    ),
    (
        "Testability",
        0.05,
        {CategoryEnum.EDGE_CASE},
    ),
]


def compute_score_and_summary(issues: List[Issue]) -> Tuple[CodeQualityScore, ReviewSummary]:
    """Computes the deterministic 7-dimension code quality score and review summary per PRD Part 15.

    Args:
        issues: List of resolved/fused Issue objects.

    Returns:
        Tuple[CodeQualityScore, ReviewSummary]: Computed quality score model and summary model.
    """
    critical_count = sum(1 for i in issues if i.severity == SeverityEnum.CRITICAL)
    high_count = sum(1 for i in issues if i.severity == SeverityEnum.HIGH)
    medium_count = sum(1 for i in issues if i.severity == SeverityEnum.MEDIUM)
    low_count = sum(1 for i in issues if i.severity == SeverityEnum.LOW)
    informational_count = sum(1 for i in issues if i.severity == SeverityEnum.INFORMATIONAL)
    total_issues = len(issues)

    dimension_scores: List[DimensionScore] = []
    weighted_score_sum = 0.0

    for dim_name, weight, categories in DIMENSION_SPECS:
        # Find issues matching this dimension's categories
        dim_issues = [i for i in issues if i.category in categories]
        dim_deductions = sum(SEVERITY_DEDUCTIONS.get(i.severity, 1.0) for i in dim_issues)
        dim_score_val = max(0.0, min(100.0, round(100.0 - dim_deductions, 2)))

        dimension_scores.append(
            DimensionScore(
                dimension_name=dim_name,
                score=dim_score_val,
                weight=weight,
                deductions=dim_deductions,
                issue_count=len(dim_issues),
            )
        )
        weighted_score_sum += dim_score_val * weight

    overall_deduction = (
        critical_count * 25.0
        + high_count * 15.0
        + medium_count * 8.0
        + low_count * 3.0
        + informational_count * 1.0
    )
    overall_score = max(0.0, min(100.0, round(min(weighted_score_sum, 100.0 - overall_deduction), 1)))

    # PRD Part 15.4 Labels
    if overall_score >= 90.0:
        label = "Excellent"
    elif overall_score >= 75.0:
        label = "Good"
    elif overall_score >= 60.0:
        label = "Needs Improvement"
    elif overall_score >= 40.0:
        label = "Poor"
    else:
        label = "Critical Issues Present"

    summary_notes = (
        "Clean code review execution — zero issues detected."
        if not issues
        else f"Review completed with {total_issues} issue(s) across {len(dimension_scores)} quality dimensions."
    )

    score = CodeQualityScore(
        overall_score=overall_score,
        label=label,
        dimensions=dimension_scores,
        summary_notes=summary_notes,
    )

    executive_summary = (
        f"Review completed. {total_issues} issue(s) detected across quality analyzers."
        if issues
        else "Review completed successfully with no issues detected."
    )

    summary = ReviewSummary(
        total_issues=total_issues,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        informational_count=informational_count,
        executive_summary=executive_summary,
    )

    return score, summary
