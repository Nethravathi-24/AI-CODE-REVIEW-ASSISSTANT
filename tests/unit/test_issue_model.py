"""Unit tests for Pydantic domain models in core/issue_model.py."""

import json
import pytest
from pydantic import ValidationError

from core.issue_model import (
    CategoryEnum,
    CodeQualityScore,
    DetectionSourceEnum,
    DimensionScore,
    Fix,
    GeneratedTest,
    Issue,
    PipelineError,
    PipelineResult,
    ReviewResult,
    ReviewSummary,
    SeverityEnum,
    ValidationStatusEnum,
)


def test_valid_issue_creation():
    """Test 1: Valid Issue creation with required and optional fields."""
    issue = Issue(
        issue_id="issue-001",
        category=CategoryEnum.SECURITY,
        severity=SeverityEnum.HIGH,
        confidence=0.95,
        line_start=10,
        line_end=12,
        code_snippet="cursor.execute('SELECT * FROM users WHERE id = ' + user_input)",
        description="Potential SQL Injection vulnerability.",
        why_it_matters="User input concatenated directly into SQL query allows unauthorized database access.",
        detection_source=DetectionSourceEnum.STATIC,
        detecting_tool="bandit",
        references=["CWE-89"],
    )
    assert issue.issue_id == "issue-001"
    assert issue.category == CategoryEnum.SECURITY
    assert issue.severity == SeverityEnum.HIGH
    assert issue.confidence == 0.95
    assert issue.line_start == 10
    assert issue.line_end == 12
    assert issue.references == ["CWE-89"]


def test_invalid_confidence_values():
    """Test 2: Invalid confidence values (< 0.0 or > 1.0) raise ValidationError."""
    with pytest.raises(ValidationError):
        Issue(
            issue_id="issue-bad-conf-low",
            category=CategoryEnum.LOGICAL_BUG,
            severity=SeverityEnum.MEDIUM,
            confidence=-0.1,  # Must be >= 0.0
            line_start=1,
            line_end=2,
            code_snippet="x = 1",
            description="Bad conf",
            why_it_matters="Test",
            detection_source=DetectionSourceEnum.AI,
        )

    with pytest.raises(ValidationError):
        Issue(
            issue_id="issue-bad-conf-high",
            category=CategoryEnum.LOGICAL_BUG,
            severity=SeverityEnum.MEDIUM,
            confidence=1.5,  # Must be <= 1.0
            line_start=1,
            line_end=2,
            code_snippet="x = 1",
            description="Bad conf",
            why_it_matters="Test",
            detection_source=DetectionSourceEnum.AI,
        )


def test_invalid_line_numbers():
    """Test 3: Invalid line numbers (line_start < 1 or line_end < line_start) raise ValidationError."""
    # line_start < 1
    with pytest.raises(ValidationError):
        Issue(
            issue_id="issue-line-0",
            category=CategoryEnum.READABILITY,
            severity=SeverityEnum.LOW,
            confidence=0.8,
            line_start=0,  # Invalid: ge=1 required
            line_end=2,
            code_snippet="foo()",
            description="Line zero",
            why_it_matters="Test",
            detection_source=DetectionSourceEnum.STATIC,
        )

    # line_end < line_start
    with pytest.raises(ValidationError):
        Issue(
            issue_id="issue-inverted-lines",
            category=CategoryEnum.READABILITY,
            severity=SeverityEnum.LOW,
            confidence=0.8,
            line_start=10,
            line_end=5,  # Invalid: line_end < line_start
            code_snippet="foo()",
            description="Inverted lines",
            why_it_matters="Test",
            detection_source=DetectionSourceEnum.STATIC,
        )


def test_invalid_enum_values():
    """Test 4: Invalid enum string values raise ValidationError."""
    with pytest.raises(ValidationError):
        Issue(
            issue_id="issue-bad-enum",
            category="non_existent_category",  # type: ignore
            severity=SeverityEnum.LOW,
            confidence=0.5,
            line_start=1,
            line_end=1,
            code_snippet="pass",
            description="Bad category",
            why_it_matters="Test",
            detection_source=DetectionSourceEnum.STATIC,
        )


