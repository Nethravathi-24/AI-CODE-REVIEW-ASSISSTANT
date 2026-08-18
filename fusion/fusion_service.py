"""FusionService implementation merging static and AI review findings."""

from typing import List, Optional
from core.interfaces import FusionServiceProtocol
from core.issue_model import DetectionSourceEnum, Issue
from fusion.deduplication import get_higher_severity, issues_are_duplicates
from fusion.models import FusionConfig


class FusionService(FusionServiceProtocol):
    """Result fusion engine merging static and AI findings into a canonical issue list."""

    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()

    def fuse(
        self, static_issues: List[Issue], ai_issues: List[Issue]
    ) -> List[Issue]:
        """Merges, deduplicates, and corroborates static and AI findings into a unified issue list."""
        if not static_issues and not ai_issues:
            return []

        if not static_issues:
            return list(ai_issues)

        if not ai_issues:
            return list(static_issues)

        fused_issues: List[Issue] = []
        matched_ai_indices = set()

        # Iterate over static issues as baseline
        for static_issue in static_issues:
            matched_ai = None
            matched_idx = -1

            for idx, ai_issue in enumerate(ai_issues):
                if idx in matched_ai_indices:
                    continue
                if issues_are_duplicates(static_issue, ai_issue, self.config.line_tolerance):
                    matched_ai = ai_issue
                    matched_idx = idx
                    break

            if matched_ai is not None:
                matched_ai_indices.add(matched_idx)
                
                # Corroborate findings
                merged_confidence = min(
                    1.0,
                    max(static_issue.confidence, matched_ai.confidence)
                    + self.config.confidence_boost_on_corroboration,
                )
                resolved_severity = get_higher_severity(
                    static_issue.severity, matched_ai.severity
                )

                description = (
                    matched_ai.description
                    if self.config.prefer_ai_explanation and matched_ai.description
                    else static_issue.description
                )
                why_it_matters = (
                    matched_ai.why_it_matters
                    if matched_ai.why_it_matters
                    else static_issue.why_it_matters
                )
                fix = matched_ai.fix or static_issue.fix
                test = matched_ai.generated_test or static_issue.generated_test

                corroborated_issue = Issue(
                    issue_id=static_issue.issue_id,
                    category=static_issue.category,
                    severity=resolved_severity,
                    confidence=merged_confidence,
                    line_start=static_issue.line_start,
                    line_end=static_issue.line_end,
                    code_snippet=static_issue.code_snippet or matched_ai.code_snippet,
                    description=description,
                    why_it_matters=why_it_matters,
                    fix=fix,
                    generated_test=test,
                    detection_source=DetectionSourceEnum.BOTH,
                    detecting_tool=f"{static_issue.detecting_tool}+{matched_ai.detecting_tool}",
                )
                fused_issues.append(corroborated_issue)
            else:
                fused_issues.append(static_issue)

        # Add remaining un-matched AI findings
        for idx, ai_issue in enumerate(ai_issues):
            if idx not in matched_ai_indices:
                fused_issues.append(ai_issue)

        return fused_issues
