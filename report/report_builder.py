"""ReportBuilder implementing ReportBuilderProtocol."""

from core.interfaces import ReportBuilderProtocol
from core.issue_model import ReviewResult
from report.json_report import JSONReportExporter
from report.markdown_report import MarkdownReportExporter
from report.pdf_report import PDFReportExporter


class ReportBuilder(ReportBuilderProtocol):
    """Assembles ReviewResult into structured reports across Markdown, JSON, and PDF formats."""

    def __init__(self, default_format: str = "markdown"):
        self.default_format = default_format.lower()
        self.markdown_exporter = MarkdownReportExporter()
        self.json_exporter = JSONReportExporter()
        self.pdf_exporter = PDFReportExporter()

    def build(self, result: ReviewResult, format_type: str = "markdown") -> str:
        """Assembles and formats a ReviewResult into a structured report string."""
        fmt = (format_type or self.default_format).lower()

        if fmt == "json":
            return self.json_exporter.export(result)
        elif fmt in ("pdf", "application/pdf"):
            return self.pdf_exporter.export(result)
        else:
            return self.markdown_exporter.export(result)
