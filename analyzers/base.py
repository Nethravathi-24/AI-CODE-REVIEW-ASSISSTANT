"""Base abstract class and shared utilities for deterministic static analyzers."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import uuid4

from core.issue_model import Issue


class BaseAnalyzer(ABC):
    """Abstract base interface for deterministic static analysis tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier name of the analyzer (e.g. 'ast', 'pyflakes', 'bandit', 'radon', 'pycodestyle')."""
        pass

    @abstractmethod
    def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
        """Runs the static analysis check and converts native output into Issue objects.

        Args:
            code: Source code text to analyze.
            filename: Identifier or filename for tracking.

        Returns:
            List[Issue]: Standardized finding objects (detection_source="static").
        """
        pass

    @staticmethod
    def _get_code_snippet(code: str, line_start: int, line_end: int) -> str:
        """Extracts a slice of code lines (1-indexed, inclusive).

        Args:
            code: Full source code.
            line_start: 1-indexed start line.
            line_end: 1-indexed end line.

        Returns:
            str: Extracted snippet text.
        """
        lines = code.splitlines()
        start_idx = max(0, line_start - 1)
        end_idx = min(len(lines), max(start_idx + 1, line_end))
        if start_idx < len(lines):
            return "\n".join(lines[start_idx:end_idx])
        return ""

    @staticmethod
    def _generate_issue_id(tool_name: str, rule_name: str, line_start: int) -> str:
        """Generates a stable, readable unique ID for an issue."""
        clean_rule = rule_name.lower().replace(" ", "-").replace(":", "")[:24]
        rand_suffix = uuid4().hex[:6]
        return f"{tool_name}-{clean_rule}-L{line_start}-{rand_suffix}"
