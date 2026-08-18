"""Unit tests for AST structural analyzer (analyzers/ast_analyzer.py)."""

import pytest
from analyzers.ast_analyzer import ASTAnalyzer
from core.interfaces import StaticAnalyzerProtocol
from core.issue_model import CategoryEnum, DetectionSourceEnum, SeverityEnum
from tests.conftest import load_fixture


@pytest.fixture
def analyzer() -> ASTAnalyzer:
    return ASTAnalyzer()


def test_ast_analyzer_implements_protocol(analyzer: ASTAnalyzer):
    """Verifies ASTAnalyzer satisfies StaticAnalyzerProtocol contract."""
    assert isinstance(analyzer, StaticAnalyzerProtocol)
    assert analyzer.name == "ast"


def test_ast_analyzer_clean_code(analyzer: ASTAnalyzer):
    """Verifies clean fixture produces zero AST findings."""
    code = load_fixture("clean.py")
    issues = analyzer.analyze(code, filename="clean.py")
    assert len(issues) == 0, f"Expected 0 issues on clean code, got: {issues}"


def test_ast_analyzer_syntax_error(analyzer: ASTAnalyzer):
    """Verifies AST analyzer captures syntax errors with CRITICAL severity."""
    code = load_fixture("syntax_error.py")
    issues = analyzer.analyze(code, filename="syntax_error.py")

    assert len(issues) == 1
    issue = issues[0]
    assert issue.category == CategoryEnum.SYNTAX_ERROR
    assert issue.severity == SeverityEnum.CRITICAL
    assert issue.confidence == 1.0
    assert issue.line_start == 2
    assert issue.line_end == 2
    assert issue.detection_source == DetectionSourceEnum.STATIC
    assert issue.detecting_tool == "ast"
    assert "syntax error" in issue.description.lower()
    assert issue.file == "syntax_error.py"


def test_ast_analyzer_resource_management(analyzer: ASTAnalyzer):
    """Verifies AST analyzer detects unclosed open() call without with context manager."""
    code = load_fixture("resource_management.py")
    issues = analyzer.analyze(code, filename="resource_management.py")

    assert len(issues) >= 1
    open_issue = next(
        (i for i in issues if i.category == CategoryEnum.RESOURCE_MANAGEMENT), None
    )
    assert open_issue is not None, "Expected RESOURCE_MANAGEMENT issue for unclosed open()"
    assert open_issue.severity == SeverityEnum.MEDIUM
    assert open_issue.confidence == 1.0
    assert open_issue.line_start == 6
    assert open_issue.detection_source == DetectionSourceEnum.STATIC
    assert open_issue.detecting_tool == "ast"
    assert "unclosed" in open_issue.description.lower() or "open()" in open_issue.description


def test_ast_analyzer_bare_except(analyzer: ASTAnalyzer):
    """Verifies AST analyzer detects bare except: handler."""
    code = (
        "def risky_operation():\n"
        "    try:\n"
        "        do_something()\n"
        "    except:\n"
        "        pass\n"
    )
    issues = analyzer.analyze(code, filename="bare_except.py")

    assert len(issues) >= 1
    except_issue = next(
        (i for i in issues if i.category == CategoryEnum.ERROR_HANDLING), None
    )
    assert except_issue is not None
    assert except_issue.severity == SeverityEnum.MEDIUM
    assert except_issue.line_start == 4
    assert except_issue.detection_source == DetectionSourceEnum.STATIC
    assert except_issue.detecting_tool == "ast"
    assert "bare" in except_issue.description.lower() or "except" in except_issue.description.lower()


def test_ast_analyzer_excessive_parameters(analyzer: ASTAnalyzer):
    """Verifies AST analyzer detects functions with more than 5 parameters."""
    code = (
        "def configure_system(host, port, user, password, timeout, retries, use_ssl):\n"
        "    return True\n"
    )
    issues = analyzer.analyze(code, filename="params.py")

    assert len(issues) == 1
    param_issue = issues[0]
    assert param_issue.category == CategoryEnum.CODE_QUALITY
    assert param_issue.severity == SeverityEnum.LOW
    assert param_issue.line_start == 1
    assert param_issue.detecting_tool == "ast"
    assert "7 parameters" in param_issue.description


def test_ast_analyzer_deep_nesting(analyzer: ASTAnalyzer):
    """Verifies AST analyzer flags control flow nesting deeper than 4 levels."""
    code = (
        "def deep_process(data):\n"
        "    if data:\n"
        "        for item in data:\n"
        "            while item > 0:\n"
        "                try:\n"
        "                    if item == 1:\n"
        "                        print(item)\n"
        "                except Exception:\n"
        "                    pass\n"
    )
    issues = analyzer.analyze(code, filename="nesting.py")

    assert len(issues) >= 1
    nesting_issue = next(
        (i for i in issues if i.category == CategoryEnum.MAINTAINABILITY), None
    )
    assert nesting_issue is not None
    assert nesting_issue.severity == SeverityEnum.LOW
    assert nesting_issue.detecting_tool == "ast"
    assert "nesting" in nesting_issue.description.lower()
