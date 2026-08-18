"""Static analyzers package exposing BaseAnalyzer and tool wrappers."""

from typing import List

from analyzers.ast_analyzer import ASTAnalyzer
from analyzers.bandit_analyzer import BanditAnalyzer
from analyzers.base import BaseAnalyzer
from analyzers.pyflakes_analyzer import PyflakesAnalyzer
from analyzers.radon_analyzer import RadonAnalyzer
from analyzers.style_analyzer import StyleAnalyzer


def get_default_analyzers() -> List[BaseAnalyzer]:
    """Returns initialized instances of all standard deterministic static analyzers."""
    return [
        ASTAnalyzer(),
        PyflakesAnalyzer(),
        BanditAnalyzer(),
        RadonAnalyzer(),
        StyleAnalyzer(),
    ]


__all__ = [
    "BaseAnalyzer",
    "ASTAnalyzer",
    "PyflakesAnalyzer",
    "BanditAnalyzer",
    "RadonAnalyzer",
    "StyleAnalyzer",
    "get_default_analyzers",
]
