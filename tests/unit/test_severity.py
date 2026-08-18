"""Unit tests for core/severity.py deterministic severity rules."""

from core.issue_model import CategoryEnum, SeverityEnum
from core.severity import calculate_base_severity, calculate_severity


def test_base_severity_mapping():
    """Test 10: Category base severity mapping rules."""
    assert calculate_base_severity(CategoryEnum.SYNTAX_ERROR) == SeverityEnum.CRITICAL
    assert calculate_base_severity(CategoryEnum.SECURITY) == SeverityEnum.HIGH
    assert calculate_base_severity(CategoryEnum.LOGICAL_BUG) == SeverityEnum.HIGH
    assert calculate_base_severity(CategoryEnum.RUNTIME_PROBLEM) == SeverityEnum.HIGH
    assert calculate_base_severity(CategoryEnum.EDGE_CASE) == SeverityEnum.MEDIUM
    assert calculate_base_severity(CategoryEnum.ERROR_HANDLING) == SeverityEnum.MEDIUM
    assert calculate_base_severity(CategoryEnum.RESOURCE_MANAGEMENT) == SeverityEnum.MEDIUM
    assert calculate_base_severity(CategoryEnum.PERFORMANCE) == SeverityEnum.MEDIUM
    assert calculate_base_severity(CategoryEnum.CODE_QUALITY) == SeverityEnum.LOW
    assert calculate_base_severity(CategoryEnum.MAINTAINABILITY) == SeverityEnum.LOW
    assert calculate_base_severity(CategoryEnum.DUPLICATE_LOGIC) == SeverityEnum.LOW
    assert calculate_base_severity(CategoryEnum.READABILITY) == SeverityEnum.LOW
    assert calculate_base_severity(CategoryEnum.BEST_PRACTICE) == SeverityEnum.INFORMATIONAL


def test_severity_confidence_capping():
    """Test 11: Low confidence AI-only findings are capped at Medium severity."""
    # High base severity + low confidence (<0.6) -> capped at Medium
    assert (
        calculate_severity(CategoryEnum.SECURITY, confidence=0.4, is_corroborated=False)
        == SeverityEnum.MEDIUM
    )

    # High base severity + high confidence (>=0.6) -> High
    assert (
        calculate_severity(CategoryEnum.SECURITY, confidence=0.8, is_corroborated=False)
        == SeverityEnum.HIGH
    )


def test_syntax_error_always_critical():
    """Test 12: Syntax errors are always Critical regardless of confidence."""
    assert (
        calculate_severity(CategoryEnum.SYNTAX_ERROR, confidence=0.1, is_corroborated=False)
        == SeverityEnum.CRITICAL
    )
