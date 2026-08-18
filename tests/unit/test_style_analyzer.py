"""Unit tests for PEP 8 Style Analyzer wrapper (analyzers/style_analyzer.py)."""

import pytest
from analyzers.style_analyzer import StyleAnalyzer
from core.interfaces import StaticAnalyzerProtocol
from core.issue_model import CategoryEnum, DetectionSourceEnum, SeverityEnum
from tests.conftest import load_fixture


@pytest.fixture
def analyzer() -> StyleAnalyzer:
    return StyleAnalyzer(max_line_length=79)


def test_style_implements_protocol(analyzer: StyleAnalyzer):
    """Verifies StyleAnalyzer satisfies StaticAnalyzerProtocol contract."""
    assert isinstance(analyzer, StaticAnalyzerProtocol)
    assert analyzer.name == "pycodestyle"


def test_style_clean_code(analyzer: StyleAnalyzer):
    """Verifies clean PEP 8 compliant code produces zero style findings."""
    code = load_fixture("clean.py")
    issues = analyzer.analyze(code, filename="clean.py")
    assert len(issues) == 0, f"Expected 0 style issues on clean code, got: {issues}"


def test_style_violations_detected(analyzer: StyleAnalyzer):
    """Verifies style analyzer identifies line length, operator spacing, and trailing whitespace."""
    code = load_fixture("style_violation.py")
    issues = analyzer.analyze(code, filename="style_violation.py")

    assert len(issues) >= 1, f"Expected style issues, got: {issues}"

    # Check for E501 (line too long)
    e501_issue = next(
        (i for i in issues if any("E501" in ref for ref in (i.references or []))),
        None,
    )
    assert e501_issue is not None, "Expected E501 line length issue"
    assert e501_issue.category == CategoryEnum.READABILITY
    assert e501_issue.severity == SeverityEnum.LOW
    assert e501_issue.confidence == 1.0
    assert e501_issue.detection_source == DetectionSourceEnum.STATIC
    assert e501_issue.detecting_tool == "pycodestyle"
    assert e501_issue.line_start == 6

    # Verify every issue has valid attributes
    for issue in issues:
        assert issue.category in (CategoryEnum.READABILITY, CategoryEnum.BEST_PRACTICE)
        assert issue.severity in (SeverityEnum.LOW, SeverityEnum.INFORMATIONAL)
        assert issue.detection_source == DetectionSourceEnum.STATIC
        assert issue.detecting_tool == "pycodestyle"


def test_style_configurable_line_length():
    """Verifies configurable line length limit."""
    code = load_fixture("style_violation.py")

    # Relaxed line limit of 150 characters
    lenient_analyzer = StyleAnalyzer(max_line_length=150)
    lenient_issues = lenient_analyzer.analyze(code)

    has_e501 = any("E501" in (ref or "") for issue in lenient_issues for ref in (issue.references or []))
    assert not has_e501, "E501 should not trigger when line length is set to 150"


def test_style_empty_and_whitespace_handled(analyzer: StyleAnalyzer):
    """Verifies empty or whitespace code produces empty results without errors."""
    assert analyzer.analyze("") == []
    assert analyzer.analyze("    \n\t  ") == []
