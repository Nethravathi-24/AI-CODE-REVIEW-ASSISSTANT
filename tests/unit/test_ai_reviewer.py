"""Unit tests for AI Reviewer layer, mock reviewer, and static-only fallback behavior."""

import pytest
from ai.mock_reviewer import MockAIReviewer
from ai.openai_reviewer import OpenAIReviewer
from ai.reviewer import get_ai_reviewer
from core.issue_model import DetectionSourceEnum, Issue


def test_mock_ai_reviewer_behavior():
    """Test 1: MockAIReviewer produces deterministic AI issues when enabled."""
    reviewer = MockAIReviewer(return_mock_issues=True)
    issues = reviewer.review("x = 10 / 0")
    assert len(issues) >= 1
    assert issues[0].detection_source == DetectionSourceEnum.AI
    assert "division" in issues[0].description.lower()


def test_mock_ai_reviewer_empty_mode():
    """Test 2: MockAIReviewer returns empty list when return_mock_issues is False."""
    reviewer = MockAIReviewer(return_mock_issues=False)
    issues = reviewer.review("x = 10 / 0")
    assert len(issues) == 0


def test_openai_reviewer_missing_key_fallback():
    """Test 3: OpenAIReviewer returns empty list safely when API key is missing."""
    reviewer = OpenAIReviewer(api_key="")
    assert reviewer.is_available() is False
    issues = reviewer.review("def foo(): pass")
    assert len(issues) == 0


def test_factory_returns_mock_when_no_api_key():
    """Test 4: get_ai_reviewer returns non-crashing fallback when key is absent."""
    reviewer = get_ai_reviewer(api_key="")
    issues = reviewer.review("def bar(): return 42")
    assert len(issues) == 0


def test_openai_reviewer_model_configuration(monkeypatch):
    """Test 5: OpenAIReviewer respects model_name parameter, OPENAI_MODEL env var, and default."""
    # 1. Default model is gpt-4o
    r_default = OpenAIReviewer(api_key="sk-fake-key")
    assert r_default.model_name == "gpt-4o"

    # 2. Custom model passed in constructor
    r_custom = OpenAIReviewer(api_key="sk-fake-key", model_name="gpt-4-turbo")
    assert r_custom.model_name == "gpt-4-turbo"

    # 3. Environment variable OPENAI_MODEL
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    r_env = OpenAIReviewer(api_key="sk-fake-key")
    assert r_env.model_name == "gpt-4o-mini"

    # 4. get_ai_reviewer factory with env var override
    r_factory = get_ai_reviewer(api_key="sk-fake-key")
    assert isinstance(r_factory, OpenAIReviewer)
    assert r_factory.model_name == "gpt-4o-mini"
