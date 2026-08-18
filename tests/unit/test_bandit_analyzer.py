"""Unit tests for Bandit security analyzer wrapper (analyzers/bandit_analyzer.py)."""

import pytest
from analyzers.bandit_analyzer import BanditAnalyzer
from core.interfaces import StaticAnalyzerProtocol
from core.issue_model import CategoryEnum, DetectionSourceEnum, SeverityEnum
from tests.conftest import load_fixture


@pytest.fixture
def analyzer() -> BanditAnalyzer:
    return BanditAnalyzer()


def test_bandit_implements_protocol(analyzer: BanditAnalyzer):
    """Verifies BanditAnalyzer satisfies StaticAnalyzerProtocol contract."""
    assert isinstance(analyzer, StaticAnalyzerProtocol)
    assert analyzer.name == "bandit"


def test_bandit_clean_code(analyzer: BanditAnalyzer):
    """Verifies clean code produces zero Bandit security issues."""
    code = load_fixture("clean.py")
    issues = analyzer.analyze(code, filename="clean.py")
    assert len(issues) == 0, f"Expected 0 issues on clean code, got: {issues}"


def test_bandit_security_hardcoded_secret(analyzer: BanditAnalyzer):
    """Verifies Bandit detects hardcoded password/API key credentials."""
    code = load_fixture("security_issue.py")
    issues = analyzer.analyze(code, filename="security_issue.py")

    assert len(issues) >= 1, f"Expected at least 1 security issue, got: {issues}"

    password_issue = next(
        (i for i in issues if any("B105" in ref or "B106" in ref for ref in (i.references or []))),
        None,
    )
    assert password_issue is not None, "Expected B105/B106 hardcoded secret issue"
    assert password_issue.category == CategoryEnum.SECURITY
    assert password_issue.severity in (SeverityEnum.HIGH, SeverityEnum.MEDIUM)
    assert password_issue.detection_source == DetectionSourceEnum.STATIC
    assert password_issue.detecting_tool == "bandit"
    assert password_issue.line_start in (3, 4)
    assert "password" in password_issue.description.lower() or "secret" in password_issue.description.lower()


def test_bandit_dangerous_eval(analyzer: BanditAnalyzer):
    """Verifies Bandit detects dangerous eval() execution."""
    code = load_fixture("dangerous_eval.py")
    issues = analyzer.analyze(code, filename="dangerous_eval.py")

    assert len(issues) >= 1, f"Expected Bandit issue for eval(), got: {issues}"

    eval_issue = next(
        (i for i in issues if any("B307" in ref or "B102" in ref for ref in (i.references or []))),
        None,
    )
    assert eval_issue is not None, "Expected B307/B102 issue for eval()"
    assert eval_issue.category == CategoryEnum.SECURITY
    assert eval_issue.severity in (SeverityEnum.HIGH, SeverityEnum.CRITICAL)
    assert eval_issue.detection_source == DetectionSourceEnum.STATIC
    assert eval_issue.detecting_tool == "bandit"
    assert eval_issue.line_start == 6
    assert "eval" in eval_issue.code_snippet


def test_bandit_syntax_error_handled_gracefully(analyzer: BanditAnalyzer):
    """Verifies Bandit exits cleanly on unparseable syntax without crashing."""
    code = load_fixture("syntax_error.py")
    issues = analyzer.analyze(code, filename="syntax_error.py")
    assert isinstance(issues, list)
