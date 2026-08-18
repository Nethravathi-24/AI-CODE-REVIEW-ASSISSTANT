"""Reusable Streamlit UI components for AI Code Review Assistant."""

from typing import Tuple, Optional
import streamlit as st
from input_handling.models import InputPipelineResult


def render_header() -> None:
    """Renders the main application header and subtitle."""
    st.title("🔍 AI Code Review Assistant")
    st.markdown(
        "A hybrid static-analysis and LLM-reasoning tool that reviews code, "
        "explains issues, proposes validated fixes, generates tests, and scores code quality."
    )
    st.divider()


def render_input_section() -> Tuple[str, Optional[str], str]:
    """Renders code paste input area, file uploader, and language selector.

    Returns:
        Tuple[str, Optional[str], str]: (submitted_code_text, filename, selected_language)
    """
    col1, col2 = st.columns([3, 1])

    with col2:
        st.subheader("Settings")
        selected_language = st.selectbox(
            "Language",
            options=["Python", "Auto-detect"],
            index=0,
            help="Select programming language or auto-detect.",
        )

        uploaded_file = st.file_uploader(
            "Upload source file (.py)",
            type=["py", "txt"],
            help="Upload a .py source code file (max 200 KB).",
        )

    filename: Optional[str] = None
    initial_code: str = ""

    if uploaded_file is not None:
        filename = uploaded_file.name
        try:
            initial_code = uploaded_file.getvalue().decode("utf-8")
        except Exception:
            initial_code = uploaded_file.getvalue().decode("latin-1")

    with col1:
        st.subheader("Source Code Input")
        code_input = st.text_area(
            "Paste code snippet here:",
            value=initial_code,
            height=300,
            placeholder="def example_function(x, y):\n    return x + y\n",
            help="Paste your source code snippet here (max 50,000 characters).",
        )

    return code_input, filename, selected_language.lower()


def render_pipeline_result(result: InputPipelineResult) -> None:
    """Renders input pipeline processing outcome and status banners."""
    val = result.validation
    lang = result.language
    prep = result.preprocessed

    if not val.is_valid:
        st.error(f"❌ Input Validation Error: {val.error_message}")
        return

    # Encoding warning if fallback occurred
    if val.encoding_warning:
        st.warning(f"⚠️ {val.encoding_warning}")

    # Success validation summary
    st.success(
        f"✅ **Input Validated** | Language: `{lang.detected_language.title()}` "
        f"(Confidence: {lang.confidence * 100:.0f}%, Source: `{lang.source}`) | "
        f"Line Count: `{prep.line_count if prep else 0}`"
    )

    # AST Parse Syntax Status
    if prep:
        if prep.is_syntax_valid:
            st.info("ℹ️ **AST Parse Check**: Python syntax is valid.")
        else:
            line_str = f" Line {prep.syntax_error_lineno}" if prep.syntax_error_lineno else ""
            st.warning(
                f"⚠️ **Syntax Error Detected**{line_str}: {prep.syntax_error_message}"
            )
