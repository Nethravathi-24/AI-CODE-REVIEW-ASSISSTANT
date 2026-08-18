"""Comprehensive unit tests for the Python static-analysis layer."""

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
from core.issue_model import (
    CategoryEnum,
    DetectionSourceEnum,
    Issue,
    SeverityEnum,
)
from orchestrator.pipeline import CodeReviewPipeline


class TestBaseAnalyzer:
    """Tests for BaseAnalyzer protocol compliance and utility functions."""

    def test_protocol_conformance(self):
        """Proves all five analyzers conform to StaticAnalyzerProtocol."""
        analyzers = get_default_analyzers()
        assert len(analyzers) == 5
        for analyzer in analyzers:
            assert isinstance(analyzer, BaseAnalyzer)
            assert isinstance(analyzer, StaticAnalyzerProtocol)
            assert isinstance(analyzer.name, str)
            assert len(analyzer.name) > 0

    def test_extract_code_snippet(self):
        """Tests line extraction helper."""
        code = "line1\nline2\nline3\nline4\nline5"
        assert BaseAnalyzer.extract_code_snippet(code, 2, 3) == "line2\nline3"
        assert BaseAnalyzer.extract_code_snippet(code, 1, 1) == "line1"
        assert BaseAnalyzer.extract_code_snippet(code, 5, 5) == "line5"
        assert BaseAnalyzer.extract_code_snippet(code, 10, 12) == "line5"
        assert BaseAnalyzer.extract_code_snippet("", 1, 1) == ""


class TestASTAnalyzer:
    """Tests for ASTAnalyzer."""

    def test_valid_clean_python(self):
        """Valid clean python code yields 0 issues."""
        code = '''
def add(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b
'''
        analyzer = ASTAnalyzer()
        issues = analyzer.analyze(code)
        assert len(issues) == 0

    def test_bare_except_detection(self):
        """Bare except clause is detected with category, severity, and line."""
        code = '''
try:
    x = 1 / 0
except:
    print("error")
'''
        analyzer = ASTAnalyzer()
        issues = analyzer.analyze(code)
        assert len(issues) == 1
        issue = issues[0]
        assert isinstance(issue, Issue)
        assert issue.category == CategoryEnum.ERROR_HANDLING
        assert issue.severity == SeverityEnum.MEDIUM
        assert issue.line_start == 4
        assert issue.detection_source == DetectionSourceEnum.STATIC
        assert issue.detecting_tool == "ast_analyzer"
        assert "Bare 'except:'" in issue.description

    def test_empty_except_pass_detection(self):
        """Empty except pass is detected with correct category."""
        code = '''
try:
    x = 1 / 0
except ValueError:
    pass
'''
        analyzer = ASTAnalyzer()
        issues = analyzer.analyze(code)
        assert any(
            i.category == CategoryEnum.ERROR_HANDLING
            and "Empty except block" in i.description
            for i in issues
        )

    def test_unclosed_file_detection(self):
        """open() call outside with statement is flagged."""
        code = '''
def read_data(filepath):
    f = open(filepath, "r")
    data = f.read()
    f.close()
    return data
'''
        analyzer = ASTAnalyzer()
        issues = analyzer.analyze(code)
        file_issues = [
            i for i in issues if i.category == CategoryEnum.RESOURCE_MANAGEMENT
        ]
        assert len(file_issues) == 1
        assert file_issues[0].line_start == 3
        assert file_issues[0].severity == SeverityEnum.MEDIUM

    def test_safe_with_open_not_flagged(self):
        """open() inside with context is not flagged."""
        code = '''
def read_data(filepath):
    with open(filepath, "r") as f:
        return f.read()
'''
        analyzer = ASTAnalyzer()
        issues = analyzer.analyze(code)
        safe_issues = [
            i for i in issues if i.category == CategoryEnum.RESOURCE_MANAGEMENT
        ]
        assert len(safe_issues) == 0

    def test_deep_nesting_detection(self):
        """Nesting depth > 4 is detected."""
        code = '''
def nested(a, b, c, d, e):
    if a:
        for i in range(10):
            while b:
                try:
                    if c:
                        print("deep")
                except Exception:
                    pass
'''
        analyzer = ASTAnalyzer()
        issues = analyzer.analyze(code)
        nesting_issues = [
            i for i in issues if "Deeply nested" in i.description
        ]
        assert len(nesting_issues) >= 1
        assert nesting_issues[0].category == CategoryEnum.MAINTAINABILITY

    def test_excessive_parameters_detection(self):
        """Function with > 5 parameters is flagged."""
        code = '''
def too_many_params(a, b, c, d, e, f, g):
    return a + b + c + d + e + f + g
'''
        analyzer = ASTAnalyzer()
        issues = analyzer.analyze(code)
        param_issues = [
            i for i in issues if "too many parameters" in i.description
        ]
        assert len(param_issues) == 1
        assert param_issues[0].line_start == 2
        assert param_issues[0].category == CategoryEnum.MAINTAINABILITY

    def test_wildcard_import_detection(self):
        """Wildcard import is flagged."""
        code = "from math import *\n"
        analyzer = ASTAnalyzer()
        issues = analyzer.analyze(code)
        star_issues = [
            i for i in issues if "Wildcard import" in i.description
        ]
        assert len(star_issues) == 1
        assert star_issues[0].category == CategoryEnum.BEST_PRACTICE
        assert star_issues[0].severity == SeverityEnum.INFORMATIONAL

    def test_syntax_error_handling(self):
        """Syntax error is returned as Critical syntax_error issue."""
        code = "def broken_syntax(:\n    pass"
        analyzer = ASTAnalyzer()
        issues = analyzer.analyze(code)
        assert len(issues) == 1
        assert issues[0].category == CategoryEnum.SYNTAX_ERROR
        assert issues[0].severity == SeverityEnum.CRITICAL
        assert issues[0].line_start == 1


