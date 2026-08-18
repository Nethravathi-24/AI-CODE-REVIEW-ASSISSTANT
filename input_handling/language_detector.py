"""Language detection component for AI Code Review Assistant."""

import os
import re
from typing import Optional, Set
from input_handling.models import LanguageDetectionResult

SUPPORTED_LANGUAGES: Set[str] = {"python"}

PYTHON_KEYWORD_PATTERNS = [
    r"\bdef\s+[a-zA-Z_]\w*\s*\(",
    r"\bclass\s+[a-zA-Z_]\w*",
    r"\bimport\s+[a-zA-Z_]",
    r"\bfrom\s+[a-zA-Z_]\w*\s+import\b",
    r"\bif\s+__name__\s*==\s*['\"]__main__['\"]:",
    r"\bprint\s*\(",
    r"\bself\.",
    r"\bprint\b",
    r"^\s*#\s+.*",
    r"\belif\s+.*:",
    r"\basync\s+def\b",
    r"\braise\s+[a-zA-Z_]\w*",
]


def detect_language(
    code: str,
    filename: Optional[str] = None,
    override_language: Optional[str] = None,
) -> LanguageDetectionResult:
    """Detects the programming language of the submitted code.

    Priority:
    1. Manual user override selection.
    2. File extension if uploaded.
    3. Keyword / syntax pattern heuristics.
    4. Default fallback to unknown.

    Args:
        code: Preprocessed code text.
        filename: Optional uploaded filename.
        override_language: Optional manual language override string.

    Returns:
        LanguageDetectionResult: Structured detection outcome.
    """
    # 1. Manual User Override
    if override_language and override_language.strip():
        lang_clean = override_language.strip().lower()
        is_supp = lang_clean in SUPPORTED_LANGUAGES
        return LanguageDetectionResult(
            detected_language=lang_clean,
            confidence=1.0,
            source="override",
            is_supported=is_supp,
        )

    # 2. File Extension
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".py":
            return LanguageDetectionResult(
                detected_language="python",
                confidence=1.0,
                source="file_extension",
                is_supported=True,
            )

    # 3. Python Keyword Heuristics
    matches = 0
    for pattern in PYTHON_KEYWORD_PATTERNS:
        if re.search(pattern, code, re.MULTILINE):
            matches += 1

    if matches >= 1:
        # Confidence scales with number of matched pattern indicators
        confidence = min(0.70 + (matches * 0.10), 0.95)
        return LanguageDetectionResult(
            detected_language="python",
            confidence=confidence,
            source="heuristics",
            is_supported=True,
        )

    # 4. Fallback / Unknown
    return LanguageDetectionResult(
        detected_language="unknown",
        confidence=0.0,
        source="fallback",
        is_supported=False,
    )
