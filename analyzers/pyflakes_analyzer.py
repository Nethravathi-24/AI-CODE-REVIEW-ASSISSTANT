"""Pyflakes static analyzer wrapper capturing undefined variables, unused imports, and name shadowing."""

import ast
from typing import List
from pyflakes import checker, messages

from analyzers.base import BaseAnalyzer
from core.issue_model import (
    CategoryEnum,
    DetectionSourceEnum,
    Issue,
    SeverityEnum,
)


class PyflakesAnalyzer(BaseAnalyzer):
    """Programmatic Pyflakes wrapper translating findings to domain Issue models."""

    @property
    def name(self) -> str:
        return "pyflakes"

    def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
        """Runs Pyflakes analysis programmatically on source code text."""
        issues: List[Issue] = []

        try:
            tree = ast.parse(code, filename=filename)
        except (SyntaxError, IndentationError):
            # Syntax errors are handled by ASTAnalyzer; Pyflakes exits cleanly
            return issues

        try:
            w = checker.Checker(tree, filename=filename)
        except Exception:
            # Fault-tolerant fallback if Pyflakes internal inspection fails
            return issues

        for msg in w.messages:
            line_no = getattr(msg, "lineno", 1)
            col_no = getattr(msg, "col", 0)
            snippet = self._get_code_snippet(code, line_no, line_no)

            msg_type = type(msg).__name__
            formatted_desc = msg.message % msg.message_args if hasattr(msg, "message_args") else str(msg)

            if isinstance(msg, messages.UndefinedName):
                category = CategoryEnum.LOGICAL_BUG
                severity = SeverityEnum.HIGH
                why_matters = (
                    "Referencing an undefined variable raises a NameError at runtime and will crash execution."
                )
            elif isinstance(msg, messages.UnusedImport):
                category = CategoryEnum.BEST_PRACTICE
                severity = SeverityEnum.LOW
                why_matters = (
                    "Unused imports clutter namespace, increase startup latency, and can mask dependencies."
                )
            elif isinstance(msg, messages.UnusedVariable):
                category = CategoryEnum.CODE_QUALITY
                severity = SeverityEnum.LOW
                why_matters = (
                    "Unused local variables indicate dead code or incomplete logic."
                )
            elif isinstance(msg, messages.DuplicateArgument):
                category = CategoryEnum.LOGICAL_BUG
                severity = SeverityEnum.HIGH
                why_matters = (
                    "Duplicate parameter names lead to ambiguous argument binding and unexpected behavior."
                )
            else:
                category = CategoryEnum.CODE_QUALITY
                severity = SeverityEnum.LOW
                why_matters = "Code structure violates static analysis guidelines."

            issues.append(
                Issue(
                    issue_id=self._generate_issue_id("pyflakes", msg_type, line_no),
                    category=category,
                    severity=severity,
                    confidence=1.0,
                    file=filename,
                    line_start=line_no,
                    line_end=line_no,
                    column=col_no,
                    code_snippet=snippet,
                    description=formatted_desc,
                    why_it_matters=why_matters,
                    root_cause=f"Pyflakes reported {msg_type}",
                    detection_source=DetectionSourceEnum.STATIC,
                    detecting_tool="pyflakes",
                    references=[f"pyflakes.{msg_type}"],
                )
            )

        return issues
