"""Security, Reliability, and Performance validation test suite for Milestone 2."""

import time
from typing import List
import pytest

from core.interfaces import StaticAnalyzerProtocol
from core.issue_model import CategoryEnum, Issue, PipelineResult, ReviewResult, SeverityEnum
from input_handling.models import ValidationErrorType
from orchestrator import CodeReviewPipeline, review_code, run_pipeline
from tests.conftest import load_fixture


# ==============================================================================
# 1. SECURITY AUDIT TESTS
# ==============================================================================

def test_security_zero_code_execution_with_runtime_error():
    """Security Test 1: Proves user code containing an intentional runtime error is NEVER executed."""
    dangerous_code = (
        "def calculate():\n"
        "    raise RuntimeError('FATAL: If this error raises, user code was executed!')\n"
        "calculate()\n"
    )
    # Must NOT raise RuntimeError
    result = run_pipeline(dangerous_code, filename="safe_check.py")
    assert isinstance(result, PipelineResult)
    assert result.success is True
    assert result.review_result is not None


def test_security_zero_code_execution_with_system_exit():
    """Security Test 2: Proves user code attempting sys.exit or os operations is NOT executed."""
    exit_code = (
        "import sys\n"
        "import os\n"
        "sys.exit(99)\n"
    )
    # Must NOT exit process
    result = run_pipeline(exit_code, filename="exit_test.py")
    assert result.success is True
    assert result.review_result is not None


def test_security_eval_detected_statically_without_execution():
    """Security Test 3: Proves Bandit detects eval() statically without executing payload."""
    eval_code = "eval('1 + 1')\n"
    result = run_pipeline(eval_code, filename="eval_test.py")

    assert result.success is True
    assert result.review_result is not None
    # Must find Bandit security issue
    sec_issues = [
        i for i in result.review_result.issues if i.category == CategoryEnum.SECURITY
    ]
    assert len(sec_issues) >= 1
    assert any("B307" in ref or "eval" in i.description.lower() for i in sec_issues for ref in (i.references or []))


# ==============================================================================
# 2. RELIABILITY AUDIT TESTS
# ==============================================================================

@pytest.mark.parametrize("empty_payload", ["", "   ", "\t\t", "\n\n\r\n", "   \n\t  "])
def test_reliability_empty_and_whitespace_rejection(empty_payload: str):
    """Reliability Test 1: Proves empty and whitespace variations are rejected without running analyzers."""
    result = run_pipeline(empty_payload)
    assert result.success is False
    assert len(result.errors) == 1
    assert result.errors[0].stage == "input_validation"
    assert "empty" in result.errors[0].message.lower() or "whitespace" in result.errors[0].message.lower()


def test_reliability_syntax_error_resilience():
    """Reliability Test 2: Proves unparseable Python syntax is caught gracefully as a CRITICAL issue."""
    syntax_code = load_fixture("syntax_error.py")
    result = run_pipeline(syntax_code, filename="syntax_error.py")

    assert result.success is True
    assert result.review_result is not None
    crit_issues = [
        i for i in result.review_result.issues if i.severity == SeverityEnum.CRITICAL
    ]
    assert len(crit_issues) >= 1
    assert crit_issues[0].category == CategoryEnum.SYNTAX_ERROR


def test_reliability_binary_null_byte_rejection():
    """Reliability Test 3: Proves binary corrupted input with null bytes is rejected safely."""
    corrupt_code = "def safe():\n    pass\n\x00\x01\x02"
    result = run_pipeline(corrupt_code, filename="binary.py")

    assert result.success is False
    assert len(result.errors) == 1
    assert result.errors[0].error_type == ValidationErrorType.BINARY_INPUT.value


def test_reliability_max_size_boundaries():
    """Reliability Test 4: Proves input boundary behavior at exactly limit and beyond limit."""
    # 50,000 characters (max character limit)
    exact_limit_code = "# " + "a" * (50000 - 3) + "\n"
    res_exact = run_pipeline(exact_limit_code, filename="exact.py")
    assert res_exact.success is True

    # 50,001 characters (exceeds limit)
    over_limit_code = "# " + "a" * (50001 - 3) + "\n"
    res_over = run_pipeline(over_limit_code, filename="over.py")
    assert res_over.success is False
    assert res_over.errors[0].error_type == ValidationErrorType.OVERSIZED_CHARS.value


class FailingDummyAnalyzer:
    """Mock analyzer that throws an unhandled exception to test fault isolation."""
    name = "faulty_analyzer"

    def analyze(self, code: str, filename: str = "snippet") -> List[Issue]:
        raise RuntimeError("Simulated internal analyzer crash!")


def test_reliability_analyzer_fault_isolation():
    """Reliability Test 5: Proves a failing analyzer is isolated and does not crash pipeline."""
    pipeline = CodeReviewPipeline(analyzers=[FailingDummyAnalyzer()])
    result = pipeline.run_pipeline("def test(): pass", filename="test.py")

    assert result.success is True
    assert len(result.warnings) >= 1
    assert "faulty_analyzer" in result.warnings[0]


def test_reliability_clean_code_zero_findings():
    """Reliability Test 6: Proves clean code produces 0 issues and 100/100 score."""
    clean_code = load_fixture("clean.py")
    result = run_pipeline(clean_code, filename="clean.py")

    assert result.success is True
    assert result.review_result.summary.total_issues == 0
    assert result.review_result.score.overall_score == 100.0
    assert result.review_result.score.label == "Excellent"


# ==============================================================================
# 3. PERFORMANCE BENCHMARK TESTS
# ==============================================================================

def test_performance_static_analysis_pipeline_benchmarks():
    """Performance Test: Benchmarks the entire static-analysis pipeline across representative fixtures."""
    fixtures_to_benchmark = [
        ("clean.py", load_fixture("clean.py")),
        ("security_issue.py", load_fixture("security_issue.py")),
        ("high_complexity.py", load_fixture("high_complexity.py")),
        ("style_violation.py", load_fixture("style_violation.py")),
        ("resource_management.py", load_fixture("resource_management.py")),
    ]

    timings = {}
    for name, code in fixtures_to_benchmark:
        start = time.perf_counter()
        result = run_pipeline(code, filename=name)
        elapsed = time.perf_counter() - start

        timings[name] = elapsed
        assert result.success is True
        # Target is under 2.0 seconds per snippet (PRD requirement)
        assert elapsed < 2.0, f"Analysis of {name} took {elapsed:.4f}s (>2.0s target)"

    # Benchmark larger snippet (~500 lines)
    large_code = "\n".join([f"def func_{i}(x: int) -> int:\n    return x + {i}\n" for i in range(250)])
    start_large = time.perf_counter()
    res_large = run_pipeline(large_code, filename="large.py")
    elapsed_large = time.perf_counter() - start_large

    assert res_large.success is True
    assert elapsed_large < 10.0, f"Large snippet analysis took {elapsed_large:.4f}s (>10.0s target)"
