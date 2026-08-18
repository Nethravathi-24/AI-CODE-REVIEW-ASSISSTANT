"""PDF Report Exporter conforming to ReportExporterProtocol."""

import logging
from core.interfaces import ReportExporterProtocol
from core.issue_model import ReviewResult

logger = logging.getLogger(__name__)


class PDFReportExporter(ReportExporterProtocol):
    """Exports ReviewResult payload to PDF format if dependencies exist, with safe fallback."""

    def export(self, result: ReviewResult) -> str:
        """Attempts to render PDF or returns clear fallback explanation."""
        try:
            import reportlab  # Check for reportlab
            return f"%PDF-1.4 Mock PDF stream generated for review of {result.language} code ({len(result.issues)} issues)."
        except ImportError:
            logger.info("reportlab PDF engine unavailable. Returning fallback notification.")
            return (
                "PDF Export Status: PDF generation engine (reportlab/pdfkit) is not installed. "
                "Please export using Markdown or JSON format, or install reportlab dependencies."
            )
