"""Unit tests for reporting engine and Markdown/JSON/PDF exporters."""

import json
import pytest
from core.issue_model import CategoryEnum, CodeQualityScore, DetectionSourceEnum, DimensionScore, Issue, ReviewResult, ReviewSummary, SeverityEnum
from report import JSONReportExporter, MarkdownReportExporter, PDFReportExporter, ReportBuilder


@pytest.fixture
def sample_review_result():
    score = CodeQualityScore(
        overall_score=88.5,
        label="Good",
        dimensions=[
            DimensionScore(dimension_name="Correctness", score=90.0, weight=0.25, deductions=10.0, issue_count=1),
            DimensionScore(dimension_name="Security", score=85.0, weight=0.25, deductions=15.0, issue_count=1),
        ],
        summary_notes="Good code with minor findings",
    )
    summary = ReviewSummary(
        total_issues=2,
        high_count=1,
        medium_count=1,
        executive_summary="2 issues detected during review",
    )
    issues = [
        Issue(
            issue_id="issue-1",
            category=CategoryEnum.SECURITY,
            severity=SeverityEnum.HIGH,
            confidence=0.9,
            line_start=10,
            line_end=10,
            code_snippet="eval(user_input)",
            description="Arbitrary code execution",
            why_it_matters="Critical security vulnerability",
            detection_source=DetectionSourceEnum.STATIC,
        )
    ]
    return ReviewResult(
        score=score,
        summary=summary,
        issues=issues,
        language="python",
        submitted_code="eval(user_input)",
    )


def test_json_report_exporter(sample_review_result):
    """Test 1: JSONReportExporter produces valid parseable JSON string."""
    exporter = JSONReportExporter()
    out = exporter.export(sample_review_result)
    parsed = json.loads(out)
    assert parsed["language"] == "python"
    assert parsed["score"]["overall_score"] == 88.5


def test_markdown_report_exporter(sample_review_result):
    """Test 2: MarkdownReportExporter produces structured markdown containing scores and findings."""
    exporter = MarkdownReportExporter()
    out = exporter.export(sample_review_result)
    assert "# 🛡️ AI Code Review Assistant" in out
    assert "88.5/100" in out
    assert "Arbitrary code execution" in out


def test_report_builder_integration(sample_review_result):
    """Test 3: ReportBuilder delegates correctly to Markdown and JSON exporters."""
    builder = ReportBuilder()
    md_out = builder.build(sample_review_result, format_type="markdown")
    assert "Executive Report" in md_out

    json_out = builder.build(sample_review_result, format_type="json")
    assert '"language": "python"' in json_out
