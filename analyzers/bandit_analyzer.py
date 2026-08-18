"""Bandit static security analyzer wrapper for scanning vulnerabilities."""

import io
import logging
import tokenize
from typing import Dict, List

from analyzers.base import BaseAnalyzer
from core.issue_model import CategoryEnum, Issue, SeverityEnum

logger = logging.getLogger(__name__)

try:
    import bandit.core.config
    import bandit.core.manager
    import bandit.core.meta_ast
    import bandit.core.metrics
    import bandit.core.node_visitor
    import bandit.core.test_set
    BANDIT_AVAILABLE = True
except ImportError:
    BANDIT_AVAILABLE = False
    logger.warning("bandit library is not available.")

# Map Bandit string severities to domain SeverityEnum
BANDIT_SEVERITY_MAP: Dict[str, SeverityEnum] = {
    "HIGH": SeverityEnum.HIGH,
    "MEDIUM": SeverityEnum.MEDIUM,
    "LOW": SeverityEnum.LOW,
    "UNDEFINED": SeverityEnum.LOW,
}

# Map Bandit string confidence to float score
BANDIT_CONFIDENCE_MAP: Dict[str, float] = {
    "HIGH": 0.95,
    "MEDIUM": 0.75,
    "LOW": 0.50,
    "UNDEFINED": 0.50,
}


class BanditAnalyzer(BaseAnalyzer):
    """Static security analyzer wrapping Bandit programmatically."""

    def __init__(self) -> None:
        super().__init__()
        self._config = None
        self._test_set = None
        if BANDIT_AVAILABLE:
            try:
                self._config = bandit.core.config.BanditConfig()
                self._test_set = bandit.core.test_set.BanditTestSet(
                    self._config, profile={}
                )
            except Exception as e:
                logger.error(
                    f"Failed to initialize Bandit test set: {e}",
                    exc_info=True,
                )

    @property
    def name(self) -> str:
        return "bandit"

    def analyze(
        self, code: str, filename: str = "submitted_snippet"
    ) -> List[Issue]:
        """Runs Bandit security scanning in-memory without subprocesses."""
        if (
            not BANDIT_AVAILABLE
            or self._test_set is None
            or not code
            or not code.strip()
        ):
            return []

        fname = filename or "submitted_snippet.py"
        encoded = code.encode("utf-8")
        fdata = io.BytesIO(encoded)
        data = fdata.read()

        # Parse nosec comments if present
        nosec_lines = dict()
        fdata.seek(0)
        try:
            tokens = tokenize.tokenize(fdata.readline)
            for toktype, tokval, (lineno, _), _, _ in tokens:
                if toktype == tokenize.COMMENT:
                    nosec_lines[lineno] = (
                        bandit.core.manager._parse_nosec_comment(tokval)
                    )
        except Exception:
            pass

        fdata.seek(0)
        metaast = bandit.core.meta_ast.BanditMetaAst()
        metrics = bandit.core.metrics.Metrics()

        try:
            visitor = bandit.core.node_visitor.BanditNodeVisitor(
                fname,
                fdata,
                metaast,
                self._test_set,
                False,  # debug
                nosec_lines,
                metrics,
            )
            visitor.process(data)
        except SyntaxError:
            # Handled by ASTAnalyzer
            return []
        except Exception as e:
            logger.error(
                f"Bandit scan error for {filename}: {e}", exc_info=True
            )
            return []

        issues: List[Issue] = []
        for result in visitor.tester.results:
            sev_str = str(getattr(result, "severity", "MEDIUM")).upper()
            conf_str = str(getattr(result, "confidence", "HIGH")).upper()

            severity = BANDIT_SEVERITY_MAP.get(sev_str, SeverityEnum.HIGH)
            confidence = BANDIT_CONFIDENCE_MAP.get(conf_str, 0.85)

            lineno = max(1, getattr(result, "lineno", 1))
            linerange = getattr(result, "linerange", None)
            if linerange and len(linerange) > 0:
                line_start = max(1, linerange[0])
                line_end = max(line_start, linerange[-1])
            else:
                line_start = lineno
                line_end = lineno

            test_id = getattr(result, "test_id", "SECURITY_ISSUE")
            text = getattr(
                result, "text", "Potential security vulnerability detected."
            )

            refs = [test_id]
            cwe = getattr(result, "cwe", None)
            if cwe:
                cwe_id = getattr(cwe, "id", None)
                if cwe_id:
                    refs.append(f"CWE-{cwe_id}")
                else:
                    refs.append(str(cwe).split()[0])

            why_it_matters = (
                f"Security vulnerability detected by Bandit ({test_id}). "
                "Insecure code constructs can lead to arbitrary code "
                "execution, sensitive data disclosure, or injection attacks."
            )

            issues.append(
                self.build_issue(
                    category=CategoryEnum.SECURITY,
                    description=text,
                    why_it_matters=why_it_matters,
                    code=code,
                    line_start=line_start,
                    line_end=line_end,
                    severity=severity,
                    confidence=confidence,
                    file=filename,
                    references=refs,
                )
            )

        return issues
