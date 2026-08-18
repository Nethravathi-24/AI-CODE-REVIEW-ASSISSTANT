"""Shared component contracts and interface protocols for parallel development."""

from typing import List, Optional, Protocol, runtime_checkable
from core.issue_model import Issue, ReviewResult


@runtime_checkable
class StaticAnalyzerProtocol(Protocol):
    """Contract for deterministic static analysis tools and wrappers.
    
    Owned by: Static Analysis Developer
    """

    def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
        """Runs static checks on the code and returns standardized Issue objects.
        
        Args:
            code: Source code text to analyze.
            filename: Identifier or filename for line tracking.

        Returns:
            List[Issue]: List of static finding Issue objects (detection_source="static").
        """
        ...


@runtime_checkable
class AIReviewerProtocol(Protocol):
    """Contract for LLM reasoning and code analysis chains.
    
    Owned by: AI Developer
    """

    def review(
        self, code: str, static_issues: Optional[List[Issue]] = None
    ) -> List[Issue]:
        """Runs AI reasoning on code using optional static findings as context.
        
        Args:
            code: Source code text to review.
            static_issues: Optional list of static findings already discovered.

        Returns:
            List[Issue]: List of AI finding Issue objects (detection_source="ai").
        """
        ...


@runtime_checkable
class FusionServiceProtocol(Protocol):
    """Contract for static and AI result fusion and reconciliation.
    
    Owned by: Team Lead / Shared
    """

    def fuse(
        self, static_issues: List[Issue], ai_issues: List[Issue]
    ) -> List[Issue]:
        """Merges, deduplicates, and reconciles static and AI findings.
        
        Args:
            static_issues: Baseline issues from static analyzers.
            ai_issues: Candidate issues from AI reasoning.

        Returns:
            List[Issue]: Single, unified, deduplicated list of Issue objects.
        """
        ...


@runtime_checkable
class ReportBuilderProtocol(Protocol):
    """Contract for report building and export serialization.
    
    Owned by: UI/Reporting Developer
    """

    def build(self, result: ReviewResult) -> str:
        """Assembles and formats a ReviewResult into a structured report string.
        
        Args:
            result: Complete ReviewResult model instance.

        Returns:
            str: Formatted report text (e.g. Markdown or JSON).
        """
        ...
