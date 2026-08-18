"""Integration tests verifying the complete end-to-end static-analysis pipeline."""

from typing import List
import pytest
from core.interfaces import StaticAnalyzerProtocol
from core.issue_model import (
    CategoryEnum,
    CodeQualityScore,
    DetectionSourceEnum,
    Issue,
    PipelineResult,
    ReviewResult,
    ReviewSummary,
    SeverityEnum,
)
from orchestrator.pipeline import CodeReviewPipeline, review_code, run_pipeline


def test_end_to_end_static_pipeline_valid_python_with_findings():
    """Test 1: Proves complete flow from raw Python code string to structured ReviewResult/PipelineResult.

    Verifies:
    1. Input is accepted
    2. Validation succeeds
    3. Python is detected correctly
    4. Preprocessing executes
    5. All applicable static analyzers are invoked
    6. Issues are collected
    7. Severity processing is applied
    8. A structured ReviewResult & PipelineResult is returned
    9. The returned result contains structured Issue objects
    10. The pipeline succeeds without requiring AI, fusion, fix generation, or test generation
    """
    # Sample snippet containing:
    # - unused import (pyflakes)
    # - insecure eval (bandit)
    # - bare except (ast)
    sample_code = (
        "import sys\r\n"
        "\r\n"
        "def execute_user_script(payload: str):\r\n"
        "    try:\r\n"
        "        result = eval(payload)\r\n"
        "        return result\r\n"
        "    except:\r\n"
        "        return None\r\n"
    )

    pipeline = CodeReviewPipeline()
    pipeline_res: PipelineResult = pipeline.run(sample_code, filename="user_script.py")

    # 1-2. Pipeline succeeds and execution time recorded
    assert isinstance(pipeline_res, PipelineResult)
    assert pipeline_res.success is True
    assert pipeline_res.execution_time_seconds >= 0.0

    # 8. Structured ReviewResult returned
    review_res: ReviewResult = pipeline_res.review_result
    assert isinstance(review_res, ReviewResult)
    assert review_res.submitted_code == sample_code.replace("\r\n", "\r\n")  # raw code preserved

    # 3. Language detected as python
    assert review_res.language == "python"

    # 6. Issues are collected from static analyzers
    assert len(review_res.issues) >= 3
    detecting_tools = {issue.detecting_tool for issue in review_res.issues}
    assert "bandit" in detecting_tools
    assert "pyflakes" in detecting_tools
    assert ("ast" in detecting_tools or "ast_analyzer" in detecting_tools)

    # 7. Severity processing applied
    for issue in review_res.issues:
        assert isinstance(issue.severity, SeverityEnum)
        assert issue.detection_source == DetectionSourceEnum.STATIC
        assert issue.confidence > 0.0
        assert issue.line_start >= 1

    # 9. Structure of Issue objects
    categories = {issue.category for issue in review_res.issues}
    assert CategoryEnum.SECURITY in categories  # from eval
    assert CategoryEnum.ERROR_HANDLING in categories  # from bare except
    assert CategoryEnum.BEST_PRACTICE in categories  # from unused sys (Pyflakes UnusedImport)

    # Score and summary
    assert isinstance(review_res.score, CodeQualityScore)
    assert review_res.score.overall_score < 100.0
    assert isinstance(review_res.summary, ReviewSummary)
    assert review_res.summary.total_issues == len(review_res.issues)
    assert review_res.summary.high_count >= 1

    # 10. Direct review_code helper returns identical structured ReviewResult
    direct_res: ReviewResult = review_code(sample_code, filename="user_script.py")
    assert isinstance(direct_res, ReviewResult)
    assert len(direct_res.issues) == len(review_res.issues)


def test_end_to_end_clean_python_snippet():
    """Test 2: Proves clean Python snippet receives a perfect score and zero issues."""
    clean_code = (
        "def compute_square(num: int) -> int:\n"
        "    \"\"\"Return the square of a given integer.\"\"\"\n"
        "    return num * num\n"
    )

    pipeline_res = run_pipeline(clean_code, filename="math_ops.py")

    assert pipeline_res.success is True
    review_res = pipeline_res.review_result
    assert review_res is not None
    assert len(review_res.issues) == 0
    assert review_res.score.overall_score == 100.0
    assert review_res.score.label == "Excellent"
    assert review_res.summary.total_issues == 0


