"""Radon static complexity and maintainability metrics analyzer."""

import logging
from typing import List

from analyzers.base import BaseAnalyzer
from core.issue_model import CategoryEnum, Issue, SeverityEnum

logger = logging.getLogger(__name__)

try:
    import radon.complexity as cc
    import radon.metrics as metrics
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False
    logger.warning("radon library is not available.")


class RadonAnalyzer(BaseAnalyzer):
    """Static analyzer computing CC and Maintainability Index via Radon."""

    @property
    def name(self) -> str:
        return "radon"

    def analyze(
        self, code: str, filename: str = "submitted_snippet"
    ) -> List[Issue]:
        """Analyzes code complexity and metrics in-memory."""
        if not RADON_AVAILABLE or not code or not code.strip():
            return []

        issues: List[Issue] = []

        # 1. Cyclomatic Complexity Analysis
        try:
            blocks = cc.cc_visit(code)
            for block in blocks:
                if block.complexity > 10:
                    if block.complexity > 30:
                        severity = SeverityEnum.HIGH
                    elif block.complexity > 20:
                        severity = SeverityEnum.MEDIUM
                    else:
                        severity = SeverityEnum.LOW

                    line_start = max(1, block.lineno)
                    end_val = getattr(block, "endline", line_start)
                    line_end = max(line_start, end_val or line_start)
                    block_type = getattr(block, "letter", "F")
                    type_label = (
                        "Function"
                        if block_type == "F"
                        else ("Class" if block_type == "C" else "Method")
                    )

                    rank_letter = getattr(block, "letter", "C")
                    description = (
                        f"{type_label} '{block.name}' has high cyclomatic "
                        f"complexity ({block.complexity}, Rank {rank_letter})"
                    )
                    why_it_matters = (
                        "High cyclomatic complexity indicates deeply "
                        "branched, difficult-to-test code. High complexity "
                        "correlates with elevated defect rates and higher "
                        "refactoring costs."
                    )

                    issues.append(
                        self.build_issue(
                            category=CategoryEnum.MAINTAINABILITY,
                            description=description,
                            why_it_matters=why_it_matters,
                            code=code,
                            line_start=line_start,
                            line_end=line_end,
                            severity=severity,
                            confidence=1.0,
                            file=filename,
                            references=["radon", f"CC-{block.complexity}"],
                        )
                    )
        except SyntaxError:
            # Handled by ASTAnalyzer
            pass
        except Exception as e:
            logger.error(
                f"Radon complexity error for {filename}: {e}", exc_info=True
            )

        # 2. Maintainability Index Analysis
        try:
            total_lines = len(code.splitlines())
            if total_lines >= 15:
                mi_score = metrics.mi_visit(code, multi=True)
                if mi_score < 20.0:
                    severity = (
                        SeverityEnum.MEDIUM
                        if mi_score >= 10.0
                        else SeverityEnum.HIGH
                    )
                    issues.append(
                        self.build_issue(
                            category=CategoryEnum.MAINTAINABILITY,
                            description=(
                                f"File has poor Maintainability Index "
                                f"({mi_score:.1f}/100)"
                            ),
                            why_it_matters=(
                                "A low Maintainability Index indicates code "
                                "with high complexity or low comment density, "
                                "which hinders maintainability."
                            ),
                            code=code,
                            line_start=1,
                            line_end=total_lines,
                            severity=severity,
                            confidence=0.9,
                            file=filename,
                            references=["radon", "MI"],
                        )
                    )
        except Exception as e:
            logger.error(
                f"Radon MI error for {filename}: {e}", exc_info=True
            )

        return issues
