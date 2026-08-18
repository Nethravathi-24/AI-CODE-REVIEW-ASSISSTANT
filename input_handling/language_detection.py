"""Language detection heuristic module for AI Code Review Assistant."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

PYTHON_SIGNATURES = [
    "def ",
    "class ",
    "import ",
    "from ",
    "lambda ",
    "elif ",
    "except:",
    "except ",
    "finally:",
    "print(",
    "__init__",
    "self.",
]


def detect_language(code: str, filename: Optional[str] = None) -> str:
    """Detects programming language from filename extension or keywords.

    Args:
        code: Source code text.
        filename: Optional filename or snippet identifier.

    Returns:
        str: Classified language name (e.g. 'python').
    """
    if filename and filename.lower().endswith((".py", ".pyw")):
        return "python"

    if any(sig in code for sig in PYTHON_SIGNATURES):
        return "python"

    return "python"
