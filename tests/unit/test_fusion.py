"""Unit tests for FusionService result fusion and deduplication."""

import pytest
from core.issue_model import CategoryEnum, DetectionSourceEnum, Issue, SeverityEnum
from fusion.fusion_service import FusionService


def test_fusion_service_combines_and_corroborates():
    """Test 1: Static and AI findings on same line are fused and corroborated."""
    static_issue = Issue(
        issue_id="stat-1",
        category=CategoryEnum.SECURITY,
        severity=SeverityEnum.MEDIUM,
        confidence=0.8,
        line_start=5,
        line_end=5,
        code_snippet="eval(code)",
        description="Dynamic code evaluation detected",
        why_it_matters="Security vulnerability",
        detection_source=DetectionSourceEnum.STATIC,
        detecting_tool="bandit",
    )

    ai_issue = Issue(
        issue_id="ai-1",
        category=CategoryEnum.SECURITY,
        severity=SeverityEnum.HIGH,
        confidence=0.9,
        line_start=5,
        line_end=5,
        code_snippet="eval(code)",
        description="Dangerous arbitrary execution using eval()",
        why_it_matters="Execution of untrusted strings causes severe RCE",
        detection_source=DetectionSourceEnum.AI,
        detecting_tool="openai_gpt4o",
    )

    fusion = FusionService()
    result = fusion.fuse([static_issue], [ai_issue])

    assert len(result) == 1
    fused = result[0]
    assert fused.detection_source == DetectionSourceEnum.BOTH
    assert fused.severity == SeverityEnum.HIGH
    assert fused.confidence > 0.8


def test_fusion_service_keeps_unrelated_separate():
    """Test 2: Unrelated findings on different lines remain separate."""
    static_issue = Issue(
        issue_id="stat-1",
        category=CategoryEnum.READABILITY,
        severity=SeverityEnum.LOW,
        confidence=0.7,
        line_start=2,
        line_end=2,
        code_snippet="x=1",
        description="Missing whitespace",
        why_it_matters="PEP 8 violation",
        detection_source=DetectionSourceEnum.STATIC,
        detecting_tool="style",
    )

    ai_issue = Issue(
        issue_id="ai-1",
        category=CategoryEnum.LOGICAL_BUG,
        severity=SeverityEnum.HIGH,
        confidence=0.85,
        line_start=15,
        line_end=15,
        code_snippet="return a / b",
        description="Potential division by zero",
        why_it_matters="Runtime zero division error",
        detection_source=DetectionSourceEnum.AI,
        detecting_tool="openai_gpt4o",
    )

    fusion = FusionService()
    result = fusion.fuse([static_issue], [ai_issue])

    assert len(result) == 2
