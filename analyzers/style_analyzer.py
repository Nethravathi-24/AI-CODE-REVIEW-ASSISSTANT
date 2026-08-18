"""PEP 8 style analyzer wrapping pycodestyle purely via Python API."""

import logging
from typing import List, Optional, Tuple

from analyzers.base import BaseAnalyzer
from core.issue_model import CategoryEnum, Issue, SeverityEnum

logger = logging.getLogger(__name__)

try:
    import pycodestyle
    PYCODESTYLE_AVAILABLE = True
except ImportError:
    PYCODESTYLE_AVAILABLE = False
    logger.warning("pycodestyle library is not available.")


if PYCODESTYLE_AVAILABLE:
    class _CustomReport(pycodestyle.BaseReport):
        """In-memory Pycodestyle report collector."""

        def __init__(self, options) -> None:
            super().__init__(options)
            self.errors: List[Tuple[int, int, str, str]] = []

        def error(
            self, line_number: int, offset: int, text: str, check
        ) -> Optional[str]:
            code = super().error(line_number, offset, text, check)
            if code:
                self.errors.append((line_number, offset, code, text))
            return code


def _map_style_category(code_id: str) -> CategoryEnum:
    if code_id.startswith("E9"):
        return CategoryEnum.SYNTAX_ERROR
    if code_id.startswith(("E4", "E7", "W6")):
        return CategoryEnum.BEST_PRACTICE
    return CategoryEnum.READABILITY


def _map_style_why_it_matters(code_id: str) -> str:
    if code_id == "E501":
        return (
            "Lines exceeding 79 characters reduce readability on standard "
            "displays and create noisy side-by-side code diffs."
        )
    if code_id.startswith(("W291", "W293", "W391")):
        return (
            "Trailing whitespace and unnecessary blank lines add noise to "
            "version control diffs and cause inconsistent formatting."
        )
    if code_id.startswith("E1"):
        return (
            "Inconsistent indentation obscures code structure and can lead to "
            "subtle scoping or syntax errors."
        )
    if code_id in ("E711", "E712", "E721"):
        return (
            "Comparing singletons (such as None or Booleans) with '==' "
            "instead of 'is' can trigger custom __eq__ logic and bugs."
        )
    return (
        "Adhering to PEP 8 style standards ensures consistent, clean Python "
        "code that is easy for engineering teams to read and maintain."
    )


class StyleAnalyzer(BaseAnalyzer):
    """Static style analyzer running pycodestyle in-memory."""

    @property
    def name(self) -> str:
        return "pycodestyle"

    def analyze(
        self, code: str, filename: str = "submitted_snippet"
    ) -> List[Issue]:
        """Runs PEP 8 style validation against submitted source code."""
        if not PYCODESTYLE_AVAILABLE or not code or not code.strip():
            return []

        lines = code.splitlines(keepends=True)
        if lines and not lines[-1].endswith("\n"):
            lines[-1] = lines[-1] + "\n"

        issues: List[Issue] = []
        try:
            style_guide = pycodestyle.StyleGuide(reporter=_CustomReport)
            report = style_guide.options.report

            checker = pycodestyle.Checker(
                filename=filename,
                lines=lines,
                options=style_guide.options,
                report=report,
            )
            checker.check_all()

            for line_number, offset, code_id, text in report.errors:
                category = _map_style_category(code_id)
                why_it_matters = _map_style_why_it_matters(code_id)

                if code_id.startswith("E9"):
                    severity = SeverityEnum.CRITICAL
                elif code_id in ("E711", "E712", "E721", "E722"):
                    severity = SeverityEnum.LOW
                else:
                    severity = SeverityEnum.INFORMATIONAL

                issues.append(
                    self.build_issue(
                        category=category,
                        description=text,
                        why_it_matters=why_it_matters,
                        code=code,
                        line_start=max(1, line_number),
                        line_end=max(1, line_number),
                        column=offset,
                        severity=severity,
                        confidence=1.0,
                        file=filename,
                        references=["PEP 8", code_id],
                    )
                )
        except Exception as e:
            logger.error(
                f"Pycodestyle error for {filename}: {e}", exc_info=True
            )

        return issues
