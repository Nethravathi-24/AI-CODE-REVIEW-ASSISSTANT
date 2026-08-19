"""Unit and integration tests for complete source code auto-correction, multi-fix remediation, AST validation, and diff generation."""

import pytest
from core.issue_model import ValidationStatusEnum
from orchestrator import run_pipeline
from remediation.fix_generator import FixGenerator


def test_python_security_multi_fix_correction():
    """Test 1: Proves complete auto-correction applies multiple fixes to Python code safely."""
    dirty_python = (
        "import os\n"
        "import sys\n\n"
        "def calculate():\n"
        "    unused_variable = 10\n"
        '    result = eval(input("Enter calculation: "))\n'
        "    try:\n"
        "        print(result)\n"
        "    except:\n"
        "        pass\n\n"
        'password = "admin123"\n'
    )

    pipeline_res = run_pipeline(dirty_python, filename="security_test.py")
    assert pipeline_res.success is True
    review_res = pipeline_res.review_result
    assert review_res is not None

    corr = review_res.corrected_code_obj
    assert corr is not None
    assert corr.is_changed is True
    assert corr.validation_status in (ValidationStatusEnum.PASSED, ValidationStatusEnum.NOT_VALIDATED)

    corrected_text = corr.corrected_code
    # 1. Bare except fixed
    assert "except Exception:" in corrected_text
    # 2. eval fixed to ast.literal_eval
    assert "ast.literal_eval" in corrected_text
    # 3. import ast added
    assert "import ast" in corrected_text
    # 4. Hardcoded password fixed
    assert "os.getenv(" in corrected_text
    # 5. Diff is non-empty and valid
    assert "---" in corr.diff and "+++" in corr.diff


def test_clean_python_code_preservation():
    """Test 2: Proves clean Python code receives zero unnecessary modifications."""
    clean_python = "def add(a: int, b: int) -> int:\n    return a + b\n"
    pipeline_res = run_pipeline(clean_python, filename="clean_test.py")
    assert pipeline_res.success is True

    corr = pipeline_res.review_result.corrected_code_obj
    assert corr is not None
    assert corr.is_changed is False
    assert corr.corrected_code.strip() == clean_python.strip()


def test_javascript_code_correction():
    """Test 3: Proves JavaScript code auto-correction fixes var, loose equality, and eval."""
    dirty_js = (
        "var x = 1;\n"
        "function test(value) {\n"
        "    if (value == null) {\n"
        '        eval("console.log(value)");\n'
        "    }\n"
        "}\n"
    )

    pipeline_res = run_pipeline(dirty_js, filename="test.js")
    assert pipeline_res.success is True

    corr = pipeline_res.review_result.corrected_code_obj
    assert corr is not None
    assert corr.is_changed is True
    assert "const x = 1;" in corr.corrected_code
    assert "===" in corr.corrected_code
    assert "JSON.parse(" in corr.corrected_code
    assert corr.validation_status == ValidationStatusEnum.PASSED


def test_typescript_code_correction():
    """Test 4: Proves TypeScript code auto-correction fixes var and eval."""
    dirty_ts = (
        "function process(data: any): any {\n"
        "    var result: any = data;\n"
        '    eval("console.log(result)");\n'
        "    return result;\n"
        "}\n"
    )

    pipeline_res = run_pipeline(dirty_ts, filename="test.ts")
    assert pipeline_res.success is True

    corr = pipeline_res.review_result.corrected_code_obj
    assert corr is not None
    assert corr.is_changed is True
    assert "const result: any = data;" in corr.corrected_code
    assert "JSON.parse(" in corr.corrected_code
    assert corr.validation_status == ValidationStatusEnum.PASSED


def test_java_code_correction():
    """Test 5: Proves Java code auto-correction fixes System.out.println and empty catch."""
    dirty_java = (
        "public class Demo {\n"
        "    public void run(String input) {\n"
        "        try {\n"
        "            System.out.println(input);\n"
        "        } catch (Exception e) {\n"
        "        }\n"
        "    }\n"
        "}\n"
    )

    pipeline_res = run_pipeline(dirty_java, filename="Demo.java")
    assert pipeline_res.success is True

    corr = pipeline_res.review_result.corrected_code_obj
    assert corr is not None
    assert corr.is_changed is True
    assert "logger.info(input)" in corr.corrected_code
    assert "logger.error" in corr.corrected_code
    assert corr.validation_status == ValidationStatusEnum.PASSED


def test_syntax_error_handling_and_rejection():
    """Test 6: Proves syntax error in submitted code reports CRITICAL issue without crashing."""
    broken_code = "def broken_function(\n    print('hello')\n"
    pipeline_res = run_pipeline(broken_code, filename="broken.py")

    assert pipeline_res.success is True
    review_res = pipeline_res.review_result
    assert review_res.summary.critical_count >= 1
    assert any(i.category.value == "syntax_error" for i in review_res.issues)