class TestPyflakesAnalyzer:
    """Tests for PyflakesAnalyzer."""

    def test_unused_import_detection(self):
        """Unused import is detected with correct line number."""
        code = "import sys\nimport os\n\nprint(sys.version)\n"
        analyzer = PyflakesAnalyzer()
        issues = analyzer.analyze(code)
        unused_issues = [
            i for i in issues if "imported but unused" in i.description
        ]
        assert len(unused_issues) == 1
        assert unused_issues[0].line_start == 2
        assert unused_issues[0].category == CategoryEnum.CODE_QUALITY
        assert unused_issues[0].detecting_tool == "pyflakes"

    def test_unused_variable_detection(self):
        """Unused local variable is detected."""
        code = "def compute():\n    unused_val = 42\n    return 10\n"
        analyzer = PyflakesAnalyzer()
        issues = analyzer.analyze(code)
        var_issues = [
            i for i in issues if "assigned to but never used" in i.description
        ]
        assert len(var_issues) == 1
        assert var_issues[0].line_start == 2
        assert var_issues[0].category == CategoryEnum.CODE_QUALITY

    def test_undefined_name_detection(self):
        """Undefined variable access is detected as a runtime problem."""
        code = "def broken():\n    return undefined_symbol + 1\n"
        analyzer = PyflakesAnalyzer()
        issues = analyzer.analyze(code)
        undef_issues = [
            i for i in issues if "undefined name" in i.description
        ]
        assert len(undef_issues) == 1
        assert undef_issues[0].line_start == 2
        assert undef_issues[0].category == CategoryEnum.RUNTIME_PROBLEM
        assert undef_issues[0].severity == SeverityEnum.HIGH


class TestBanditAnalyzer:
    """Tests for BanditAnalyzer."""

    def test_eval_security_issue(self):
        """Use of eval is flagged as a security issue."""
        code = 'user_data = "1 + 1"\nresult = eval(user_data)\n'
        analyzer = BanditAnalyzer()
        issues = analyzer.analyze(code)
        assert len(issues) >= 1
        eval_issue = issues[0]
        assert eval_issue.category == CategoryEnum.SECURITY
        assert eval_issue.line_start == 2
        assert eval_issue.detecting_tool == "bandit"
        assert eval_issue.confidence >= 0.7
        assert eval_issue.severity in (
            SeverityEnum.CRITICAL,
            SeverityEnum.HIGH,
            SeverityEnum.MEDIUM,
        )
        assert any(
            "B307" in ref for ref in (eval_issue.references or [])
        )

    def test_clean_code_no_bandit_issues(self):
        """Safe code produces 0 Bandit findings."""
        code = "def safe_math(a: int, b: int) -> int:\n    return a * b\n"
        analyzer = BanditAnalyzer()
        issues = analyzer.analyze(code)
        assert len(issues) == 0


