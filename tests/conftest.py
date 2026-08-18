"""Pytest fixtures and configuration for static analysis test suite."""

from pathlib import Path
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(fixture_name: str) -> str:
    """Helper to read fixture file content as a string."""
    fixture_path = FIXTURES_DIR / fixture_name
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def get_fixture():
    """Pytest fixture providing a function to load fixture strings by filename."""
    return load_fixture
