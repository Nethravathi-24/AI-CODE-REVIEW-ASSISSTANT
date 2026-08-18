"""Streamlit UI rendering components for AI Code Review Assistant."""

from typing import List
import streamlit as st

from core.issue_model import Issue, ReviewResult, SeverityEnum

SEVERITY_COLORS = {
    SeverityEnum.CRITICAL: "🔴 Critical",
    SeverityEnum.HIGH: "🟠 High",
    SeverityEnum.MEDIUM: "🟡 Medium",
    SeverityEnum.LOW: "🔵 Low",
    SeverityEnum.INFORMATIONAL: "⚪ Informational",
}


def render_dashboard_header(result: ReviewResult) -> None:
    """Renders the executive summary and metrics header cards."""
    st.title("🛡️ AI Code Review Assistant")
    st.caption("Milestone 2 Static Analysis & Quality Dashboard")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Overall Score",
            f"{result.score.overall_score:.0f}/100",
            result.score.label,
        )
    with col2:
        st.metric("Total Issues", result.summary.total_issues)
    with col3:
        high_crit = (
            result.summary.critical_count + result.summary.high_count
        )
        st.metric("Critical / High", high_crit)
    with col4:
        st.metric("Language", result.language.title())

    if result.summary.executive_summary:
        st.info(result.summary.executive_summary)


def render_issue_card(issue: Issue, index: int) -> None:
    """Renders an individual collapsible issue card."""
    sev_label = SEVERITY_COLORS.get(
        issue.severity, str(issue.severity.value).title()
    )
    cat_label = issue.category.value.replace("_", " ").title()
    expander_title = (
        f"#{index + 1} [{sev_label}] Line {issue.line_start}: "
        f"{cat_label} — {issue.description[:60]}"
    )

    is_expanded = issue.severity in (
        SeverityEnum.CRITICAL, SeverityEnum.HIGH
    )
    with st.expander(expander_title, expanded=is_expanded):
        st.markdown(f"**Description:** {issue.description}")
        st.markdown(f"**Why It Matters:** {issue.why_it_matters}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Tool:** `{issue.detecting_tool or 'static'}`")
        with col2:
            st.markdown(f"**Confidence:** `{issue.confidence * 100:.0f}%`")
        with col3:
            st.markdown(
                f"**Line Range:** `{issue.line_start} - {issue.line_end}`"
            )

        if issue.code_snippet:
            st.markdown("**Code Snippet:**")
            st.code(issue.code_snippet, language="python")


def render_issues_list(issues: List[Issue]) -> None:
    """Renders the list of discovered issues."""
    if not issues:
        st.success("🎉 No static analysis issues discovered! Code is clean.")
        return

    st.subheader(f"Discovered Issues ({len(issues)})")

    for i, issue in enumerate(issues):
        render_issue_card(issue, i)


def render_review_dashboard(result: ReviewResult) -> None:
    """Renders the complete ReviewResult dashboard in Streamlit."""
    render_dashboard_header(result)
    render_issues_list(result.issues)
