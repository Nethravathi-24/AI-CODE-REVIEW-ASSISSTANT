"""Abstract base class and shared utilities for static analyzers."""

from abc import ABC, abstractmethod
import logging
from typing import List, Optional
import uuid

from core.issue_model import (
    CategoryEnum,
    DetectionSourceEnum,
    Fix,
    GeneratedTest,
    Issue,
    SeverityEnum,
)
from core.severity import calculate_severity

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """Abstract interface for all deterministic static analysis tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of analyzer (e.g. 'bandit', 'pyflakes')."""
        pass

    @abstractmethod
    def analyze(
        self, code: str, filename: str = "submitted_snippet"
    ) -> List[Issue]:
        """Runs static analysis checks and returns standardized Issue objects.

        Args:
            code: Source code text to analyze.
            filename: Identifier or filename for tracking.

        Returns:
            List[Issue]: List of static finding Issue objects.
        """
        pass

    @staticmethod
    def extract_code_snippet(
        code: str, line_start: int, line_end: Optional[int] = None
    ) -> str:
        """Extracts source lines for given 1-indexed line range.

        Args:
            code: Source code string.
            line_start: 1-indexed starting line.
            line_end: 1-indexed ending line (inclusive).

        Returns:
            str: Extracted snippet or fallback string.
        """
        if not code:
            return ""
        lines = code.splitlines()
        total_lines = len(lines)
        if total_lines == 0:
            return ""

        start_idx = max(1, min(line_start, total_lines)) - 1
        end_val = line_end if line_end is not None else line_start
        end_idx = max(
            start_idx + 1, min(max(end_val, line_start), total_lines)
        )

        selected = lines[start_idx:end_idx]
        return "\n".join(selected)

    def build_issue(
        self,
        category: CategoryEnum,
        description: str,
        why_it_matters: str,
        code: str = "",
        line_start: int = 1,
        line_end: Optional[int] = None,
        column: Optional[int] = None,
        severity: Optional[SeverityEnum] = None,
        confidence: float = 1.0,
        file: str = "submitted_snippet",
        code_snippet: Optional[str] = None,
        root_cause: Optional[str] = None,
        fix: Optional[Fix] = None,
        generated_test: Optional[GeneratedTest] = None,
        detection_source: DetectionSourceEnum = DetectionSourceEnum.STATIC,
        detecting_tool: Optional[str] = None,
        references: Optional[List[str]] = None,
        issue_id: Optional[str] = None,
    ) -> Issue:
        """Helper to construct a validated Issue instance with defaults."""
        effective_line_start = max(1, line_start)
        effective_line_end = max(
            effective_line_start,
            line_end if line_end is not None else effective_line_start,
        )

        if code_snippet is None:
            code_snippet = self.extract_code_snippet(
                code, effective_line_start, effective_line_end
            )

        if severity is None:
            severity = calculate_severity(category, confidence=confidence)

        if not issue_id:
            short_id = uuid.uuid4().hex[:8]
            tool_prefix = (detecting_tool or self.name).replace("_", "-")
            issue_id = (
                f"{tool_prefix}-{category.value}-"
                f"{effective_line_start}-{short_id}"
            )

        return Issue(
            issue_id=issue_id,
            category=category,
            severity=severity,
            confidence=max(0.0, min(1.0, confidence)),
            file=file or "submitted_snippet",
            line_start=effective_line_start,
            line_end=effective_line_end,
            column=column if column is not None and column >= 0 else None,
            code_snippet=code_snippet,
            description=description,
            why_it_matters=why_it_matters,
            root_cause=root_cause,
            fix=fix,
            generated_test=generated_test,
            detection_source=detection_source,
            detecting_tool=detecting_tool or self.name,
            references=references,
        )
