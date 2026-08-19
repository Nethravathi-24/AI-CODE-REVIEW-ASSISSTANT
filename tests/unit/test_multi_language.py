"""Comprehensive multi-language unit and integration test suite targeting real AST parsers."""

import pytest
from analyzers import get_analyzers_for_language
from analyzers.java_analyzer import JavaAnalyzer
from analyzers.js_analyzer import JSAnalyzer
from analyzers.ts_analyzer import TSAnalyzer
from core.issue_model import CategoryEnum, Issue, SeverityEnum
from input_handling import detect_language, validate_input
from orchestrator import CodeReviewPipeline, run_pipeline
from remediation import FixGenerator, TestGenerator
from remediation.validator import validate_code_syntax
from report import MarkdownReportExporter


def test_language_detection():
    """Test 1: Correct language detection for Python, JS, TS, Java."""
    assert detect_language("def foo(): pass", filename="script.py").language == "python"
    assert detect_language("const total = price + tax;", filename="app.js").language == "javascript"
    assert detect_language("function process(x: any): string {}", filename="service.ts").language == "typescript"
    assert detect_language("public class Main { public static void main(String[] args) {} }", filename="Main.java").language == "java"


def test_analyzer_routing():
    """Test 2: Correct analyzer routing by language."""
    py_tools = get_analyzers_for_language("python")
    assert len(py_tools) == 5

    js_tools = get_analyzers_for_language("javascript")
    assert len(js_tools) == 1 and isinstance(js_tools[0], JSAnalyzer)

    ts_tools = get_analyzers_for_language("typescript")
    assert len(ts_tools) == 1 and isinstance(ts_tools[0], TSAnalyzer)

    java_tools = get_analyzers_for_language("java")
    assert len(java_tools) == 1 and isinstance(java_tools[0], JavaAnalyzer)

    assert len(get_analyzers_for_language("unsupported_lang")) == 0


def test_real_js_esprima_parser():
    """Test 3 & 4 & 5: Real Esprima AST parser invocation and JS findings."""
    analyzer = JSAnalyzer()
    assert analyzer.is_available() is True
    meta = analyzer.get_metadata()
    assert meta["tool_name"] == "esprima"
    assert meta["type"] == "ast_walker"

    # Test valid JS AST findings
    js_code = "var total = 10;\nif (total == 10) {\n  console.log('msg');\n  eval('x = 1');\n}\n"
    issues = analyzer.analyze(js_code, filename="app.js")
    assert len(issues) >= 3
    cats = {i.category for i in issues}
    assert CategoryEnum.SECURITY in cats
    assert CategoryEnum.BEST_PRACTICE in cats
    assert CategoryEnum.READABILITY in cats

    # Test JS syntax error parsing
    bad_js = "function test() { var x = ; }"
    err_issues = analyzer.analyze(bad_js, filename="bad.js")
    assert len(err_issues) == 1
    assert err_issues[0].category == CategoryEnum.SYNTAX_ERROR
    assert err_issues[0].line_start == 1


def test_real_ts_tree_sitter_parser():
    """Test 3 & 4 & 5: Real Tree-Sitter AST parser invocation and TS findings."""
    analyzer = TSAnalyzer()
    assert analyzer.is_available() is True
    meta = analyzer.get_metadata()
    assert meta["tool_name"] == "tree_sitter_typescript"

    # Test valid TS AST findings
    ts_code = "function calc(x: any): any {\n  var a: any = x;\n  if (a == 10) {\n    eval('x = 1');\n  }\n  return a;\n}"
    issues = analyzer.analyze(ts_code, filename="service.ts")
    assert len(issues) >= 3
    cats = {i.category for i in issues}
    assert CategoryEnum.CODE_QUALITY in cats  # any type
    assert CategoryEnum.SECURITY in cats      # eval


