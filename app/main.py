"""Streamlit web application entrypoint for AI Code Review Assistant."""

import streamlit as st

from app.ui.components import render_review_dashboard
from orchestrator.pipeline import review_code


def main() -> None:
    """Main Streamlit application lifecycle."""
    st.set_page_config(
        page_title="AI Code Review Assistant",
        page_icon="🛡️",
        layout="wide",
    )

    st.sidebar.title("Configuration")
    language = st.sidebar.selectbox(
        "Target Language", ["Python (Auto-detect)", "Python"]
    )

    st.header("Code Review Input")
    uploaded_file = st.file_uploader(
        "Upload Python file (.py)", type=["py"]
    )

    default_snippet = (
        "def compute_data(items):\n"
        "    try:\n"
        "        f = open('data.txt', 'r')\n"
        "        raw = f.read()\n"
        "        return eval(raw)\n"
        "    except:\n"
        "        pass\n"
    )

    if uploaded_file is not None:
        input_code = uploaded_file.getvalue().decode(
            "utf-8", errors="replace"
        )
    else:
        input_code = st.text_area(
            "Paste Python Code Snippet Below:",
            value=default_snippet,
            height=200,
        )

    if st.button("🚀 Run Code Review", type="primary"):
        if not input_code.strip():
            st.warning(
                "Please paste or upload Python code before running review."
            )
        else:
            with st.spinner("Analyzing code via static analyzers..."):
                filename = (
                    uploaded_file.name
                    if uploaded_file
                    else "submitted_snippet.py"
                )
                result = review_code(input_code)
                render_review_dashboard(result)


if __name__ == "__main__":
    main()
