"""Streamlit application entry point for AI Code Review Assistant."""

import streamlit as st
from input_handling import process_input
from app.ui.components import (
    render_header,
    render_input_section,
    render_pipeline_result,
)

# Configure Streamlit Page Settings
st.set_page_config(
    page_title="AI Code Review Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    """Main Streamlit application layout and execution flow."""
    render_header()

    # Sidebar Status Indicator
    with st.sidebar:
        st.header("Pipeline Controls")
        st.info("System Status: **Milestone 2 Prototype**")
        st.markdown(
            "- Static Analysis: *In Development*\n"
            "- AI Reasoning: *In Development*\n"
            "- Fusion & Scoring: *In Development*"
        )
        st.caption("AI Code Review Assistant v0.2.0")

    # Render Main Input Section
    code_input, filename, selected_language = render_input_section()

    # Review Trigger CTA Button
    review_button = st.button("Review Code 🚀", type="primary", use_container_width=False)

    if review_button:
        if not code_input and not filename:
            st.error("Please paste or upload code before starting a review.")
            return

        # Determine override language
        override_lang = (
            None if selected_language == "auto-detect" else selected_language
        )

        with st.spinner("Processing input & validating syntax..."):
            pipeline_result = process_input(
                input_data=code_input,
                filename=filename,
                override_language=override_lang,
            )

        # Render Input Processing Outcome
        render_pipeline_result(pipeline_result)


if __name__ == "__main__":
    main()
