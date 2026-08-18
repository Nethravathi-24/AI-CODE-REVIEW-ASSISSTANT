"""Primary Streamlit web application entry point for AI Code Review Assistant."""

from pathlib import Path
import sys
import streamlit as st

# Ensure repository root directory is in sys.path for absolute imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai import get_ai_reviewer
from app.ui.components import (
    render_export_section,
    render_header,
    render_issue_card,
    render_sidebar_controls,
    render_score_dashboard,
    render_summary_metrics,
)
from core.issue_model import CategoryEnum, SeverityEnum
from orchestrator import CodeReviewPipeline


def main() -> None:
    """Main Streamlit application layout and execution controller."""
    st.set_page_config(
        page_title="AI Code Review Assistant",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    render_header()
    enable_ai, manual_override = render_sidebar_controls()

    # Input Section: Code Text Area + File Uploader
    st.subheader("📥 Source Code Input")
    col1, col2 = st.columns([3, 1])

    with col2:
        uploaded_file = st.file_uploader(
            "Upload Python File (.py)",
            type=["py", "pyw"],
            help="Drag and drop or browse for a Python file to review.",
        )

    initial_code = ""
    filename = "submitted_snippet"
    if uploaded_file is not None:
        filename = uploaded_file.name
        try:
            initial_code = uploaded_file.getvalue().decode("utf-8-sig")
            st.success(f"Loaded `{filename}` ({len(initial_code)} characters)")
        except UnicodeDecodeError:
            initial_code = uploaded_file.getvalue().decode("latin-1", errors="replace")

    with col1:
        code_input = st.text_area(
            "Paste Python Code",
            value=initial_code,
            height=260,
            placeholder="paste python code here to review (e.g. def foo(): eval(bar)...)",
        )

    # Line count indicator
    line_count = len(code_input.splitlines()) if code_input else 0
    st.caption(f"Line Count: `{line_count}` lines | Character Count: `{len(code_input)}` chars")

    review_clicked = st.button("🔍 Run Code Review", type="primary", use_container_width=True)

    if review_clicked or "last_pipeline_result" in st.session_state:
        if review_clicked:
            if not code_input.strip():
                st.error("❌ Input code is empty or whitespace only. Please enter code to review.")
                return

            with st.spinner("⏳ Running Code Review Pipeline (Validating -> Static Analysis -> AI Reasoning -> Fusion -> Scoring)..."):
                # Instantiate AI Reviewer if enabled
                ai_reviewer = get_ai_reviewer(force_mock=not enable_ai)
                pipeline = CodeReviewPipeline(ai_reviewer=ai_reviewer)

                pipeline_result = pipeline.run(
                    code=code_input,
                    filename=filename,
                    manual_override=manual_override,
                )
                st.session_state["last_pipeline_result"] = pipeline_result

        pipeline_result = st.session_state.get("last_pipeline_result")
        if not pipeline_result:
            return

        if not pipeline_result.success:
            st.error(f"❌ Review Failed: {pipeline_result.errors[0].message if pipeline_result.errors else 'Unknown error'}")
            return

        review_result = pipeline_result.review_result
        if not review_result:
            return

        # Render Dashboard
        st.markdown("---")
        render_score_dashboard(review_result.score)
        st.markdown("---")
        render_summary_metrics(review_result.summary)

        # Filters: Severity Chips & Category Filter
        st.markdown("---")
        st.subheader("🔍 Review Findings & Vulnerability Audit")
        
        f_col1, f_col2 = st.columns([1, 2])
        with f_col1:
            severity_filter = st.multiselect(
                "Filter by Severity",
                options=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"],
                default=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"],
            )
        with f_col2:
            category_filter = st.multiselect(
                "Filter by Category",
                options=[c.value for c in CategoryEnum],
                default=[c.value for c in CategoryEnum],
            )

        # Filter Issue List Client-side
        filtered_issues = [
            i for i in review_result.issues
            if i.severity.value.upper() in severity_filter
            and i.category.value in category_filter
        ]

        if not filtered_issues:
            if not review_result.issues:
                st.success("🎉 **No issues detected!** The submitted Python code passed all quality & security checks.")
            else:
                st.info("ℹ️ No issues match the active filter criteria.")
        else:
            st.write(f"Displaying `{len(filtered_issues)}` of `{len(review_result.issues)}` finding(s):")
            for idx, issue in enumerate(filtered_issues, 1):
                render_issue_card(issue, index=idx)

        # Render Export Buttons in Sidebar
        render_export_section(review_result)


if __name__ == "__main__":
    main()
