"""Unit tests for individual deterministic static analyzer modules."""

import pytest
from analyzers import (
    ASTAnalyzer,
    BanditAnalyzer,
    BaseAnalyzer,
    PyflakesAnalyzer,
    RadonAnalyzer,
    StyleAnalyzer,
    get_default_analyzers,
)
from core.interfaces import StaticAnalyzerProtocol
from core.issue_model import CategoryEnum, DetectionSourceEnum, SeverityEnum


def test_default_analyzers_instantiation():
    """Verify that all default static analyzers instantiate and satisfy StaticAnalyzerProtocol."""
    analyzers = get_default_analyzers()
    assert len(analyzers) == 5
    for analyzer in analyzers:
        assert isinstance(analyzer, BaseAnalyzer)
        assert isinstance(analyzer, StaticAnalyzerProtocol)
        assert analyzer.name != ""


def test_ast_analyzer_detects_bare_except():
    """Verify ASTAnalyzer flags bare except clauses."""
    code = (
        "try:\n"
        "    x = 1 / 0\n"
        "except:\n"
        "    pass\n"
    )
    analyzer = ASTAnalyzer()
    issues = analyzer.analyze(code, filename="test_except.py")

    assert len(issues) >= 1
    bare_except_issues = [
        i for i in issues if "bare 'except" in i.description.lower() or "bare-except" in i.issue_id
    ]
    assert len(bare_except_issues) == 1
    issue = bare_except_issues[0]
    assert issue.category == CategoryEnum.ERROR_HANDLING
    assert issue.line_start == 3
    assert issue.detection_source == DetectionSourceEnum.STATIC
    assert issue.detecting_tool == "ast"


def test_ast_analyzer_detects_unclosed_file():
    """Verify ASTAnalyzer flags open() calls not managed inside a with statement."""
    code = (
        "def read_data():\n"
        "    f = open('data.txt', 'r')\n"
        "    content = f.read()\n"
        "    return content\n"
    )
    analyzer = ASTAnalyzer()
    issues = analyzer.analyze(code, filename="test_open.py")

    unclosed_issues = [i for i in issues if "unclosed file" in i.description.lower()]
    assert len(unclosed_issues) == 1
    issue = unclosed_issues[0]
    assert issue.category == CategoryEnum.RESOURCE_MANAGEMENT
    assert issue.severity == SeverityEnum.MEDIUM
    assert issue.line_start == 2


def test_ast_analyzer_detects_excessive_parameters():
    """Verify ASTAnalyzer flags functions with more than 5 parameters."""
    code = "def complex_func(p1, p2, p3, p4, p5, p6):\n    return p1\n"
    analyzer = ASTAnalyzer()
    issues = analyzer.analyze(code, filename="test_params.py")

    param_issues = [i for i in issues if "parameters" in i.description.lower()]
    assert len(param_issues) == 1
    issue = param_issues[0]
    assert issue.category == CategoryEnum.CODE_QUALITY
    assert issue.line_start == 1


def test_ast_analyzer_detects_deep_nesting():
    """Verify ASTAnalyzer flags control flow nested deeper than 4 levels."""
    code = (
        "def deep_nesting():\n"
        "    if True:\n"
        "        for i in range(1):\n"
        "            while True:\n"
        "                try:\n"
        "                    if i == 0:\n"
        "                        pass\n"
        "                except Exception:\n"
        "                    pass\n"
    )
    analyzer = ASTAnalyzer()
    issues = analyzer.analyze(code, filename="test_nesting.py")

    nesting_issues = [i for i in issues if "nesting" in i.description.lower()]
    assert len(nesting_issues) >= 1
    assert nesting_issues[0].category == CategoryEnum.MAINTAINABILITY


def test_pyflakes_analyzer_detects_unused_import_and_undefined():
    """Verify PyflakesAnalyzer flags unused imports and undefined variables."""
    code = (
        "import os\n"
        "import sys\n"
        "def test():\n"
        "    print(undefined_variable)\n"
    )
    analyzer = PyflakesAnalyzer()
    issues = analyzer.analyze(code, filename="test_pyflakes.py")

    descriptions = [i.description.lower() for i in issues]
    assert any("imported but unused" in d for d in descriptions)
    assert any("undefined name" in d for d in descriptions)

    undefined_issues = [i for i in issues if "undefined name" in i.description.lower()]
    assert len(undefined_issues) == 1
    assert undefined_issues[0].category == CategoryEnum.LOGICAL_BUG
    assert undefined_issues[0].severity == SeverityEnum.HIGH


def test_bandit_analyzer_detects_eval():
    """Verify BanditAnalyzer flags unsafe eval() calls."""
    code = (
        "def run_user_code(user_input):\n"
        "    return eval(user_input)\n"
    )
    analyzer = BanditAnalyzer()
    issues = analyzer.analyze(code, filename="test_bandit.py")

    assert len(issues) >= 1
    eval_issues = [i for i in issues if i.category == CategoryEnum.SECURITY]
    assert len(eval_issues) >= 1
    assert eval_issues[0].severity in (SeverityEnum.HIGH, SeverityEnum.CRITICAL)
    assert eval_issues[0].detection_source == DetectionSourceEnum.STATIC
    assert eval_issues[0].detecting_tool == "bandit"


def test_radon_analyzer_detects_high_complexity():
    """Verify RadonAnalyzer flags functions exceeding cyclomatic complexity threshold."""
    # Function with 12 branches (CC > 10)
    branches = "\n".join([f"    if x == {i}:\n        return {i}" for i in range(12)])
    code = f"def highly_complex_function(x):\n{branches}\n    return -1\n"

    analyzer = RadonAnalyzer(complexity_threshold=10)
    issues = analyzer.analyze(code, filename="test_radon.py")

    assert len(issues) == 1
    assert issues[0].category == CategoryEnum.MAINTAINABILITY
    assert "cyclomatic complexity" in issues[0].description.lower()


def test_style_analyzer_detects_long_lines():
    """Verify StyleAnalyzer flags PEP 8 line length violations (> 79 chars)."""
    long_line = "x = '" + "a" * 85 + "'"
    code = f"{long_line}\n"

    analyzer = StyleAnalyzer(max_line_length=79)
    issues = analyzer.analyze(code, filename="test_style.py")

    assert len(issues) >= 1
    assert any("E501" in i.description for i in issues)
    e501_issues = [i for i in issues if "E501" in i.description]
    assert e501_issues[0].category == CategoryEnum.READABILITY
