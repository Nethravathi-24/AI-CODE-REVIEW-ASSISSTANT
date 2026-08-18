"""Radon complexity analyzer wrapper calculating cyclomatic complexity per function."""

from typing import List
from radon.complexity import cc_visit

from analyzers.base import BaseAnalyzer
from core.issue_model import (
    CategoryEnum,
    DetectionSourceEnum,
    Issue,
    SeverityEnum,
)


class RadonAnalyzer(BaseAnalyzer):
    """Programmatic Radon wrapper flagging functions with cyclomatic complexity exceeding threshold."""

    def __init__(self, complexity_threshold: int = 10) -> None:
        self.complexity_threshold = complexity_threshold

    @property
    def name(self) -> str:
        return "radon"

    def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
        """Calculates cyclomatic complexity and flags complex functions/methods."""
        issues: List[Issue] = []

        try:
            blocks = cc_visit(code)
        except Exception:
            # If code has syntax errors or Radon fails to parse, exit safely
            return issues

        for block in blocks:
            complexity = getattr(block, "complexity", 1)
            if complexity > self.complexity_threshold:
                line_start = getattr(block, "lineno", 1)
                line_end = getattr(block, "endline", line_start)
                if line_end < line_start:
                    line_end = line_start

                snippet = self._get_code_snippet(code, line_start, line_start)
                name = getattr(block, "name", "function")
                rank = getattr(block, "letter", "C")

                severity = SeverityEnum.HIGH if complexity >= 20 else SeverityEnum.MEDIUM

                description = (
                    f"Function '{name}' has high cyclomatic complexity (CC = {complexity}, Rank '{rank}'). "
                    f"Threshold is {self.complexity_threshold}."
                )

                issues.append(
                    Issue(
                        issue_id=self._generate_issue_id("radon", "cyclomatic-complexity", line_start),
                        category=CategoryEnum.MAINTAINABILITY,
                        severity=severity,
                        confidence=1.0,
                        file=filename,
                        line_start=line_start,
                        line_end=line_end,
                        column=getattr(block, "col_offset", None),
                        code_snippet=snippet,
                        description=description,
                        why_it_matters=(
                            "Functions with cyclomatic complexity > 10 contain too many independent execution paths, "
                            "making them prone to regression bugs, difficult to understand, and hard to test thoroughly."
                        ),
                        root_cause=f"High branching complexity (CC = {complexity}) exceeds limit of {self.complexity_threshold}.",
                        detection_source=DetectionSourceEnum.STATIC,
                        detecting_tool="radon",
                        references=[f"radon.CC={complexity}", f"radon.Rank={rank}"],
                    )
                )

        return issues
