"""AI Reviewer factory module."""

import os
from typing import Optional
from ai.mock_reviewer import MockAIReviewer
from ai.openai_reviewer import OpenAIReviewer
from core.interfaces import AIReviewerProtocol
from services.config_service import get_settings


def get_ai_reviewer(
    force_mock: bool = False,
    api_key: Optional[str] = None,
) -> AIReviewerProtocol:
    """Factory function returning the appropriate AI reviewer implementation.

    Returns OpenAIReviewer if a valid API key is present and force_mock is False,
    otherwise returns MockAIReviewer.
    """
    settings = get_settings()
    effective_key = api_key or os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")

    if force_mock or not effective_key or not effective_key.strip() or effective_key.startswith("your_"):
        return MockAIReviewer(return_mock_issues=False)

    reviewer = OpenAIReviewer(api_key=effective_key)
    if reviewer.is_available():
        return reviewer

    return MockAIReviewer(return_mock_issues=False)
