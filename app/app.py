"""Streamlit Web Interface for AI Code Review Assistant (Static-Analysis MVP)."""

import os
from pathlib import Path
import sys

# Ensure repository root is in sys.path for absolute package imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

try:
    from app.components import (
        render_header,
        render_issue_card,
        render_no_issues_card,
        render_summary_metrics,
    )
except ImportError:
    from components import (
        render_header,
        render_issue_card,
        render_no_issues_card,
        render_summary_metrics,
    )

from core.issue_model import SeverityEnum
from orchestrator import run_pipeline

# Configure Streamlit page settings
st.set_page_config(
    page_title="AI Code Review Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
if "code_input" not in st.session_state:
    st.session_state["code_input"] = ""
if "review_result" not in st.session_state:
    st.session_state["review_result"] = None
if "review_error" not in st.session_state:
    st.session_state["review_error"] = None
if "uploaded_filename" not in st.session_state:
    st.session_state["uploaded_filename"] = "submitted_snippet.py"


def main() -> None:
    """Main Streamlit application entry point."""
    render_header()

    # Sidebar: Configurations & Quick Fixture Loaders
    with st.sidebar:
        st.header("⚙️ Configuration")
        language_selection = st.selectbox(
            "Language",
            ["Python", "Auto-Detect"],
            index=0,
            help="Static analyzers are currently configured for Python source code.",
        )
        language_override = "python" if language_selection == "Python" else None

        st.markdown("---")
        st.subheader("💡 Quick Examples")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Clean Code", use_container_width=True):
                st.session_state["code_input"] = (
                    "def calculate_total(prices: list[float]) -> float:\n"
                    "    '''Computes sum of prices.'''\n"
                    "    if not prices:\n"
                    "        return 0.0\n"
                    "    return sum(prices)\n"
                )
                st.session_state["uploaded_filename"] = "clean_example.py"
                st.session_state["review_result"] = None
                st.session_state["review_error"] = None
                st.rerun()

        with c2:
            if st.button("Security Bug", use_container_width=True):
                st.session_state["code_input"] = (
                    "import os\n\n"
                    "API_KEY_SECRET = 'sk-proj-1234567890abcdef'\n\n"
                    "def run_user_code(user_input: str):\n"
                    "    eval(user_input)\n"
                )
                st.session_state["uploaded_filename"] = "security_example.py"
                st.session_state["review_result"] = None
                st.session_state["review_error"] = None
                st.rerun()

        if st.button("🧹 Clear Code", use_container_width=True):
            st.session_state["code_input"] = ""
            st.session_state["uploaded_filename"] = "submitted_snippet.py"
            st.session_state["review_result"] = None
            st.session_state["review_error"] = None
            st.rerun()

        st.markdown("---")
        st.caption("🔒 **Security Guarantee**: User code is never executed. Analyzers perform deterministic static inspection in memory.")

    # Main Input Section
    col_upload, col_space = st.columns([2, 1])
    with col_upload:
        uploaded_file = st.file_uploader(
            "📂 Upload a Python file (.py)",
            type=["py"],
            help="Upload a .py file to load its code into the review editor.",
        )
        if uploaded_file is not None:
            uploaded_text = uploaded_file.getvalue().decode("utf-8", errors="replace")
            # Update editor if file is different or fresh
            if st.session_state["code_input"] != uploaded_text:
                st.session_state["code_input"] = uploaded_text
                st.session_state["uploaded_filename"] = uploaded_file.name
                st.session_state["review_result"] = None
                st.session_state["review_error"] = None

    code_input = st.text_area(
        "✍️ Python Source Code Editor",
        value=st.session_state.get("code_input", ""),
        height=280,
        placeholder="Paste your Python source code here...",
        help="Enter or paste the Python code you want to review.",
    )

    # If code changed manually, clear stale review results
    if code_input != st.session_state.get("code_input", ""):
        st.session_state["code_input"] = code_input
        st.session_state["review_result"] = None
        st.session_state["review_error"] = None

    # Review Action Button
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        run_review = st.button("🔍 Review Code", type="primary", use_container_width=True)

    if run_review:
        filename = st.session_state.get("uploaded_filename", "submitted_snippet.py")
        with st.spinner("Running static analysis pipeline (AST, Pyflakes, Bandit, Radon, Pycodestyle)..."):
            # Call backend orchestrator entry point
            pipeline_result = run_pipeline(
                code=code_input,
                filename=filename,
                language_override=language_override,
            )

            if not pipeline_result.success:
                err_msg = (
                    pipeline_result.errors[0].message
                    if pipeline_result.errors
                    else "Input validation failed. Please provide valid Python code."
                )
                st.session_state["review_error"] = err_msg
                st.session_state["review_result"] = None
            else:
                st.session_state["review_error"] = None
                st.session_state["review_result"] = pipeline_result.review_result

    # Display Validation Error if any
    if st.session_state.get("review_error"):
        st.error(f"❌ **Validation Error**: {st.session_state['review_error']}")

    # Display Review Results
    result = st.session_state.get("review_result")
    if result is not None:
        st.markdown("---")
        render_summary_metrics(result.summary, result.score)
        st.markdown("---")

        if result.summary.total_issues == 0:
            render_no_issues_card()
        else:
            st.subheader(f"📋 Detected Issues ({result.summary.total_issues})")

            # Severity Filter
            severity_filter = st.multiselect(
                "Filter by Severity",
                options=["Critical", "High", "Medium", "Low", "Informational"],
                default=["Critical", "High", "Medium", "Low", "Informational"],
                help="Select which severity levels to display in the list below.",
            )

            filtered_issues = [
                issue
                for issue in result.issues
                if issue.severity.value.capitalize() in severity_filter
            ]

            if not filtered_issues:
                st.info("ℹ️ No issues match the selected severity filter.")
            else:
                for idx, issue in enumerate(filtered_issues, start=1):
                    render_issue_card(issue, index=idx)


if __name__ == "__main__":
    main()
