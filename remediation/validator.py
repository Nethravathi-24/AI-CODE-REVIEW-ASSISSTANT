"""Safe static AST syntax check validator for fixes and generated tests.

CRITICAL SECURITY REQUIREMENT:
This module performs ONLY static ast.parse syntax checks.
It MUST NEVER use eval(), exec(), or run code in a subprocess.
"""

import ast
import difflib
from typing import Tuple
from core.issue_model import ValidationStatusEnum


def validate_python_syntax(code_snippet: str) -> Tuple[bool, ValidationStatusEnum, str]:
    """Validates Python syntax statically using ast.parse without executing code.

    Returns:
        (is_valid, validation_status, message)
    """
    if not code_snippet or not code_snippet.strip():
        return False, ValidationStatusEnum.FAILED, "Empty code snippet provided."

    try:
        ast.parse(code_snippet)
        return True, ValidationStatusEnum.PASSED, "Syntax check passed."
    except SyntaxError as err:
        return False, ValidationStatusEnum.FAILED, f"SyntaxError: {err.msg} at line {err.lineno}"
    except Exception as err:
        return False, ValidationStatusEnum.FAILED, f"Validation error: {err}"


def compute_unified_diff(original_code: str, corrected_code: str, filename: str = "submitted_code.py") -> str:
    """Generates a clean unified diff string comparing original and corrected code."""
    orig_lines = original_code.splitlines(keepends=True)
    corr_lines = corrected_code.splitlines(keepends=True)

    diff = difflib.unified_diff(
        orig_lines,
        corr_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        n=3,
    )
    return "".join(diff)
