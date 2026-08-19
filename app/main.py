"""Primary Streamlit web application entry point for AI Code Review Assistant."""

from pathlib import Path
import sys
import streamlit as st

# Ensure repository root directory is in sys.path for absolute imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai import get_ai_reviewer
from analyzers import get_analyzers_for_language
from app.ui.components import (
    SAMPLE_CODE_SNIPPETS,
    render_analysis_engine_status,
    render_custom_css,
    render_dashboard_grid,
    render_export_section,
    render_header,
    render_issue_card,
    render_ready_to_analyze_bar,
    render_sidebar_controls,
    render_summary_metrics,
)
from core.issue_model import CategoryEnum
from orchestrator import CodeReviewPipeline


def main() -> None:
    """Main Streamlit application layout and execution controller."""
    st.set_page_config(
        page_title="AI Code Review Assistant",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject custom dark mode stylesheet matching visual dashboard screenshot
    render_custom_css()

    render_header()
    enable_ai, manual_override, analysis_depth, options = render_sidebar_controls()

    # Input Section Container matching screenshot layout
    st.markdown("---")
    st.markdown("### 🛠️ Source Code Input")
    st.caption("Paste your code or upload a file to start analysis")

    col1, col2 = st.columns([3, 1])

    initial_code = ""
    filename = "submitted_snippet"

    with col2:
        uploaded_file = st.file_uploader(
            "Upload Source File",
            type=["py", "pyw", "js", "jsx", "ts", "tsx", "java"],
            help="Supported: Python (.py, .pyw), JavaScript (.js, .jsx), TypeScript (.ts, .tsx), Java (.java)",
        )
        if uploaded_file is not None:
            filename = uploaded_file.name
            try:
                initial_code = uploaded_file.getvalue().decode("utf-8-sig")
                st.success(f"Loaded `{filename}` ({len(initial_code)} characters)")
            except UnicodeDecodeError:
                initial_code = uploaded_file.getvalue().decode("latin-1", errors="replace")

        sample_lang = st.selectbox("Load Example Code", options=["Select Example..."] + list(SAMPLE_CODE_SNIPPETS.keys()))
        if sample_lang and sample_lang != "Select Example...":
            initial_code = SAMPLE_CODE_SNIPPETS[sample_lang]

    with col1:
        code_input = st.text_area(
            "Paste Source Code",
            value=initial_code,
            height=260,
            placeholder="Paste source code here to review (Python, JavaScript, TypeScript, Java)...",
        )

    # Line count indicator
    line_count = len(code_input.splitlines()) if code_input else 0
    char_count = len(code_input) if code_input else 0
    syn_msg = "✓ Syntax appears valid" if code_input else "Waiting for code input"

    st.caption(f"Line 1, Col 1  •  `{line_count}` lines  •  `{char_count}` characters  •  **{syn_msg}**")

    # Ready to Analyze Action Bar & CTA Button
    st.markdown("---")
    review_clicked = render_ready_to_analyze_bar()

    if review_clicked or "last_pipeline_result" in st.session_state:
        if review_clicked:
            if not code_input.strip():
                st.error("❌ Input code is empty or whitespace only. Please enter code to review.")
                return

            with st.spinner("⏳ Running Code Review Pipeline (Validating -> Static AST Analysis -> AI Reasoning -> Fusion -> Scoring)..."):
                ai_reviewer = get_ai_reviewer(force_mock=not enable_ai)
                pipeline = CodeReviewPipeline(ai_reviewer=ai_reviewer)

                pipeline_result = pipeline.run(
                    code=code_input,
                    filename=filename,
                    manual_override=manual_override,
                )
                st.session_state["last_pipeline_result"] = pipeline_result

        pipeline_result = st.session_state.get("last_pipeline_result")
        if pipeline_result and pipeline_result.success and pipeline_result.review_result:
            review_result = pipeline_result.review_result

            # Render Dashboard Grid (Quality Score Preview, Severity Distribution, Analysis Engine Status)
            st.markdown("---")
            render_dashboard_grid(review_result, manual_override=manual_override)

            # Render Capability Details
            st.markdown("---")
            render_analysis_engine_status(
                review_result.language,
                get_analyzers_for_language(review_result.language),
                enable_ai=enable_ai,
            )
            st.markdown("---")
            render_summary_metrics(review_result.summary)

            # Render Findings & Audit Section
            st.markdown("---")
            st.subheader("🔍 Review Findings & Vulnerability Audit")

            col_f1, col_f2 = st.columns([1, 2])
            with col_f1:
                severity_filter = st.multiselect(
                    "Filter by Severity",
                    options=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"],
                    default=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"],
                )
            with col_f2:
                category_filter = st.multiselect(
                    "Filter by Category",
                    options=[c.value for c in CategoryEnum],
                    default=[c.value for c in CategoryEnum],
                )

            filtered_issues = [
                i for i in review_result.issues
                if i.severity.value.upper() in severity_filter
                and i.category.value in category_filter
            ]

            if not filtered_issues:
                if not review_result.issues:
                    st.success("🎉 **No issues detected!** The submitted source code passed all static AST quality & security checks.")
                else:
                    st.info("ℹ️ No issues match the active filter criteria.")
            else:
                st.write(f"Displaying `{len(filtered_issues)}` of `{len(review_result.issues)}` finding(s):")
                for idx, issue in enumerate(filtered_issues, 1):
                    render_issue_card(issue, index=idx)

            # Render Export Buttons in Sidebar
            render_export_section(review_result)
        else:
            # Pre-run state dashboard grid
            st.markdown("---")
            render_dashboard_grid(review_result=None, manual_override=manual_override)


if __name__ == "__main__":
    main()