class TestRadonAnalyzer:
    """Tests for RadonAnalyzer."""

    def test_high_complexity_function(self):
        """Function with Cyclomatic Complexity > 10 is flagged."""
        code = '''
def complex_routing(a, b, c, d, e, f, g, h, i, j, k):
    if a:
        return 1
    elif b:
        return 2
    elif c:
        return 3
    elif d:
        return 4
    elif e:
        return 5
    elif f:
        return 6
    elif g:
        return 7
    elif h:
        return 8
    elif i:
        return 9
    elif j:
        return 10
    elif k:
        return 11
    return 0
'''
        analyzer = RadonAnalyzer()
        issues = analyzer.analyze(code)
        cc_issues = [
            i for i in issues
            if "cyclomatic complexity" in i.description.lower()
        ]
        assert len(cc_issues) == 1
        assert cc_issues[0].line_start == 2
        assert cc_issues[0].category == CategoryEnum.MAINTAINABILITY
        assert cc_issues[0].detecting_tool == "radon"

    def test_simple_code_low_complexity(self):
        """Simple code produces no complexity warnings."""
        code = "def simple():\n    return 42\n"
        analyzer = RadonAnalyzer()
        issues = analyzer.analyze(code)
        assert len(issues) == 0


class TestStyleAnalyzer:
    """Tests for StyleAnalyzer."""

    def test_trailing_whitespace_and_long_line(self):
        """Pycodestyle flags trailing whitespace and line length."""
        long_line = "x = 1 " + " # " + ("a" * 80) + "\n"
        analyzer = StyleAnalyzer()
        issues = analyzer.analyze(long_line)
        assert len(issues) >= 1
        assert all(
            i.category in (
                CategoryEnum.READABILITY, CategoryEnum.BEST_PRACTICE
            )
            for i in issues
        )
        assert all(i.detecting_tool == "pycodestyle" for i in issues)
        assert all(i.line_start == 1 for i in issues)

    def test_clean_style_code(self):
        """Clean PEP 8 compliant code produces 0 style issues."""
        code = "def clean_fn(x: int) -> int:\n    return x + 1\n"
        analyzer = StyleAnalyzer()
        issues = analyzer.analyze(code)
        assert len(issues) == 0


class TestPipelineFailureIsolationAndSecurity:
    """Tests for analyzer failure isolation and security."""

    def test_pipeline_isolates_failing_analyzer(self):
        """A crashing analyzer does not crash pipeline."""
        class CrashingAnalyzer(BaseAnalyzer):
            @property
            def name(self) -> str:
                return "crash_analyzer"

            def analyze(
                self, code: str, filename: str = "snippet"
            ) -> list:
                raise RuntimeError("Catastrophic analyzer failure!")

        working_analyzer = ASTAnalyzer()
        pipeline = CodeReviewPipeline(
            analyzers=[CrashingAnalyzer(), working_analyzer]
        )

        code = "try:\n    x = 1\nexcept:\n    pass\n"
        result = pipeline.review_code(code)

        assert result is not None
        assert len(result.issues) >= 1
        assert any(i.detecting_tool == "ast_analyzer" for i in result.issues)

    def test_default_pipeline_runs_all_analyzers(self):
        """Default pipeline runs all 5 static analyzers."""
        pipeline = CodeReviewPipeline()
        assert len(pipeline.analyzers) == 5

        code = (
            "import os\n"
            "import sys\n\n"
            "try:\n"
            "    eval('1+1')\n"
            "except:\n"
            "    print(sys.version)\n"
        )
        result = pipeline.review_code(code)

        tools_detected = {issue.detecting_tool for issue in result.issues}
        assert "ast_analyzer" in tools_detected
        assert "pyflakes" in tools_detected
        assert "bandit" in tools_detected

    def test_security_never_executes_user_code(self):
        """Verifies that static analysis never executes submitted code."""
        malicious_code = '''
def payload():
    raise AssertionError("USER CODE WAS EXECUTED!")

payload()
'''
        pipeline = CodeReviewPipeline()
        result = pipeline.review_code(malicious_code)
        assert result is not None
