"""Base abstract class and capability metadata interface for static analyzers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import uuid4

from core.issue_model import Issue


class BaseAnalyzer(ABC):
    """Abstract base interface for deterministic static analysis tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier name of the analyzer."""
        pass

    @property
    def language(self) -> str:
        """Target programming language identifier (e.g. 'python', 'javascript', 'typescript', 'java')."""
        return "python"

    @property
    def analyzer_type(self) -> str:
        """Type category of the analyzer (e.g. 'ast_linter', 'ast_walker', 'cli_compiler')."""
        return "ast_walker"

    @property
    def tool_name(self) -> str:
        """Underlying parser or engine name (e.g. 'ast', 'esprima', 'tree_sitter', 'javalang', 'javac')."""
        return self.name

    def is_available(self) -> bool:
        """Returns True if the underlying tool/library is installed and operational."""
        return True

    def get_availability_reason(self) -> str:
        """Human-readable explanation of tool availability status."""
        return "Operational" if self.is_available() else "Required analyzer library or binary unavailable"

    def get_metadata(self) -> Dict[str, Any]:
        """Returns structured capability metadata for UI and reporting facades."""
        return {
            "language": self.language,
            "analyzer": self.name,
            "tool_name": self.tool_name,
            "type": self.analyzer_type,
            "available": self.is_available(),
            "reason": self.get_availability_reason(),
        }

    @abstractmethod
    def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
        """Runs static analysis check and converts output into canonical Issue objects."""
        pass

    @staticmethod
    def _get_code_snippet(code: str, line_start: int, line_end: int) -> str:
        """Extracts a slice of code lines (1-indexed, inclusive)."""
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
