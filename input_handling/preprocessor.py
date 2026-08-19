"""Code preprocessing module for line normalization, offset mapping, and AST syntax validation."""

import ast
from typing import List, Optional

from core.issue_model import (
    CategoryEnum,
    DetectionSourceEnum,
    Issue,
    SeverityEnum,
)
from input_handling.models import PreprocessedCode


def preprocess_code(
    code: str,
    filename: Optional[str] = "submitted_snippet",
    language: str = "python",
) -> PreprocessedCode:
    """Normalizes code line endings, computes line offset maps, and validates Python AST syntax if Python.

    Args:
        code: Submitted raw source code string.
        filename: Optional filename or identifier for line tracking.
        language: Language identifier string (defaults to 'python').

    Returns:
        PreprocessedCode: Model containing normalized code, AST tree (for Python), and any syntax Issue.
    """
    effective_filename = filename or "submitted_snippet"

    # 1. Normalize line endings (CRLF and CR to standard LF) and strip BOM
    normalized_code = code.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")

    # 2. Compute line count and 0-indexed character offsets
    lines = normalized_code.split("\n")
    line_count = len(lines)

    line_offsets: List[int] = []
    current_offset = 0
    for line in lines:
        line_offsets.append(current_offset)
        current_offset += len(line) + 1  # 1 byte/char for newline '\n'

    # 3. Validate syntax statically based on target language
    ast_tree = None
    syntax_error: Optional[Issue] = None
    is_valid_syntax = True

    if language.lower() in ("python", "py"):
        try:
            ast_tree = ast.parse(normalized_code, filename=effective_filename)
            is_valid_syntax = True
        except (SyntaxError, IndentationError) as err:
            is_valid_syntax = False
            ast_tree = None

            line_number = err.lineno if err.lineno is not None and err.lineno > 0 else 1
            end_line = getattr(err, "end_lineno", None)
            if end_line is None or end_line < line_number:
                end_line = line_number

            column = err.offset if err.offset is not None and err.offset >= 0 else 0
            error_msg = err.msg or "Invalid Python syntax"

            snippet = ""
            if err.text:
                snippet = err.text.rstrip("\r\n")
            elif 1 <= line_number <= len(lines):
                snippet = lines[line_number - 1]

            syntax_error = Issue(
                issue_id=f"syntax-err-line-{line_number}",
                category=CategoryEnum.SYNTAX_ERROR,
                severity=SeverityEnum.CRITICAL,
                confidence=1.0,
                file=effective_filename,
                line_start=line_number,
                line_end=end_line,
                column=column,
                code_snippet=snippet,
                description=f"Syntax Error: {error_msg}",
                why_it_matters=(
                    "Code containing syntax errors cannot be parsed or analyzed by "
                    "static AST tools and will fail execution."
                ),
                root_cause=f"Python parser raised {type(err).__name__}: {error_msg}",
                detection_source=DetectionSourceEnum.STATIC,
                detecting_tool="ast_parser",
            )

    return PreprocessedCode(
        original_code=code,
        normalized_code=normalized_code,
        line_count=line_count,
        line_offsets=line_offsets,
        is_valid_syntax=is_valid_syntax,
        syntax_error=syntax_error,
        ast_tree=ast_tree,
    )
