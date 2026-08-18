"""PEP 8 Style Analyzer wrapper using pycodestyle to detect formatting and readability issues."""

from typing import List
import pycodestyle

from analyzers.base import BaseAnalyzer
from core.issue_model import (
    CategoryEnum,
    DetectionSourceEnum,
    Issue,
    SeverityEnum,
)


class _InMemoryStyleReport(pycodestyle.BaseReport):
    """Custom in-memory pycodestyle report collecting findings without writing to stdout."""

    def __init__(self, options) -> None:
        super().__init__(options)
        self.findings = []

    def error(self, line_number: int, offset: int, text: str, check) -> str:
        rule_code = text[:4]
        message = text[5:]
        self.findings.append({
            "line_number": line_number,
            "column": offset,
            "rule_code": rule_code,
            "message": message,
        })
        return rule_code


class StyleAnalyzer(BaseAnalyzer):
    """Programmatic PEP 8 style analyzer checking code formatting and readability."""

    def __init__(self, max_line_length: int = 79) -> None:
        self.max_line_length = max_line_length
        self._style_guide = pycodestyle.StyleGuide(
            max_line_length=self.max_line_length,
            quiet=True,
        )

    @property
    def name(self) -> str:
        return "pycodestyle"

    def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
        """Runs pycodestyle in-memory over code lines."""
        issues: List[Issue] = []
        if not code.strip():
            return issues

        # Prepare line array with trailing newlines
        lines = [line + "\n" for line in code.splitlines()]
        if not lines:
            return issues

        report = _InMemoryStyleReport(self._style_guide.options)
        try:
            checker = pycodestyle.Checker(
                filename=filename,
                lines=lines,
                options=self._style_guide.options,
                report=report,
            )
            checker.check_all()
        except Exception:
            return issues

        for item in report.findings:
            line_no = item["line_number"]
            col_no = item["column"]
            rule_code = item["rule_code"]
            msg = item["message"]
            snippet = self._get_code_snippet(code, line_no, line_no)

            is_warning = rule_code.startswith("W")
            category = CategoryEnum.READABILITY if rule_code.startswith(("E5", "E1", "E2", "W")) else CategoryEnum.BEST_PRACTICE
            severity = SeverityEnum.INFORMATIONAL if is_warning else SeverityEnum.LOW

            description = f"[{rule_code}] {msg}"
            why_it_matters = (
                "Adhering to PEP 8 styling conventions ensures consistency, "
                "enhances readability, and reduces cognitive strain for code reviewers."
            )

            issues.append(
                Issue(
                    issue_id=self._generate_issue_id("style", rule_code, line_no),
                    category=category,
                    severity=severity,
                    confidence=1.0,
                    file=filename,
                    line_start=line_no,
                    line_end=line_no,
                    column=col_no,
                    code_snippet=snippet,
                    description=description,
                    why_it_matters=why_it_matters,
                    root_cause=f"PEP 8 style guide rule {rule_code} violated.",
                    detection_source=DetectionSourceEnum.STATIC,
                    detecting_tool="pycodestyle",
                    references=[f"PEP-8.{rule_code}"],
                )
            )

        return issues
