"""Production Streamlit UI component library for AI Code Review Assistant."""

import json
from typing import List, Optional, Tuple
import streamlit as st

from core.issue_model import CategoryEnum, CodeQualityScore, Issue, ReviewResult, ReviewSummary, SeverityEnum
from report import JSONReportExporter, MarkdownReportExporter, PDFReportExporter

SEVERITY_ICONS = {
    SeverityEnum.CRITICAL: "🔴",
    SeverityEnum.HIGH: "🟠",
    SeverityEnum.MEDIUM: "🟡",
    SeverityEnum.LOW: "🔵",
    SeverityEnum.INFORMATIONAL: "⚪",
}


def render_header() -> None:
    """Renders the main page title header and status description."""
    st.title("🛡️ AI Code Review Assistant")
    st.caption("⚡ **Production Review Engine** | Multi-Layer Static Analysis & AI Reasoning")


def render_sidebar_controls() -> Tuple[bool, Optional[str]]:
    """Renders sidebar controls: AI mode toggle, OpenAI status badge, and manual language override.

    Returns:
        (enable_ai, manual_override)
    """
    st.sidebar.header("⚙️ Review Settings")

    enable_ai = st.sidebar.toggle("🤖 Enable AI Reasoning", value=True, help="Enable OpenAI LLM reasoning chain for logic flaws and edge cases.")

    # OpenAI Connection Status Badge
    import os
    from services.config_service import get_settings
    settings = get_settings()
    api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")
    has_valid_key = bool(api_key and api_key.strip() and not api_key.startswith("your_"))

    if enable_ai:
        if has_valid_key:
            st.sidebar.success("🟢 OpenAI Connected")
        else:
            st.sidebar.warning("⚠️ OpenAI Key Missing (Static Fallback Active)")
    else:
        st.sidebar.info("🔵 Static-Only Mode Active")

    st.sidebar.markdown("---")
    language_override = st.sidebar.selectbox(
        "🔤 Manual Language Override",
        options=["Auto-Detect", "Python", "Unknown"],
        index=0,
    )
    manual_lang = None if language_override == "Auto-Detect" else language_override.lower()

    return enable_ai, manual_lang


def render_score_dashboard(score: CodeQualityScore) -> None:
    """Renders overall quality score gauge and 7-dimension score grid."""
    st.subheader("🏆 Code Quality Score Dashboard")

    score_color = "green" if score.overall_score >= 85 else ("orange" if score.overall_score >= 60 else "red")
    st.markdown(
        f"### Overall Rating: <span style='color:{score_color}; font-size:2rem; font-weight:bold;'>{score.overall_score}/100</span> (`{score.label}`)",
        unsafe_allow_html=True,
    )
    st.info(f"📝 **Summary**: {score.summary_notes}")

    st.markdown("#### 7 Quality Dimensions Breakdown (PRD Weighted Model)")
    cols = st.columns(len(score.dimensions)) if score.dimensions else [st]
    
    for idx, dim in enumerate(score.dimensions):
        col = cols[idx % len(cols)]
        with col:
            d_color = "green" if dim.score >= 85 else ("orange" if dim.score >= 60 else "red")
            st.metric(
                label=dim.dimension_name,
                value=f"{dim.score}/100",
                delta=f"-{dim.deductions} pts" if dim.deductions > 0 else "Clean",
                delta_color="inverse" if dim.deductions > 0 else "normal",
            )
            st.caption(f"Weight: {int(dim.weight*100)}% | Issues: {dim.issue_count}")


def render_summary_metrics(summary: ReviewSummary) -> None:
    """Renders high-level review statistics and severity counters."""
    st.subheader("📊 Severity Counter Summary")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Total Issues", summary.total_issues)
    with c2:
        st.metric("🔴 Critical", summary.critical_count)
    with c3:
        st.metric("🟠 High", summary.high_count)
    with c4:
        st.metric("🟡 Medium", summary.medium_count)
    with c5:
        st.metric("🔵 Low", summary.low_count)
    with c6:
        st.metric("⚪ Info", summary.informational_count)


def render_issue_card(issue: Issue, index: int = 1) -> None:
    """Renders an individual structured Issue card in an expandable container."""
    icon = SEVERITY_ICONS.get(issue.severity, "🔍")
    severity_str = issue.severity.value.upper()
    category_str = issue.category.value.replace("_", " ").title()

    expander_title = (
        f"{icon} #{index} [{severity_str}] {category_str}: {issue.description[:80]} "
        f"(Line {issue.line_start})"
    )

    with st.expander(expander_title, expanded=(issue.severity in (SeverityEnum.CRITICAL, SeverityEnum.HIGH))):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"**Severity**: `{severity_str}`")
        with c2:
            st.markdown(f"**Category**: `{category_str}`")
        with c3:
            line_txt = f"Line {issue.line_start}" if issue.line_start == issue.line_end else f"Lines {issue.line_start}–{issue.line_end}"
            st.markdown(f"**Location**: `{line_txt}`")
        with c4:
            st.markdown(f"**Source**: `{issue.detection_source.value}` ({issue.detecting_tool or 'engine'})")

        st.markdown(f"**Description**: {issue.description}")

        if issue.code_snippet and issue.code_snippet.strip():
            st.markdown("**Code Excerpt**:")
            st.code(issue.code_snippet, language="python")

        if issue.why_it_matters:
            st.markdown(f"💡 **Why it matters**: {issue.why_it_matters}")

        # Fix display
        if issue.fix:
            st.markdown("🛠️ **Suggested Remediation**:")
            st.info(issue.fix.suggested_fix)
            if issue.fix.diff and issue.fix.diff.strip():
                st.markdown("**Unified Diff**:")
                st.code(issue.fix.diff, language="diff")

        # Test case display
        if issue.generated_test:
            st.markdown("🧪 **Generated Pytest Case**:")
            st.code(issue.generated_test.test_code, language="python")


def render_export_section(review_result: ReviewResult) -> None:
    """Renders report export buttons for Markdown, JSON, and PDF download."""
    st.sidebar.markdown("---")
    st.sidebar.header("📥 Export Report")

    md_exporter = MarkdownReportExporter()
    json_exporter = JSONReportExporter()
    pdf_exporter = PDFReportExporter()

    md_content = md_exporter.export(review_result)
    json_content = json_exporter.export(review_result)
    pdf_content = pdf_exporter.export(review_result)

    st.sidebar.download_button(
        label="📄 Download Markdown Report",
        data=md_content,
        file_name="code_review_report.md",
        mime="text/markdown",
    )

    st.sidebar.download_button(
        label="📊 Download JSON Payload",
        data=json_content,
        file_name="code_review_report.json",
        mime="application/json",
    )

    st.sidebar.download_button(
        label="📕 Export PDF Report",
        data=pdf_content,
        file_name="code_review_report.pdf",
        mime="application/pdf" if pdf_content.startswith("%PDF") else "text/plain",
    )
