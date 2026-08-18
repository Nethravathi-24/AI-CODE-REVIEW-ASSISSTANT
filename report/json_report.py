"""JSON Report Exporter conforming to ReportExporterProtocol."""

import json
from core.interfaces import ReportExporterProtocol
from core.issue_model import ReviewResult


class JSONReportExporter(ReportExporterProtocol):
    """Serializes ReviewResult payload into structured JSON string."""

    def export(self, result: ReviewResult) -> str:
        """Exports ReviewResult as pretty-printed JSON string."""
        if not result:
            return "{}"
        return result.model_dump_json(indent=2)
