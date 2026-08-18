"""Language detection module with heuristic analysis and manual override support."""

import os
import re
from typing import List, Optional, Tuple

from input_handling.models import LanguageDetectionResult

# Python characteristic patterns with assigned weights
PYTHON_PATTERNS = [
    (r"^\s*def\s+[a-zA-Z_]\w*\s*\(", 0.30, "function_def"),
    (r"^\s*class\s+[a-zA-Z_]\w*", 0.25, "class_def"),
    (r"^\s*from\s+[a-zA-Z_][\w.]*\s+import\s+", 0.30, "from_import"),
    (r"^\s*import\s+[a-zA-Z_][\w.]*", 0.25, "import_stmt"),
    (r"if\s+__name__\s*==\s*['\"]__main__['\"]:", 0.35, "main_guard"),
    (r"^\s*async\s+def\s+[a-zA-Z_]\w*\s*\(", 0.30, "async_def"),
    (r"^\s*elif\s+", 0.20, "elif_block"),
    (r"^\s*except(\s+[a-zA-Z_][\w.]*(\s+as\s+[a-zA-Z_]\w*)?)?\s*:", 0.25, "except_block"),
    (r"^\s*with\s+.+\s+as\s+[a-zA-Z_]\w*\s*:", 0.25, "with_stmt"),
    (r"^\s*@[a-zA-Z_][\w.]*", 0.20, "decorator"),
    (r"\bself\.[a-zA-Z_]\w*", 0.20, "self_reference"),
    (r"\b__init__\b", 0.25, "init_dunder"),
    (r"\blambda\s+[a-zA-Z_]\w*\s*:", 0.20, "lambda_expr"),
    (r"\b(None|True|False)\b", 0.10, "py_literal"),
    (r"^\s*print\s*\(", 0.15, "print_call"),
    (r"^\s*#\s+.*", 0.05, "hash_comment"),
]

# Non-Python signature patterns used to detect alternative languages and penalize Python confidence
NON_PYTHON_LANGUAGES = [
    (
        "javascript",
        [
            (r"\bfunction\s+[a-zA-Z_]\w*\s*\(", 0.35),
            (r"\b(const|let|var)\s+[a-zA-Z_]\w*\s*=", 0.35),
            (r"\bconsole\.log\s*\(", 0.40),
            (r"=>\s*\{", 0.30),
            (r"\b(export\s+default|module\.exports)\b", 0.40),
        ],
    ),
    (
        "java",
        [
            (r"\bpublic\s+(static\s+)?(void|class|int|String|boolean)\b", 0.45),
            (r"\bSystem\.out\.println\s*\(", 0.45),
            (r"\bpackage\s+[a-zA-Z_][\w.]*;", 0.40),
        ],
    ),
    (
        "c_cpp",
        [
            (r"#include\s+<[a-zA-Z0-9_.]+>", 0.45),
            (r"\b(std::cout|std::vector|std::string)\b", 0.45),
            (r"\bint\s+main\s*\(\s*(int\s+argc)?", 0.35),
        ],
    ),
    (
        "go",
        [
            (r"\bfunc\s+([a-zA-Z_]\w*\s+)?\w+\s*\(", 0.45),
            (r"\bpackage\s+[a-zA-Z_]\w*", 0.40),
            (r"\bfmt\.Print", 0.40),
        ],
    ),
    (
        "rust",
        [
            (r"\bfn\s+[a-zA-Z_]\w*\s*\(", 0.45),
            (r"\blet\s+mut\s+[a-zA-Z_]\w*", 0.40),
            (r"\bprintln!\s*\(", 0.45),
        ],
    ),
    (
        "html",
        [
            (r"<!DOCTYPE\s+html>", 0.50),
            (r"<(html|head|body|div|script|style)[\s>]", 0.45),
        ],
    ),
]


def detect_language(
    code: str,
    filename: Optional[str] = None,
    manual_override: Optional[str] = None,
) -> LanguageDetectionResult:
    """Detects programming language of code snippet using manual override, extension, and heuristics.

    Args:
        code: Submitted source code text.
        filename: Optional filename or identifier.
        manual_override: User-selected language override (takes highest precedence).

    Returns:
        LanguageDetectionResult: Model with detected language, confidence, and signatures.
    """
    # 1. Manual Override Handling
    if manual_override and manual_override.strip():
        override_clean = manual_override.strip().lower()
        if override_clean in ("python", "py", "python3", "py3"):
            return LanguageDetectionResult(
                language="python",
                confidence=1.0,
                is_python=True,
                detection_method="manual_override",
                matched_signatures=["manual_override:python"],
            )
        return LanguageDetectionResult(
            language=override_clean,
            confidence=1.0,
            is_python=False,
            detection_method="manual_override",
            matched_signatures=[f"manual_override:{override_clean}"],
        )

    matched_signatures: List[str] = []
    confidence_score: float = 0.0

    # 2. File Extension Detection
    has_py_extension = False
    if filename:
        clean_name = filename.strip()
        if clean_name not in ("submitted_snippet", "<stdin>", ""):
            ext = os.path.splitext(clean_name)[1].lower()
            if ext in (".py", ".pyw"):
                has_py_extension = True
                confidence_score += 0.60
                matched_signatures.append(f"extension:{ext}")

    # 3. Python Characteristic Heuristic Pattern Matching
    for pattern, weight, sig_name in PYTHON_PATTERNS:
        if re.search(pattern, code, re.MULTILINE):
            confidence_score += weight
            matched_signatures.append(sig_name)

    # 4. Check for Non-Python language signatures
    strongest_non_py_lang: Optional[str] = None
    strongest_non_py_score = 0.0

    for lang_name, patterns in NON_PYTHON_LANGUAGES:
        lang_score = 0.0
        for pattern, weight in patterns:
            if re.search(pattern, code, re.MULTILINE):
                lang_score += weight
        if lang_score > strongest_non_py_score:
            strongest_non_py_score = lang_score
            strongest_non_py_lang = lang_name

    # Penalize Python confidence if non-Python signatures are strongly present
    if strongest_non_py_score > 0.3:
        confidence_score -= strongest_non_py_score * 0.8
        if strongest_non_py_lang:
            matched_signatures.append(f"conflict:{strongest_non_py_lang}")

    # 5. Determine Final Classification
    final_confidence = max(0.0, min(1.0, round(confidence_score, 2)))

    # High-confidence Python
    if has_py_extension:
        # If extension is .py and not completely overrun by another language
        if final_confidence >= 0.40:
            method = "file_extension" if not (set(matched_signatures) - {f"extension:{ext}"}) else "heuristic"
            return LanguageDetectionResult(
                language="python",
                confidence=max(0.70, final_confidence),
                is_python=True,
                detection_method=method,
                matched_signatures=matched_signatures,
            )

    if final_confidence >= 0.50:
        return LanguageDetectionResult(
            language="python",
            confidence=final_confidence,
            is_python=True,
            detection_method="heuristic",
            matched_signatures=matched_signatures,
        )

    # If another language has clear signal
    if strongest_non_py_lang and strongest_non_py_score >= 0.40:
        return LanguageDetectionResult(
            language=strongest_non_py_lang,
            confidence=min(1.0, round(strongest_non_py_score, 2)),
            is_python=False,
            detection_method="heuristic",
            matched_signatures=matched_signatures,
        )

    # Low confidence / Ambiguous / Unknown
    return LanguageDetectionResult(
        language="unknown",
        confidence=final_confidence,
        is_python=False,
        detection_method="fallback",
        matched_signatures=matched_signatures,
    )