def test_real_java_javalang_parser():
    """Test 3 & 4 & 5: Real Javalang AST parser invocation and Java findings."""
    analyzer = JavaAnalyzer()
    assert analyzer.is_available() is True
    meta = analyzer.get_metadata()
    assert meta["tool_name"] == "javalang"

    # Test valid Java AST findings
    java_code = (
        "public class Demo {\n"
        "    public void run(String cmd, String s1) {\n"
        "        System.out.println(cmd);\n"
        "        if (s1 == \"test\") {}\n"
        "        try {\n"
        "            Runtime.getRuntime().exec(cmd);\n"
        "        } catch (Exception e) {}\n"
        "    }\n"
        "}\n"
    )
    issues = analyzer.analyze(java_code, filename="Demo.java")
    assert len(issues) >= 3
    cats = {i.category for i in issues}
    assert CategoryEnum.SECURITY in cats       # exec
    assert CategoryEnum.LOGICAL_BUG in cats     # string ==
    assert CategoryEnum.ERROR_HANDLING in cats  # empty catch


def test_python_analyzers_never_run_for_non_python():
    """Test 6: Python linters are NEVER executed for JS, TS, or Java code."""
    js_code = "const x = 10; function foo() { return x; }"
    pipeline = CodeReviewPipeline()
    res = pipeline.run(js_code, filename="test.js")

    assert res.success is True
    assert res.review_result.language == "javascript"
    # Ensure no Python AST or Bandit errors were raised
    for err in res.errors:
        assert err.stage != "static_analysis"


def test_remediation_language_specific():
    """Test 9 & 10: Fix and Test Generators produce language-specific output."""
    issue = Issue(
        issue_id="test-1",
        category=CategoryEnum.SECURITY,
        severity=SeverityEnum.HIGH,
        confidence=0.9,
        line_start=2,
        line_end=2,
        code_snippet="eval(x)",
        description="Dangerous eval execution",
        why_it_matters="Security flaw",
        detection_source="static",
    )

    fix_gen = FixGenerator()
    test_gen = TestGenerator()

    # Python -> pytest
    py_fix = fix_gen.generate_fix(issue, "eval(x)", language="python")
    py_test = test_gen.generate_test(issue, "eval(x)", language="python")
    assert "ast.literal_eval" in py_fix.suggested_fix
    assert "def test_regression_" in py_test.test_code

    # JavaScript -> Jest
    js_fix = fix_gen.generate_fix(issue, "eval(x)", language="javascript")
    js_test = test_gen.generate_test(issue, "eval(x)", language="javascript")
    assert "JSON.parse" in js_fix.suggested_fix
    assert "describe('Regression Test Suite'" in js_test.test_code

    # Java -> JUnit 5
    java_test = test_gen.generate_test(issue, "Runtime.getRuntime().exec(x)", language="java")
    assert "import org.junit.jupiter.api.Test;" in java_test.test_code


def test_real_ast_syntax_validation():
    """Test 15: Real AST syntax validation for all languages."""
    # Valid Python
    valid_py, status_py, msg_py = validate_code_syntax("def foo(): pass", "python")
    assert valid_py is True
    assert "FULL validation" in msg_py

    # Valid JS via Esprima
    valid_js, status_js, msg_js = validate_code_syntax("const x = 10;", "javascript")
    assert valid_js is True
    assert "Esprima JavaScript AST" in msg_js

    # Valid TS via Tree-Sitter
    valid_ts, status_ts, msg_ts = validate_code_syntax("const x: number = 10;", "typescript")
    assert valid_ts is True
    assert "Tree-Sitter TypeScript AST" in msg_ts

    # Valid Java via Javalang
    valid_java, status_java, msg_java = validate_code_syntax("public class A {}", "java")
    assert valid_java is True
    assert "Javalang Java AST" in msg_java


def test_report_contains_language_metadata():
    """Test 11: Reports include language and parser metadata."""
    res = run_pipeline("const x = 10;\neval('x = 20');\n", filename="app.js")
    exporter = MarkdownReportExporter()
    report = exporter.export(res.review_result)

    assert "**Language:** `JAVASCRIPT`" in report
    assert "Esprima ECMAScript AST" in report
    assert "JSAnalyzer" in report


def test_removal_of_txt_extension():
    """Test 19: .txt file extension is rejected."""
    txt_res = validate_input("plain text", filename="notes.txt")
    assert txt_res.is_valid is False
    txt_txt_error = txt_res.error_message
    assert "Invalid file extension" in txt_txt_error