def test_analyzer_failure_isolation_and_resilience():
    """Test 3: Proves one failing/crashing analyzer does NOT crash the pipeline.

    Remaining analyzers continue executing and their issues are returned.
    """
    class CrashingAnalyzer(StaticAnalyzerProtocol):
        @property
        def name(self) -> str:
            return "crashing_analyzer"

        def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
            raise RuntimeError("Simulated internal analyzer crash (e.g. out of memory or unhandled AST)")

    class HealthyAnalyzer(StaticAnalyzerProtocol):
        @property
        def name(self) -> str:
            return "healthy_analyzer"

        def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
            return [
                Issue(
                    issue_id="healthy-001",
                    category=CategoryEnum.BEST_PRACTICE,
                    severity=SeverityEnum.INFORMATIONAL,
                    confidence=1.0,
                    file=filename,
                    line_start=1,
                    line_end=1,
                    code_snippet="x = 1",
                    description="Healthy analyzer discovered issue.",
                    why_it_matters="Explanation.",
                    detection_source=DetectionSourceEnum.STATIC,
                    detecting_tool="healthy_analyzer",
                )
            ]

    # Inject one crashing analyzer and one healthy analyzer
    pipeline = CodeReviewPipeline(analyzers=[CrashingAnalyzer(), HealthyAnalyzer()])

    # Run pipeline: should not raise exception
    pipeline_res = pipeline.run("x = 1\n", filename="test.py")

    assert pipeline_res.success is True
    assert pipeline_res.is_partial_analysis is True
    assert len(pipeline_res.errors) == 1
    assert pipeline_res.errors[0].stage == "static_analysis"
    assert "Simulated internal analyzer crash" in pipeline_res.errors[0].message
    assert any("CrashingAnalyzer" in w or "crashing_analyzer" in w for w in pipeline_res.warnings)

    # Issues from healthy analyzer are still collected and returned
    assert pipeline_res.review_result is not None
    assert len(pipeline_res.review_result.issues) == 1
    assert pipeline_res.review_result.issues[0].issue_id == "healthy-001"


def test_invalid_input_stops_before_static_analysis():
    """Test 4: Proves invalid inputs halt immediately before static analysis without executing analyzers."""
    class SpyAnalyzer(StaticAnalyzerProtocol):
        def __init__(self):
            self.call_count = 0

        @property
        def name(self) -> str:
            return "spy_analyzer"

        def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
            self.call_count += 1
            return []

    spy = SpyAnalyzer()
    pipeline = CodeReviewPipeline(analyzers=[spy])

    # 1. Test empty whitespace input
    res_empty = pipeline.run("   \n\t   ", filename="empty.py")
    assert res_empty.success is False
    assert res_empty.review_result is None
    assert len(res_empty.errors) == 1
    assert res_empty.errors[0].stage == "validation"
    assert spy.call_count == 0  # Analyzer was NEVER invoked!

    # 2. Test binary input
    res_bin = pipeline.run(b"\x00\x01\x02\x03\x04", filename="binary.py")
    assert res_bin.success is False
    assert res_bin.review_result is None
    assert spy.call_count == 0  # Analyzer was NEVER invoked!

    # 3. Test review_code on invalid input raises ValueError
    with pytest.raises(ValueError, match="Input code is empty or contains only whitespace"):
        pipeline.review_code("   ", filename="empty.py")


def test_syntax_error_in_code_captured_as_critical_issue():
    """Test 5: Proves unparseable Python syntax produces a structured CRITICAL syntax error Issue."""
    bad_syntax_code = "def broken_func(:\n    pass\n"

    pipeline_res = run_pipeline(bad_syntax_code, filename="syntax_err.py")

    assert pipeline_res.success is True
    assert pipeline_res.is_partial_analysis is True
    assert pipeline_res.review_result is not None

    issues = pipeline_res.review_result.issues
    syntax_issues = [i for i in issues if i.category == CategoryEnum.SYNTAX_ERROR]
    assert len(syntax_issues) == 1
    assert syntax_issues[0].severity == SeverityEnum.CRITICAL
    assert syntax_issues[0].line_start == 1
    assert syntax_issues[0].detecting_tool == "ast_parser"
    assert pipeline_res.review_result.score.overall_score <= 75.0
