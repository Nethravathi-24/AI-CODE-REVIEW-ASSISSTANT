"""UI components and presentation helpers for Streamlit interface."""

from typing import List, Optional
import streamlit as st

from core.issue_model import (
    CodeQualityScore,
    Issue,
    ReviewSummary,
    SeverityEnum,
)

SEVERITY_ICONS = {
    SeverityEnum.CRITICAL: "🔴",
    SeverityEnum.HIGH: "🟠",
    SeverityEnum.MEDIUM: "🟡",
    SeverityEnum.LOW: "🔵",
    SeverityEnum.INFORMATIONAL: "⚪",
}


def render_header() -> None:
    """Renders the top application header and MVP disclaimer banner."""
    st.title("🛡️ AI Code Review Assistant")
    st.caption("🚀 **Milestone 2 — Static-Analysis MVP** | Python Engine")
    st.info(
        "ℹ️ **Static Analysis Mode**: Deterministic checks active (AST Structural Analysis, Pyflakes, "
        "Bandit Security Scanner, Radon Complexity, Pycodestyle PEP 8). *AI Reasoning and LLM chains are inactive in this phase.*"
    )


def render_summary_metrics(summary: ReviewSummary, score: Optional[CodeQualityScore] = None) -> None:
    """Renders high-level review statistics and severity counters."""
    st.subheader("📊 Review Summary")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Total Issues", summary.total_issues)
    with col2:
        st.metric("🔴 Critical", summary.critical_count)
    with col3:
        st.metric("🟠 High", summary.high_count)
    with col4:
        st.metric("🟡 Medium", summary.medium_count)
    with col5:
        st.metric("🔵 Low", summary.low_count)
    with col6:
        st.metric("⚪ Info", summary.informational_count)

    if score is not None:
        score_color = "green" if score.overall_score >= 80 else ("orange" if score.overall_score >= 50 else "red")
        st.markdown(
            f"**Overall Quality Score**: <span style='font-size:1.3rem; font-weight:bold; color:{score_color};'>"
            f"{score.overall_score}/100 ({score.label})</span> — *{score.summary_notes}*",
            unsafe_allow_html=True,
        )


def render_no_issues_card() -> None:
    """Renders celebratory card when 0 static issues are found."""
    st.success(
        "🎉 **No issues detected!** The submitted Python code passed all deterministic static analysis checks "
        "(AST, Pyflakes, Bandit Security, Radon Complexity, and PEP 8 style)."
    )


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
            st.markdown(f"**Detector**: `{issue.detecting_tool or issue.detection_source.value}`")

        st.markdown(f"**Description**: {issue.description}")

        if issue.code_snippet and issue.code_snippet.strip():
            st.markdown("**Code Snippet**:")
            st.code(issue.code_snippet, language="python")

        if issue.why_it_matters:
            st.markdown(f"💡 **Why it matters**: {issue.why_it_matters}")

        if issue.root_cause:
            st.markdown(f"🔍 **Root Cause**: `{issue.root_cause}`")

        if issue.references:
            refs_str = " • ".join([f"`{ref}`" for ref in issue.references])
            st.markdown(f"📚 **References / Rule IDs**: {refs_str}")
