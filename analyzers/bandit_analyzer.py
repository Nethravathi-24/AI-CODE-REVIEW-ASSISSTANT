"""Bandit security scanner wrapper detecting hardcoded secrets, eval/exec, and unsafe calls."""

import ast
import io
import logging
from typing import List

from bandit.core import config, manager

from analyzers.base import BaseAnalyzer
from core.issue_model import (
    CategoryEnum,
    DetectionSourceEnum,
    Issue,
    SeverityEnum,
)

logger = logging.getLogger(__name__)

# Suppress noisy bandit qualified name logger
logging.getLogger("bandit.core.node_visitor").setLevel(logging.ERROR)


class BanditAnalyzer(BaseAnalyzer):
    """Programmatic Bandit security analyzer mapping security checks to Issue models."""

    def __init__(self) -> None:
        self._config = config.BanditConfig()

    @property
    def name(self) -> str:
        return "bandit"

    def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
        """Runs Bandit security analysis in-memory on submitted source code."""
        issues: List[Issue] = []

        try:
            tree = ast.parse(code, filename=filename)
        except (SyntaxError, IndentationError):
            # Syntax errors are handled by ASTAnalyzer; Bandit gracefully exits
            return issues

        try:
            b_mgr = manager.BanditManager(self._config, "file")
            fdata = io.BytesIO(code.encode("utf-8"))
            b_mgr._execute_ast_visitor(filename, fdata, tree, {})
        except Exception as e:
            logger.warning("Bandit analysis execution warning: %s", str(e))
            return issues

        for b_issue in b_mgr.results:
            line_no = getattr(b_issue, "lineno", 1)
            line_range = getattr(b_issue, "linerange", [line_no])
            line_end = line_range[-1] if line_range else line_no
            if line_end < line_no:
                line_end = line_no

            snippet = self._get_code_snippet(code, line_no, line_end)
            test_id = getattr(b_issue, "test_id", "B000")
            b_severity = getattr(b_issue, "severity", "MEDIUM").upper()
            b_confidence = getattr(b_issue, "confidence", "HIGH").upper()

            # Map Bandit severity & confidence
            if b_severity == "HIGH":
                severity = SeverityEnum.HIGH
            elif b_severity == "MEDIUM":
                severity = SeverityEnum.HIGH if test_id in ("B307", "B102") else SeverityEnum.MEDIUM
            else:
                severity = SeverityEnum.MEDIUM if test_id in ("B105", "B106", "B107") else SeverityEnum.LOW

            conf_score = 0.95 if b_confidence == "HIGH" else (0.80 if b_confidence == "MEDIUM" else 0.60)

            # References
            refs = [test_id]
            cwe_obj = getattr(b_issue, "cwe", None)
            if cwe_obj and hasattr(cwe_obj, "id"):
                refs.append(f"CWE-{cwe_obj.id}")
            elif cwe_obj and str(cwe_obj).startswith("CWE-"):
                refs.append(str(cwe_obj).split()[0])

            description = f"[{test_id}] {b_issue.text}"

            issues.append(
                Issue(
                    issue_id=self._generate_issue_id("bandit", test_id, line_no),
                    category=CategoryEnum.SECURITY,
                    severity=severity,
                    confidence=conf_score,
                    file=filename,
                    line_start=line_no,
                    line_end=line_end,
                    column=getattr(b_issue, "col_offset", None),
                    code_snippet=snippet,
                    description=description,
                    why_it_matters=(
                        "Security vulnerabilities in source code can allow unauthorized data access, "
                        "remote code execution, or credential theft."
                    ),
                    root_cause=f"Bandit rule {test_id} triggered on unsafe pattern.",
                    detection_source=DetectionSourceEnum.STATIC,
                    detecting_tool="bandit",
                    references=refs,
                )
            )

        return issues
