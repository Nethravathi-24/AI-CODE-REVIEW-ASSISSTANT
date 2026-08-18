"""Shared component contracts and interface protocols for parallel development."""

from typing import List, Optional, Protocol, runtime_checkable
from core.issue_model import Fix, GeneratedTest, Issue, ReviewResult


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
        """Assembles and formats a ReviewResult into a structured report string."""
        ...


@runtime_checkable
class FixGeneratorProtocol(Protocol):
    """Contract for automated code remediation and fix generation."""

    def generate_fix(self, issue: Issue, code: str) -> Optional[Fix]:
        """Generates a suggested fix and corrected code snippet for an issue."""
        ...


@runtime_checkable
class TestGeneratorProtocol(Protocol):
    """Contract for executable unit test case generation."""

    __test__ = False

    def generate_test(self, issue: Issue, code: str) -> Optional[GeneratedTest]:
        """Generates a pytest test case targeting a reported code issue."""
        ...


@runtime_checkable
class ReportExporterProtocol(Protocol):
    """Contract for report export serialization (JSON, Markdown, PDF)."""

    def export(self, result: ReviewResult) -> str:
        """Serializes ReviewResult payload into target format string or binary payload."""
        ...

