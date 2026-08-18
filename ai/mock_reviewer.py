"""Mock AI Reviewer implementation for testing and static-only fallback mode."""

from typing import List, Optional
from core.interfaces import AIReviewerProtocol
from core.issue_model import CategoryEnum, DetectionSourceEnum, Issue, SeverityEnum


class MockAIReviewer(AIReviewerProtocol):
    """Mock implementation of AIReviewerProtocol producing deterministic findings."""

    def __init__(self, return_mock_issues: bool = True):
        self.return_mock_issues = return_mock_issues

    def review(
        self, code: str, static_issues: Optional[List[Issue]] = None
    ) -> List[Issue]:
        """Returns deterministic mock AI issues if requested, otherwise an empty list."""
        if not self.return_mock_issues or not code.strip():
            return []

        ai_issues: List[Issue] = []

        # Example mock check for unhandled exceptions or logic bugs
        if "division" in code.lower() or "/" in code:
            ai_issues.append(
                Issue(
                    issue_id="ai-mock-zero-div-1",
                    category=CategoryEnum.LOGICAL_BUG,
                    severity=SeverityEnum.HIGH,
                    confidence=0.9,
                    line_start=1,
                    line_end=1,
                    code_snippet="division",
                    description="Potential unhandled ZeroDivisionError in arithmetic calculation.",
                    why_it_matters="Division operations without zero checks can cause unhandled ZeroDivisionError crashes at runtime.",
                    detection_source=DetectionSourceEnum.AI,
                    detecting_tool="openai_gpt4o",
                )
            )

        return ai_issues
