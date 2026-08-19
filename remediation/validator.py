"""Safe static syntax check validator for fixes and generated tests across supported languages.

CRITICAL SECURITY REQUIREMENT:
This module performs ONLY static parser AST syntax checks.
It MUST NEVER use eval(), exec(), or run code in a subprocess for execution.
"""

import ast
import difflib
import logging
from typing import Tuple
from core.issue_model import ValidationStatusEnum

logger = logging.getLogger(__name__)

try:
    import esprima
    ESPRIMA_AVAILABLE = True
except ImportError:
    ESPRIMA_AVAILABLE = False

try:
    import tree_sitter
    import tree_sitter_typescript
    TREE_SITTER_TS_AVAILABLE = True
except ImportError:
    TREE_SITTER_TS_AVAILABLE = False

try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False


def validate_python_syntax(code_snippet: str) -> Tuple[bool, ValidationStatusEnum, str]:
    """Validates Python syntax statically using ast.parse without executing code.

    Returns:
        (is_valid, validation_status, message)
    """
    if not code_snippet or not code_snippet.strip():
        return False, ValidationStatusEnum.FAILED, "Empty code snippet provided."

    try:
        ast.parse(code_snippet)
        return True, ValidationStatusEnum.PASSED, "Python AST syntax check passed (FULL validation)."
    except SyntaxError as err:
        return False, ValidationStatusEnum.FAILED, f"Python SyntaxError: {err.msg} at line {err.lineno}"
    except Exception as err:
        return False, ValidationStatusEnum.FAILED, f"Python Validation error: {err}"


def validate_code_syntax(code_snippet: str, language: str = "python") -> Tuple[bool, ValidationStatusEnum, str]:
    """Validates code syntax statically for Python, JS, TS, and Java using real language AST parsers.

    Args:
        code_snippet: Code string to validate.
        language: Programming language identifier.

    Returns:
        (is_valid, validation_status, message)
    """
    if not code_snippet or not code_snippet.strip():
        return False, ValidationStatusEnum.FAILED, "Empty code snippet provided."

    lang_clean = (language or "python").lower().strip()

    # 1. Python Syntax Validation via ast.parse
    if lang_clean in ("python", "py"):
        return validate_python_syntax(code_snippet)

    # 2. JavaScript Syntax Validation via Esprima AST parser
    elif lang_clean in ("javascript", "js", "jsx"):
        if ESPRIMA_AVAILABLE:
            try:
                esprima.parseScript(code_snippet, tolerant=False)
                return True, ValidationStatusEnum.PASSED, "Esprima JavaScript AST parse succeeded (FULL validation)."
            except Exception:
                try:
                    esprima.parseModule(code_snippet, tolerant=False)
                    return True, ValidationStatusEnum.PASSED, "Esprima JavaScript Module AST parse succeeded (FULL validation)."
                except Exception as err:
                    msg = getattr(err, "description", str(err))
                    line_no = getattr(err, "lineNumber", 1)
                    return False, ValidationStatusEnum.FAILED, f"JavaScript SyntaxError: {msg} at line {line_no}"
        else:
            return False, ValidationStatusEnum.NOT_VALIDATED, "Esprima parser unavailable (PARTIAL delimiter check only)."

    # 3. TypeScript Syntax Validation via Tree-Sitter TypeScript AST parser
    elif lang_clean in ("typescript", "ts", "tsx"):
        if TREE_SITTER_TS_AVAILABLE:
            try:
                is_tsx = lang_clean == "tsx"
                ts_lang_fn = (
                    tree_sitter_typescript.language_tsx
                    if is_tsx
                    else tree_sitter_typescript.language_typescript
                )
                lang = tree_sitter.Language(ts_lang_fn())
                parser = tree_sitter.Parser(lang)
                tree = parser.parse(code_snippet.encode("utf-8"))
                if tree.root_node.has_error:
                    return False, ValidationStatusEnum.FAILED, "Tree-Sitter TypeScript AST detected syntax error node."
                return True, ValidationStatusEnum.PASSED, "Tree-Sitter TypeScript AST parse succeeded (FULL validation)."
            except Exception as err:
                return False, ValidationStatusEnum.FAILED, f"TypeScript AST parse error: {err}"
        else:
            return False, ValidationStatusEnum.NOT_VALIDATED, "Tree-Sitter TypeScript parser unavailable (PARTIAL validation)."

    # 4. Java Syntax Validation via Javalang AST parser
    elif lang_clean == "java":
        if JAVALANG_AVAILABLE:
            try:
                javalang.parse.parse(code_snippet)
                return True, ValidationStatusEnum.PASSED, "Javalang Java AST parse succeeded (FULL validation)."
            except javalang.parser.JavaSyntaxError as err:
                line_no = getattr(err.at, "line", 1) if getattr(err, "at", None) else 1
                msg = getattr(err, "description", str(err))
                return False, ValidationStatusEnum.FAILED, f"Java SyntaxError: {msg} at line {line_no}"
            except Exception as err:
                return False, ValidationStatusEnum.FAILED, f"Java parse error: {err}"
        else:
            return False, ValidationStatusEnum.NOT_VALIDATED, "Javalang parser unavailable (PARTIAL validation)."

    # 5. Unsupported languages
    return True, ValidationStatusEnum.NOT_VALIDATED, f"No native AST parser available for '{language}' (PARTIAL validation)."


def compute_unified_diff(original_code: str, corrected_code: str, filename: str = "submitted_code") -> str:
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
