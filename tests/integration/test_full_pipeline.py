"""End-to-end integration tests for complete Milestone 2 review pipeline."""

import pytest

from analyzers.base import BaseAnalyzer
from core.issue_model import (
    CategoryEnum,
    CodeQualityScore,
    DetectionSourceEnum,
    Issue,
    ReviewResult,
    ReviewSummary,
    SeverityEnum,
)
from orchestrator.pipeline import CodeReviewPipeline, review_code
from services.config_service import get_settings


class TestFullPipelineIntegration:
    """Integration test suite for the complete static review pipeline."""

    def test_1_valid_python_with_issues(self):
        """Test 1: Valid Python with multiple detectable static issues.

        Flow: Input -> Validation -> Preprocess -> Analyzers -> Result
        """
        code = (
            "import os\n"
            "import sys\n\n"
            "def process_user_input(input_str):\n"
            "    try:\n"
            "        result = eval(input_str)\n"
            "        return result\n"
            "    except:\n"
            "        return None\n"
        )

        result = review_code(code)

        assert isinstance(result, ReviewResult)
        assert result.language == "python"
        assert result.submitted_code.strip() == code.strip()
        assert len(result.issues) >= 2

        for issue in result.issues:
            assert isinstance(issue, Issue)
            assert issue.detection_source == DetectionSourceEnum.STATIC
            assert issue.severity in (
                SeverityEnum.CRITICAL,
                SeverityEnum.HIGH,
                SeverityEnum.MEDIUM,
                SeverityEnum.LOW,
                SeverityEnum.INFORMATIONAL,
            )
            assert issue.line_start >= 1
            assert issue.line_end >= issue.line_start
            assert isinstance(issue.description, str)
            assert len(issue.description) > 0
            assert isinstance(issue.why_it_matters, str)
            assert len(issue.why_it_matters) > 0

        assert isinstance(result.score, CodeQualityScore)
        assert isinstance(result.summary, ReviewSummary)
        assert result.summary.total_issues == len(result.issues)
        assert result.score.overall_score < 100.0

    def test_2_clean_python(self):
        """Test 2: Clean Python code returns ReviewResult with high score."""
        code = (
            "def calculate_area(width: float, height: float) -> float:\n"
            '    """Calculates the area of a rectangle."""\n'
            "    if width < 0 or height < 0:\n"
            '        raise ValueError("Dimensions must be non-negative")\n'
            "    return width * height\n"
        )

        result = review_code(code)

        assert isinstance(result, ReviewResult)
        assert result.language == "python"
        assert result.summary.critical_count == 0
        assert result.summary.high_count == 0
        assert result.score.overall_score >= 90.0
        assert result.score.label == "Excellent"

    def test_3_invalid_python_syntax_error(self):
        """Test 3: Syntactically invalid Python is handled safely."""
        broken_code = (
            "def invalid_syntax_example(\n"
            "    print('missing paren'"
        )

        result = review_code(broken_code)

        assert isinstance(result, ReviewResult)
        assert len(result.issues) >= 1
        syntax_issues = [
            i for i in result.issues
            if i.category == CategoryEnum.SYNTAX_ERROR
        ]
        assert len(syntax_issues) >= 1
        assert syntax_issues[0].severity == SeverityEnum.CRITICAL
        assert syntax_issues[0].line_start >= 1

    def test_4_empty_input_handled_safely(self):
        """Test 4: Empty input is validated safely and raises clean ValueError."""
        with pytest.raises(ValueError) as excinfo:
            review_code("")
        assert "empty" in str(excinfo.value).lower()

    def test_5_oversized_input_rejected(self):
        """Test 5: Oversized input exceeding MAX_CODE_CHARS is rejected with clean ValueError."""
        settings = get_settings()
        pad_count = (settings.MAX_CODE_CHARS // 5) + 100
        oversized_code = "# Padding\n" + ("x = 1\n" * pad_count)

        with pytest.raises(ValueError) as excinfo:
            review_code(oversized_code)
        assert "exceeds" in str(excinfo.value).lower()

    def test_6_analyzer_failure_isolation(self):
        """Test 6: Analyzer failure is isolated and pipeline continues."""
        class CrashingMockAnalyzer(BaseAnalyzer):
            @property
            def name(self) -> str:
                return "broken_mock_analyzer"

            def analyze(self, code: str, filename: str = "snippet") -> list:
                raise RuntimeError("Analyzer runtime catastrophe!")

        pipeline = CodeReviewPipeline()
        pipeline.analyzers = [CrashingMockAnalyzer()] + pipeline.analyzers

        code = "import os\n\ndef run(s):\n    return eval(s)\n"
        result = pipeline.review_code(code)

        assert isinstance(result, ReviewResult)
        tools_detected = {i.detecting_tool for i in result.issues}
        assert "bandit" in tools_detected or "pyflakes" in tools_detected

    def test_7_multiple_analyzer_findings_combined(self):
        """Test 7: Combined findings from multiple static analyzers."""
        code = (
            "import math\n"
            "import os\n\n"
            "def heavy_branching(a, b, c, d, e, f, g, h, i, j, k): \n"
            "    if a:\n"
            "        return 1\n"
            "    elif b:\n"
            "        return 2\n"
            "    elif c:\n"
            "        return 3\n"
            "    elif d:\n"
            "        return 4\n"
            "    elif e:\n"
            "        return 5\n"
            "    elif f:\n"
            "        return 6\n"
            "    elif g:\n"
            "        return 7\n"
            "    elif h:\n"
            "        return 8\n"
            "    elif i:\n"
            "        return 9\n"
            "    elif j:\n"
            "        return 10\n"
            "    elif k:\n"
            "        return 11\n"
            "    try:\n"
            "        eval(a)\n"
            "    except:\n"
            "        pass\n"
            "    return 0\n"
        )

        result = review_code(code)

        assert isinstance(result, ReviewResult)
        assert len(result.issues) >= 4

        detecting_tools = {i.detecting_tool for i in result.issues}
        assert "ast_analyzer" in detecting_tools
        assert "pyflakes" in detecting_tools
        assert "bandit" in detecting_tools
        assert "radon" in detecting_tools
        assert "pycodestyle" in detecting_tools

        assert result.summary.total_issues == len(result.issues)
        assert result.summary.medium_count >= 1
        assert result.score.overall_score < 100.0

    def test_8_streamlit_dashboard_compatibility(self):
        """Test 8: ReviewResult has all attributes for Streamlit UI."""
        code = (
            "def sample():\n"
            "    try:\n"
            "        eval('1')\n"
            "    except:\n"
            "        pass\n"
        )
        result = review_code(code)

        assert hasattr(result, "score")
        assert hasattr(result.score, "overall_score")
        assert hasattr(result.score, "label")
        assert hasattr(result.score, "dimensions")
        assert hasattr(result, "summary")
        assert hasattr(result.summary, "total_issues")
        assert hasattr(result.summary, "critical_count")
        assert hasattr(result.summary, "high_count")
        assert hasattr(result.summary, "executive_summary")
        assert hasattr(result, "issues")

        for issue in result.issues:
            assert hasattr(issue, "issue_id")
            assert hasattr(issue, "category")
            assert hasattr(issue, "severity")
            assert hasattr(issue, "confidence")
            assert hasattr(issue, "line_start")
            assert hasattr(issue, "line_end")
            assert hasattr(issue, "code_snippet")
            assert hasattr(issue, "description")
            assert hasattr(issue, "why_it_matters")
            assert hasattr(issue, "detecting_tool")

    def test_9_security_guarantee_no_user_code_execution(self):
        """Test 9: Malicious code is never executed during static review."""
        malicious_code = (
            "import sys\n\n"
            "def trigger_exploit():\n"
            '    raise SystemExit("MALICIOUS_EXECUTION_TRIGGERED")\n\n'
            "trigger_exploit()\n"
        )

        result = review_code(malicious_code)
        assert result is not None
        assert isinstance(result, ReviewResult)
