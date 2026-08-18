"""Preprocessing and Python AST parse validation component."""

import ast
from typing import Optional
from input_handling.models import PreprocessorResult


def preprocess_code(code: str) -> PreprocessorResult:
    """Preprocesses source code by normalizing line endings and performing AST syntax validation.

    CRITICAL RULES:
    1. Original source code is preserved untouched in original_code.
    2. Line endings normalized (CRLF -> LF) to ensure consistent line-number tracking.
    3. Python syntax validation performed strictly via ast.parse without executing code.
    4. Syntax errors are captured as structured data rather than crashing callers.

    Args:
        code: Decoded source code text.

    Returns:
        PreprocessorResult: Model containing original code, normalized code, and syntax validation status.
    """
    original_code = code

    # Line ending normalization (CRLF -> LF, standalone CR -> LF)
    normalized_code = code.replace("\r\n", "\n").replace("\r", "\n")

    # Compute line count
    lines = normalized_code.split("\n")
    line_count = len(lines)

    # AST Parse Syntax Validation
    is_syntax_valid = True
    syntax_error_message: Optional[str] = None
    syntax_error_lineno: Optional[int] = None
    syntax_error_offset: Optional[int] = None

    try:
        ast.parse(normalized_code, filename="submitted_snippet")
    except SyntaxError as e:
        is_syntax_valid = False
        syntax_error_message = e.msg or str(e)
        syntax_error_lineno = e.lineno
        syntax_error_offset = e.offset
    except Exception as e:
        is_syntax_valid = False
        syntax_error_message = f"Parse failure: {str(e)}"

    return PreprocessorResult(
        original_code=original_code,
        normalized_code=normalized_code,
        is_syntax_valid=is_syntax_valid,
        syntax_error_message=syntax_error_message,
        syntax_error_lineno=syntax_error_lineno,
        syntax_error_offset=syntax_error_offset,
        line_count=line_count,
    )
