"""Unit tests for remediation fix generation, test generation, and AST syntax validation."""

import pytest
from core.issue_model import CategoryEnum, DetectionSourceEnum, Issue, SeverityEnum, ValidationStatusEnum
from remediation import FixGenerator, TestGenerator, validate_python_syntax


def test_validate_python_syntax_valid():
    """Test 1: Valid Python snippet passes syntax check."""
    is_valid, status, msg = validate_python_syntax("x = 1 + 2\nprint(x)\n")
    assert is_valid is True
    assert status == ValidationStatusEnum.PASSED


def test_validate_python_syntax_invalid():
    """Test 2: Invalid Python syntax fails syntax check gracefully."""
    is_valid, status, msg = validate_python_syntax("def broken(:\n    pass\n")
    assert is_valid is False
    assert status == ValidationStatusEnum.FAILED


def test_fix_generator_bare_except():
    """Test 3: FixGenerator creates clean replacement for bare except."""
    issue = Issue(
        issue_id="fix-1",
        category=CategoryEnum.ERROR_HANDLING,
        severity=SeverityEnum.MEDIUM,
        confidence=1.0,
        line_start=3,
        line_end=3,
        code_snippet="except:",
        description="Bare except clause detected",
        why_it_matters="Catches system exit signals",
        detection_source=DetectionSourceEnum.STATIC,
    )
    code = "try:\n    x = 1/0\nexcept:\n    pass\n"

    generator = FixGenerator()
    fix = generator.generate_fix(issue, code)

    assert fix is not None
    assert "except Exception:" in fix.corrected_code
    assert fix.diff != ""


def test_test_generator_valid_pytest_output():
    """Test 4: TestGenerator produces syntactically valid pytest case."""
    issue = Issue(
        issue_id="test-1",
        category=CategoryEnum.LOGICAL_BUG,
        severity=SeverityEnum.HIGH,
        confidence=0.9,
        line_start=2,
        line_end=2,
        code_snippet="return a / b",
        description="Zero division risk",
        why_it_matters="Runtime crash",
        detection_source=DetectionSourceEnum.STATIC,
    )
    code = "def div(a, b):\n    return a / b\n"

    generator = TestGenerator()
    gen_test = generator.generate_test(issue, code)

    assert gen_test is not None
    assert "def test_regression_test_1():" in gen_test.test_code
    is_valid, status, _ = validate_python_syntax(gen_test.test_code)
    assert is_valid is True
