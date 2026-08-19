"""Static analyzers package exposing BaseAnalyzer, real language AST tools, and analyzer capability routing."""

from typing import List

from analyzers.ast_analyzer import ASTAnalyzer
from analyzers.bandit_analyzer import BanditAnalyzer
from analyzers.base import BaseAnalyzer
from analyzers.java_analyzer import JavaAnalyzer
from analyzers.js_analyzer import JSAnalyzer
from analyzers.pyflakes_analyzer import PyflakesAnalyzer
from analyzers.radon_analyzer import RadonAnalyzer
from analyzers.style_analyzer import StyleAnalyzer
from analyzers.ts_analyzer import TSAnalyzer


def get_default_analyzers() -> List[BaseAnalyzer]:
    """Returns initialized instances of standard deterministic Python static analyzers."""
    return [
        ASTAnalyzer(),
        PyflakesAnalyzer(),
        BanditAnalyzer(),
        RadonAnalyzer(),
        StyleAnalyzer(),
    ]


def get_analyzers_for_language(language: str) -> List[BaseAnalyzer]:
    """Returns static analyzers configured for target programming language.

    Args:
        language: Language identifier string ('python', 'javascript', 'typescript', 'java').

    Returns:
        List[BaseAnalyzer]: Active language static analyzers.
    """
    lang_clean = (language or "python").lower().strip()

    if lang_clean in ("python", "py"):
        return [
            ASTAnalyzer(),
            PyflakesAnalyzer(),
            BanditAnalyzer(),
            RadonAnalyzer(),
            StyleAnalyzer(),
        ]
    elif lang_clean in ("javascript", "js", "jsx"):
        return [JSAnalyzer()]
    elif lang_clean in ("typescript", "ts", "tsx"):
        return [TSAnalyzer()]
    elif lang_clean == "java":
        return [JavaAnalyzer()]
    else:
        # Unsupported languages cleanly skip static analysis (PRD Part 5.3)
        return []


__all__ = [
    "BaseAnalyzer",
    "ASTAnalyzer",
    "PyflakesAnalyzer",
    "BanditAnalyzer",
    "RadonAnalyzer",
    "StyleAnalyzer",
    "JSAnalyzer",
    "TSAnalyzer",
    "JavaAnalyzer",
    "get_default_analyzers",
    "get_analyzers_for_language",
]
