"""Unit tests for Pyflakes static analyzer wrapper (analyzers/pyflakes_analyzer.py)."""

import pytest
from analyzers.pyflakes_analyzer import PyflakesAnalyzer
from core.interfaces import StaticAnalyzerProtocol
from core.issue_model import CategoryEnum, DetectionSourceEnum, SeverityEnum
from tests.conftest import load_fixture


@pytest.fixture
def analyzer() -> PyflakesAnalyzer:
    return PyflakesAnalyzer()


def test_pyflakes_implements_protocol(analyzer: PyflakesAnalyzer):
    """Verifies PyflakesAnalyzer satisfies StaticAnalyzerProtocol contract."""
    assert isinstance(analyzer, StaticAnalyzerProtocol)
    assert analyzer.name == "pyflakes"


def test_pyflakes_clean_code(analyzer: PyflakesAnalyzer):
    """Verifies clean code produces zero Pyflakes issues."""
    code = load_fixture("clean.py")
    issues = analyzer.analyze(code, filename="clean.py")
    assert len(issues) == 0, f"Expected 0 issues on clean code, got: {issues}"


def test_pyflakes_undefined_name(analyzer: PyflakesAnalyzer):
    """Verifies Pyflakes accurately identifies undefined variables."""
    code = load_fixture("undefined_name.py")
    issues = analyzer.analyze(code, filename="undefined_name.py")

    assert len(issues) >= 2, f"Expected at least 2 undefined name issues, got: {issues}"

    for issue in issues:
        assert issue.category == CategoryEnum.LOGICAL_BUG
        assert issue.severity == SeverityEnum.HIGH
        assert issue.confidence == 1.0
        assert issue.detection_source == DetectionSourceEnum.STATIC
        assert issue.detecting_tool == "pyflakes"
        assert issue.line_start == 6
        assert "undefined name" in issue.description.lower()
        assert "pyflakes.UndefinedName" in (issue.references or [])

    names_flagged = [i.description for i in issues]
    assert any("price" in desc for desc in names_flagged)
    assert any("quantity" in desc for desc in names_flagged)


def test_pyflakes_unused_import(analyzer: PyflakesAnalyzer):
    """Verifies Pyflakes flags unused import statements with line numbers."""
    code = load_fixture("unused_import.py")
    issues = analyzer.analyze(code, filename="unused_import.py")

    assert len(issues) == 2, f"Expected 2 unused import issues, got: {issues}"

    for issue in issues:
        assert issue.category == CategoryEnum.BEST_PRACTICE
        assert issue.severity == SeverityEnum.LOW
        assert issue.confidence == 1.0
        assert issue.detection_source == DetectionSourceEnum.STATIC
        assert issue.detecting_tool == "pyflakes"
        assert issue.line_start in (3, 4)
        assert "imported but unused" in issue.description.lower() or "unused" in issue.description.lower()
        assert "pyflakes.UnusedImport" in (issue.references or [])


def test_pyflakes_unused_variable(analyzer: PyflakesAnalyzer):
    """Verifies Pyflakes detects assigned but unused local variables."""
    code = (
        "def compute_score():\n"
        "    unused_metric = 100\n"
        "    return 42\n"
    )
    issues = analyzer.analyze(code, filename="unused_var.py")

    assert len(issues) == 1
    issue = issues[0]
    assert issue.category == CategoryEnum.CODE_QUALITY
    assert issue.severity == SeverityEnum.LOW
    assert issue.line_start == 2
    assert issue.detecting_tool == "pyflakes"
    assert "unused_metric" in issue.description
    assert "pyflakes.UnusedVariable" in (issue.references or [])


def test_pyflakes_syntax_error_handled_gracefully(analyzer: PyflakesAnalyzer):
    """Verifies Pyflakes does not crash when encountering invalid syntax."""
    code = load_fixture("syntax_error.py")
    issues = analyzer.analyze(code, filename="syntax_error.py")
    assert isinstance(issues, list)
