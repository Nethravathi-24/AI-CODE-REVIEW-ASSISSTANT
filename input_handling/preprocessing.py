"""Code preprocessing and normalization module for AI Code Review Assistant."""

import ast
import logging
from typing import Optional, Tuple

from core.issue_model import (
    CategoryEnum,
    DetectionSourceEnum,
    Issue,
    SeverityEnum,
)

logger = logging.getLogger(__name__)


def preprocess_code(
    code: str, filename: str = "submitted_snippet"
) -> Tuple[str, Optional[Issue]]:
    """Normalizes CRLF line endings to LF and validates Python syntax.

    Args:
        code: Raw source code text.
        filename: Identifier or filename for tracking.

    Returns:
        Tuple[str, Optional[Issue]]: (normalized_code, syntax_issue_if_any)
    """
    normalized = code.replace("\r\n", "\n").replace("\r", "\n")

    try:
        ast.parse(normalized, filename=filename)
        return normalized, None
    except SyntaxError as e:
        line_num = max(1, e.lineno or 1)
        col_num = e.offset - 1 if e.offset and e.offset > 0 else 0
        lines = normalized.splitlines()
        snippet = (
            lines[line_num - 1]
            if line_num <= len(lines)
            else (e.text.strip() if e.text else "")
        )

        syntax_issue = Issue(
            issue_id=f"syntax-error-{line_num}",
            category=CategoryEnum.SYNTAX_ERROR,
            severity=SeverityEnum.CRITICAL,
            confidence=1.0,
            file=filename,
            line_start=line_num,
            line_end=line_num,
            column=col_num,
            code_snippet=snippet,
            description=f"SyntaxError: {e.msg}",
            why_it_matters=(
                "Syntax errors prevent Python code from compiling "
                "or executing."
            ),
            detection_source=DetectionSourceEnum.STATIC,
            detecting_tool="preprocessor",
        )
        return normalized, syntax_issue
    except Exception as e:
        logger.error(f"Preprocessing error: {e}", exc_info=True)
        return normalized, None