def test_optional_fields_defaults():
    """Test 5: Optional fields default safely to None or default values."""
    issue = Issue(
        issue_id="issue-minimal",
        category=CategoryEnum.BEST_PRACTICE,
        severity=SeverityEnum.INFORMATIONAL,
        confidence=1.0,
        line_start=5,
        line_end=5,
        code_snippet="x == None",
        description="Use 'is None'",
        why_it_matters="PEP 8 guideline",
        detection_source=DetectionSourceEnum.STATIC,
    )
    assert issue.file == "submitted_snippet"
    assert issue.column is None
    assert issue.root_cause is None
    assert issue.fix is None
    assert issue.generated_test is None
    assert issue.detecting_tool is None
    assert issue.references is None


def test_fix_serialization():
    """Test 6: Fix model creation, serialization, and deserialization."""
    fix = Fix(
        suggested_fix="Use parameterized query",
        corrected_code="cursor.execute('SELECT * FROM users WHERE id = %s', (user_input,))",
        diff="--- original\n+++ fixed\n- query string\n+ parameterized",
        validation_status=ValidationStatusEnum.PASSED,
    )
    fix_dict = fix.model_dump()
    assert fix_dict["validation_status"] == "passed"

    fix_json = fix.model_dump_json()
    reconstructed = Fix.model_validate_json(fix_json)
    assert reconstructed.suggested_fix == fix.suggested_fix
    assert reconstructed.validation_status == ValidationStatusEnum.PASSED


def test_generated_test_serialization():
    """Test 7: GeneratedTest creation and serialization."""
    gen_test = GeneratedTest(
        issue_id="issue-001",
        test_code="def test_sql_injection(): assert True",
        explanation="Verifies SQL query parameterization prevents injection.",
        target_category=CategoryEnum.SECURITY,
        validation_status=ValidationStatusEnum.PASSED,
    )
    test_json = gen_test.model_dump_json()
    reconstructed = GeneratedTest.model_validate_json(test_json)
    assert reconstructed.issue_id == "issue-001"
    assert reconstructed.target_category == CategoryEnum.SECURITY


def test_review_result_serialization():
    """Test 8: Full ReviewResult model assembly and clean JSON round-trip."""
    dim_score = DimensionScore(
        dimension_name="Security", score=75.0, weight=0.25, deductions=25.0, issue_count=1
    )
    score = CodeQualityScore(
        overall_score=93.75,
        label="Excellent",
        dimensions=[dim_score],
        summary_notes="Clean overall with one security note.",
    )
    summary = ReviewSummary(
        total_issues=1,
        high_count=1,
        executive_summary="Found 1 security issue.",
        top_recommendations=["Fix SQL injection."],
    )
    issue = Issue(
        issue_id="iss-1",
        category=CategoryEnum.SECURITY,
        severity=SeverityEnum.HIGH,
        confidence=1.0,
        line_start=1,
        line_end=2,
        code_snippet="query = ...",
        description="SQL injection",
        why_it_matters="Security risk",
        detection_source=DetectionSourceEnum.STATIC,
    )
    review_res = ReviewResult(
        issues=[issue],
        score=score,
        summary=summary,
        language="python",
        submitted_code="query = 'SELECT * FROM users'",
    )

    res_json = review_res.model_dump_json()
    parsed_json = json.loads(res_json)
    assert parsed_json["language"] == "python"
    assert parsed_json["score"]["overall_score"] == 93.75

    reconstructed = ReviewResult.model_validate_json(res_json)
    assert len(reconstructed.issues) == 1
    assert reconstructed.issues[0].category == CategoryEnum.SECURITY


def test_pipeline_result_defaults():
    """Test 9: PipelineResult default values and PipelineError payload."""
    res = PipelineResult(success=True)
    assert res.success is True
    assert res.review_result is None
    assert res.errors == []
    assert res.warnings == []
    assert res.is_partial_analysis is False
    assert res.execution_time_seconds == 0.0

    err = PipelineError(
        error_type="TimeoutError",
        message="OpenAI API call timed out",
        stage="ai_analysis",
        is_fatal=False,
    )
    res_err = PipelineResult(
        success=False,
        errors=[err],
        warnings=["Fallback to static analysis only"],
        is_partial_analysis=True,
    )
    assert res_err.success is False
    assert len(res_err.errors) == 1
    assert res_err.errors[0].stage == "ai_analysis"
    assert res_err.is_partial_analysis is True
