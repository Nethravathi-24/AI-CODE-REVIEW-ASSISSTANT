"""Unit tests for the PRD Part 15 7-Dimension Code Quality Scoring Engine."""

import pytest
from core.issue_model import CategoryEnum, DetectionSourceEnum, Issue, SeverityEnum
from core.scoring import compute_score_and_summary


def test_perfect_score_when_no_issues():
    """Test 1: Zero issues produce a perfect 100.0 Excellent score."""
    score, summary = compute_score_and_summary([])
    assert score.overall_score == 100.0
    assert score.label == "Excellent"
    assert len(score.dimensions) == 7
    for dim in score.dimensions:
        assert dim.score == 100.0
        assert dim.issue_count == 0


def test_critical_issue_deduction_and_label():
    """Test 2: Critical issues deduct 25 points from affected dimension and overall score."""
    critical_issue = Issue(
        issue_id="crit_1",
        category=CategoryEnum.SECURITY,
        severity=SeverityEnum.CRITICAL,
        confidence=1.0,
        line_start=5,
        line_end=5,
        code_snippet="eval(x)",
        description="Dangerous eval execution",
        why_it_matters="Allows arbitrary code execution",
        detection_source=DetectionSourceEnum.STATIC,
    )
    score, summary = compute_score_and_summary([critical_issue])

    # Security weight is 0.25. 100 - 25 = 75 in Security dim.
    # Overall score = 0.25*75 + 0.75*100 = 18.75 + 75 = 93.8 (or rounded to 93.8)
    security_dim = next(d for d in score.dimensions if d.dimension_name == "Security")
    assert security_dim.score == 75.0
    assert security_dim.issue_count == 1
    assert score.overall_score == 75.0
    assert score.label == "Good"


def test_high_medium_low_info_issues_deductions():
    """Test 3: Verify deductions for High (-15), Medium (-8), Low (-3), Informational (-1)."""
    high_issue = Issue(
        issue_id="high_1",
        category=CategoryEnum.LOGICAL_BUG,  # Correctness (weight 0.25)
        severity=SeverityEnum.HIGH,
        confidence=1.0,
        line_start=1,
        line_end=1,
        code_snippet="a / b",
        description="Logic error",
        why_it_matters="Crash risk",
        detection_source=DetectionSourceEnum.STATIC,
    )
    med_issue = Issue(
        issue_id="med_1",
        category=CategoryEnum.MAINTAINABILITY,  # Maintainability (weight 0.15)
        severity=SeverityEnum.MEDIUM,
        confidence=1.0,
        line_start=2,
        line_end=2,
        code_snippet="complex_fn()",
        description="High complexity",
        why_it_matters="Hard to maintain",
        detection_source=DetectionSourceEnum.STATIC,
    )
    low_issue = Issue(
        issue_id="low_1",
        category=CategoryEnum.READABILITY,  # Readability (weight 0.10)
        severity=SeverityEnum.LOW,
        confidence=1.0,
        line_start=3,
        line_end=3,
        code_snippet="x=1",
        description="Whitespace formatting",
        why_it_matters="PEP 8 compliance",
        detection_source=DetectionSourceEnum.STATIC,
    )
    info_issue = Issue(
        issue_id="info_1",
        category=CategoryEnum.BEST_PRACTICE,  # Best Practices (weight 0.10)
        severity=SeverityEnum.INFORMATIONAL,
        confidence=1.0,
        line_start=4,
        line_end=4,
        code_snippet="# TODO",
        description="TODO comment found",
        why_it_matters="Tracked item",
        detection_source=DetectionSourceEnum.STATIC,
    )

    score, summary = compute_score_and_summary([high_issue, med_issue, low_issue, info_issue])

    correctness_dim = next(d for d in score.dimensions if d.dimension_name == "Correctness")
    assert correctness_dim.score == 85.0  # 100 - 15

    maint_dim = next(d for d in score.dimensions if d.dimension_name == "Maintainability")
    assert maint_dim.score == 92.0  # 100 - 8

    read_dim = next(d for d in score.dimensions if d.dimension_name == "Readability")
    assert read_dim.score == 97.0  # 100 - 3

    bp_dim = next(d for d in score.dimensions if d.dimension_name == "Best Practices")
    assert bp_dim.score == 99.0  # 100 - 1

    assert summary.total_issues == 4
    assert summary.high_count == 1
    assert summary.medium_count == 1
    assert summary.low_count == 1
    assert summary.informational_count == 1


def test_score_boundaries_floored_at_zero():
    """Test 4: Multiple critical issues floor dimension score and overall score at 0.0."""
    many_issues = [
        Issue(
            issue_id=f"crit_{i}",
            category=CategoryEnum.SECURITY,
            severity=SeverityEnum.CRITICAL,
            confidence=1.0,
            line_start=i + 1,
            line_end=i + 1,
            code_snippet=f"eval({i})",
            description="API secret leaked",
            why_it_matters="Exposes credentials",
            detection_source=DetectionSourceEnum.STATIC,
        )
        for i in range(5)  # 5 * 25 = 125 deduction -> floored to 0.0
    ]
    # Add critical issues across all categories so all dimensions hit 0
    all_cat_issues = []
    for i, cat in enumerate(CategoryEnum):
        for _ in range(5):
            all_cat_issues.append(
                Issue(
                    issue_id=f"crit_all_{i}",
                    category=cat,
                    severity=SeverityEnum.CRITICAL,
                    confidence=1.0,
                    line_start=1,
                    line_end=1,
                    code_snippet="bad()",
                    description="Critical failure",
                    why_it_matters="Critical risk",
                    detection_source=DetectionSourceEnum.STATIC,
                )
            )

    score, summary = compute_score_and_summary(all_cat_issues)
    for dim in score.dimensions:
        assert dim.score == 0.0
    assert score.overall_score == 0.0
    assert score.label == "Critical Issues Present"


def test_all_seven_dimensions_present_and_weights_sum_to_one():
    """Test 5: Verify all 7 PRD dimensions are computed and weights sum to 1.0."""
    score, summary = compute_score_and_summary([])
    dim_names = {d.dimension_name for d in score.dimensions}
    expected_dims = {
        "Correctness",
        "Security",
        "Maintainability",
        "Readability",
        "Performance",
        "Best Practices",
        "Testability",
    }
    assert dim_names == expected_dims
    total_weight = sum(d.weight for d in score.dimensions)
    assert abs(total_weight - 1.0) < 1e-6
