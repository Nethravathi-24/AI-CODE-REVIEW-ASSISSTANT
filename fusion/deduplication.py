"""Deduplication and similarity matching utilities for code issues."""

import re
from typing import List, Tuple
from core.issue_model import Issue, SeverityEnum


def normalize_text(text: str) -> str:
    """Normalizes description text for fuzzy matching by removing punctuation and lowercasing."""
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def issues_are_duplicates(issue_a: Issue, issue_b: Issue, line_tolerance: int = 2) -> bool:
    """Determines whether two Issue objects represent the same underlying code problem.

    Matching criteria:
    1. Categories match OR one category is a subset/superset (e.g. security vs. logical_bug).
    2. Line numbers overlap within line_tolerance.
    3. Description text shares significant term overlap.
    """
    # 1. Line distance check
    line_diff = abs(issue_a.line_start - issue_b.line_start)
    if line_diff > line_tolerance:
        return False

    # 2. Category check
    category_match = (
        issue_a.category == issue_b.category
        or issue_a.category.value in issue_b.category.value
        or issue_b.category.value in issue_a.category.value
    )

    # 3. Description keyword similarity check
    desc_a = set(normalize_text(issue_a.description).split())
    desc_b = set(normalize_text(issue_b.description).split())
    
    if not desc_a or not desc_b:
        text_similarity = 0.0
    else:
        intersection = desc_a.intersection(desc_b)
        text_similarity = len(intersection) / max(len(desc_a), len(desc_b))

    return category_match and (line_diff == 0 or text_similarity >= 0.3)


def get_higher_severity(sev1: SeverityEnum, sev2: SeverityEnum) -> SeverityEnum:
    """Returns the higher severity of two SeverityEnum values."""
    severity_order = [
        SeverityEnum.CRITICAL,
        SeverityEnum.HIGH,
        SeverityEnum.MEDIUM,
        SeverityEnum.LOW,
        SeverityEnum.INFORMATIONAL,
    ]
    idx1 = severity_order.index(sev1) if sev1 in severity_order else 4
    idx2 = severity_order.index(sev2) if sev2 in severity_order else 4
    return sev1 if idx1 <= idx2 else sev2
