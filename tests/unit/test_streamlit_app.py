"""Integration and component tests for the Streamlit web interface and orchestrator pipeline."""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

from core.issue_model import CategoryEnum, PipelineResult, ReviewResult, SeverityEnum
from orchestrator import run_pipeline
from tests.conftest import load_fixture

APP_FILE = str((Path(__file__).resolve().parent.parent.parent / "app" / "main.py").resolve())


def test_streamlit_app_loads_successfully():
    """Test 1: Proves Streamlit app initializes, sets page title, and renders controls."""
    at = AppTest.from_file(APP_FILE).run()
    assert not at.exception
    assert len(at.title) >= 1
    assert "AI Code Review Assistant" in at.title[0].value
    assert len(at.text_area) >= 1
    assert len(at.button) >= 1


def test_streamlit_app_empty_input_validation():
    """Test 2: Proves clicking 'Review Code' with empty input renders a validation error banner."""
    at = AppTest.from_file(APP_FILE).run()
    at.text_area[0].input("   \n\t  ").run()

    review_button = next((b for b in at.button if "Review Code" in b.label), at.button[0])
    review_button.click().run()

    assert not at.exception
    assert len(at.error) >= 1
    assert "empty" in at.error[0].value.lower() or "whitespace" in at.error[0].value.lower()


def test_streamlit_app_clean_code_review():
    """Test 3: Proves submitting clean code displays zero issues and clean state success card."""
    clean_code = load_fixture("clean.py")
    at = AppTest.from_file(APP_FILE).run()
    at.text_area[0].input(clean_code).run()

    review_button = next((b for b in at.button if "Review Code" in b.label), at.button[0])
    review_button.click().run()

    assert not at.exception
    assert len(at.error) == 0
    assert len(at.success) >= 1
    assert "no issues detected" in at.success[0].value.lower()


def test_streamlit_app_security_code_review():
    """Test 4: Proves submitting security bug code renders issues with severity metrics."""
    sec_code = load_fixture("security_issue.py")
    at = AppTest.from_file(APP_FILE).run()
    at.text_area[0].input(sec_code).run()

    review_button = next((b for b in at.button if "Review Code" in b.label), at.button[0])
    review_button.click().run()

    assert not at.exception
    assert len(at.error) == 0
    metrics_labels = [m.label for m in at.metric]
    assert "Total Issues" in metrics_labels
    assert len(at.expander) >= 1


def test_orchestrator_pipeline_end_to_end_valid_and_invalid():
    """Test 5: Proves run_pipeline executes all stages deterministically."""
    dirty_code = "import math\n\ndef calc():\n    eval('1+1')\n"
    res_valid = run_pipeline(dirty_code, filename="test.py")

    assert isinstance(res_valid, PipelineResult)
    assert res_valid.success is True
    assert isinstance(res_valid.review_result, ReviewResult)
    assert res_valid.review_result.summary.total_issues >= 2

    # Invalid empty input
    res_invalid = run_pipeline("   ")
    assert res_invalid.success is False
    assert len(res_invalid.errors) == 1
    assert "empty" in res_invalid.errors[0].message.lower()
