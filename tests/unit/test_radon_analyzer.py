"""Unit tests for Radon complexity analyzer wrapper (analyzers/radon_analyzer.py)."""

import pytest
from analyzers.radon_analyzer import RadonAnalyzer
from core.interfaces import StaticAnalyzerProtocol
from core.issue_model import CategoryEnum, DetectionSourceEnum, SeverityEnum
from tests.conftest import load_fixture


@pytest.fixture
def analyzer() -> RadonAnalyzer:
    return RadonAnalyzer(complexity_threshold=10)


def test_radon_implements_protocol(analyzer: RadonAnalyzer):
    """Verifies RadonAnalyzer satisfies StaticAnalyzerProtocol contract."""
    assert isinstance(analyzer, StaticAnalyzerProtocol)
    assert analyzer.name == "radon"


def test_radon_clean_code(analyzer: RadonAnalyzer):
    """Verifies clean low-complexity code produces zero Radon issues."""
    code = load_fixture("clean.py")
    issues = analyzer.analyze(code, filename="clean.py")
    assert len(issues) == 0, f"Expected 0 complexity issues, got: {issues}"


def test_radon_high_complexity(analyzer: RadonAnalyzer):
    """Verifies Radon flags functions with cyclomatic complexity exceeding threshold."""
    code = load_fixture("high_complexity.py")
    issues = analyzer.analyze(code, filename="high_complexity.py")

    assert len(issues) == 1, f"Expected 1 high complexity issue, got: {issues}"
    issue = issues[0]

    assert issue.category == CategoryEnum.MAINTAINABILITY
    assert issue.severity in (SeverityEnum.MEDIUM, SeverityEnum.HIGH)
    assert issue.confidence == 1.0
    assert issue.detection_source == DetectionSourceEnum.STATIC
    assert issue.detecting_tool == "radon"
    assert issue.line_start == 4
    assert "complex_decision_engine" in issue.description
    assert any("CC=" in ref for ref in (issue.references or []))


def test_radon_configurable_threshold():
    """Verifies configurable complexity threshold behaves dynamically."""
    code = load_fixture("high_complexity.py")

    # Lower threshold of 2 triggers issue
    strict_analyzer = RadonAnalyzer(complexity_threshold=2)
    assert len(strict_analyzer.analyze(code)) >= 1

    # Higher threshold of 50 produces 0 issues
    lenient_analyzer = RadonAnalyzer(complexity_threshold=50)
    assert len(lenient_analyzer.analyze(code)) == 0


def test_radon_syntax_error_handled_gracefully(analyzer: RadonAnalyzer):
    """Verifies Radon handles syntax errors cleanly without throwing exceptions."""
    code = load_fixture("syntax_error.py")
    issues = analyzer.analyze(code, filename="syntax_error.py")
    assert isinstance(issues, list)
