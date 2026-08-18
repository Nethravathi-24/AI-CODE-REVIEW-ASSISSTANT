"""Contract verification tests for shared interfaces, models, and pipeline skeleton."""

from typing import List, Optional

from core.interfaces import (
    AIReviewerProtocol,
    FusionServiceProtocol,
    ReportBuilderProtocol,
    StaticAnalyzerProtocol,
)
from core.issue_model import (
    CategoryEnum,
    CodeQualityScore,
    DetectionSourceEnum,
    Fix,
    GeneratedTest,
    Issue,
    PipelineError,
    PipelineResult,
    ReviewResult,
    ReviewSummary,
    SeverityEnum,
    ValidationStatusEnum,
)
from orchestrator.pipeline import CodeReviewPipeline, review_code


def test_issue_models_importable():
    """Test 1: Proves all core domain models can be imported and instantiated."""
    issue = Issue(
        issue_id="test-contract-001",
        category=CategoryEnum.SECURITY,
        severity=SeverityEnum.HIGH,
        confidence=0.9,
        line_start=1,
        line_end=1,
        code_snippet="eval(user_input)",
        description="Insecure eval usage",
        why_it_matters="Execution of arbitrary code.",
        detection_source=DetectionSourceEnum.STATIC,
    )
    assert issue.issue_id == "test-contract-001"


def test_interfaces_importable():
    """Test 2: Proves all protocol contracts can be imported and checked via runtime_checkable."""

    class MockStaticAnalyzer:
        def analyze(
            self, code: str, filename: str = "submitted_snippet"
        ) -> List[Issue]:
            return []

    class MockAIReviewer:
        def review(
            self, code: str, static_issues: Optional[List[Issue]] = None
        ) -> List[Issue]:
            return []

    class MockFusionService:
        def fuse(
            self, static_issues: List[Issue], ai_issues: List[Issue]
        ) -> List[Issue]:
            return []

    class MockReportBuilder:
        def build(self, result: ReviewResult) -> str:
            return "Mock Report"

    assert isinstance(MockStaticAnalyzer(), StaticAnalyzerProtocol)
    assert isinstance(MockAIReviewer(), AIReviewerProtocol)
    assert isinstance(MockFusionService(), FusionServiceProtocol)
    assert isinstance(MockReportBuilder(), ReportBuilderProtocol)


def test_pipeline_importable_and_executable():
    """Test 3: Proves pipeline skeleton imports and executes cleanly returning a valid ReviewResult."""
    result = review_code("def foo(): pass")
    assert isinstance(result, ReviewResult)
    assert result.language == "python"
    assert result.submitted_code == "def foo(): pass"
    assert isinstance(result.score, CodeQualityScore)
    assert isinstance(result.summary, ReviewSummary)


def test_no_circular_imports():
    """Test 4: Proves importing modules in different order causes no circular import issues."""
    import config.settings
    import core.interfaces
    import core.issue_model
    import core.severity
    import orchestrator.pipeline
    import services.config_service

    assert config.settings.settings is not None
    assert orchestrator.pipeline.CodeReviewPipeline is not None
