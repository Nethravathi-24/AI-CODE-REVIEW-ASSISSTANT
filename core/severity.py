"""Deterministic severity calculation engine for AI Code Review Assistant."""

from typing import Dict
from core.issue_model import CategoryEnum, SeverityEnum

# Deterministic base severity lookup table mapping category to default severity
CATEGORY_BASE_SEVERITY_MAP: Dict[CategoryEnum, SeverityEnum] = {
    CategoryEnum.SYNTAX_ERROR: SeverityEnum.CRITICAL,
    CategoryEnum.SECURITY: SeverityEnum.HIGH,
    CategoryEnum.LOGICAL_BUG: SeverityEnum.HIGH,
    CategoryEnum.RUNTIME_PROBLEM: SeverityEnum.HIGH,
    CategoryEnum.EDGE_CASE: SeverityEnum.MEDIUM,
    CategoryEnum.ERROR_HANDLING: SeverityEnum.MEDIUM,
    CategoryEnum.RESOURCE_MANAGEMENT: SeverityEnum.MEDIUM,
    CategoryEnum.PERFORMANCE: SeverityEnum.MEDIUM,
    CategoryEnum.CODE_QUALITY: SeverityEnum.LOW,
    CategoryEnum.MAINTAINABILITY: SeverityEnum.LOW,
    CategoryEnum.DUPLICATE_LOGIC: SeverityEnum.LOW,
    CategoryEnum.READABILITY: SeverityEnum.LOW,
    CategoryEnum.BEST_PRACTICE: SeverityEnum.INFORMATIONAL,
}


def calculate_base_severity(category: CategoryEnum) -> SeverityEnum:
    """Returns the baseline deterministic severity level for a given category.

    Args:
        category: The Issue CategoryEnum value.

    Returns:
        SeverityEnum: Default baseline severity.
    """
    return CATEGORY_BASE_SEVERITY_MAP.get(category, SeverityEnum.LOW)


def calculate_severity(
    category: CategoryEnum,
    confidence: float = 1.0,
    is_corroborated: bool = False,
) -> SeverityEnum:
    """Computes the final deterministic severity for an issue.

    Rules per PRD Part 12.2:
    1. Start with baseline category severity.
    2. Low-confidence AI-only findings (confidence < 0.6) are capped at MEDIUM even if
       the category base is HIGH/CRITICAL.
    3. Syntax errors are always CRITICAL regardless of confidence.
    4. Static + AI corroborated findings retain or reinforce base severity.

    Args:
        category: The category of the finding.
        confidence: Confidence score between 0.0 and 1.0.
        is_corroborated: True if finding is corroborated by both static and AI analysis.

    Returns:
        SeverityEnum: Final computed severity.
    """
    base = calculate_base_severity(category)

    # Hard rule: Syntax errors are always Critical
    if category == CategoryEnum.SYNTAX_ERROR:
        return SeverityEnum.CRITICAL

    # Cap low-confidence findings at Medium
    if confidence < 0.6 and base in (SeverityEnum.CRITICAL, SeverityEnum.HIGH):
        return SeverityEnum.MEDIUM

    return base
