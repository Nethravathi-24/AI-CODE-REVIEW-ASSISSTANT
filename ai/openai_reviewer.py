"""OpenAI & LangChain LLM Reviewer implementation of AIReviewerProtocol."""

import logging
import os
from typing import List, Optional

from ai.models import AIFinding, AIReviewResponse
from ai.prompts import SYSTEM_PROMPT, USER_REVIEW_PROMPT_TEMPLATE
from core.interfaces import AIReviewerProtocol
from core.issue_model import CategoryEnum, DetectionSourceEnum, Issue, SeverityEnum
from services.config_service import get_settings

logger = logging.getLogger(__name__)


class OpenAIReviewer(AIReviewerProtocol):
    """OpenAI / LangChain code review engine conforming to AIReviewerProtocol."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")
        self.model_name = model_name or os.getenv("OPENAI_MODEL") or getattr(settings, "OPENAI_MODEL", "gpt-4o")

    def is_available(self) -> bool:
        """Returns True if a valid OpenAI API key is present."""
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("your_"))

    def review(
        self,
        code: str,
        static_issues: Optional[List[Issue]] = None,
        language: str = "python",
    ) -> List[Issue]:
        """Runs AI reasoning on code using optional static findings as context.

        Gracefully degrades and returns an empty list if API key is missing or service fails.
        """
        if not self.is_available():
            logger.info("OpenAI API key missing or invalid. AI review skipped (static-only mode).")
            return []

        if not code or not code.strip():
            return []

        try:
            # Try importing langchain_openai
            try:
                from langchain_core.prompts import ChatPromptTemplate
                from langchain_openai import ChatOpenAI
            except ImportError:
                logger.warning("langchain-openai or langchain-core not installed. AI review unavailable.")
                return []

            llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                temperature=0.1,
            )
            structured_llm = llm.with_structured_output(AIReviewResponse)

            static_context = "None"
            if static_issues:
                static_context = "\n".join(
                    f"- [{issue.severity.value.upper()}] Line {issue.line_start}: {issue.description}"
                    for issue in static_issues
                )

            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("user", USER_REVIEW_PROMPT_TEMPLATE),
            ])

            chain = prompt | structured_llm
            response: AIReviewResponse = chain.invoke({
                "code": code,
                "language": language or "python",
                "static_context": static_context,
            })

            return self._map_findings_to_issues(response.findings, code)

        except Exception as e:
            logger.error(f"AI review execution failed gracefully: {e}", exc_info=True)
            return []

    def _map_findings_to_issues(self, findings: List[AIFinding], code: str) -> List[Issue]:
        """Maps structured AIFinding objects into canonical Issue domain models."""
        issues: List[Issue] = []
        code_lines = code.splitlines()

        for idx, finding in enumerate(findings):
            # Map category string to CategoryEnum safely
            cat_str = finding.category.lower().replace(" ", "_")
            category = CategoryEnum.LOGICAL_BUG
            for cat_enum in CategoryEnum:
                if cat_enum.value == cat_str:
                    category = cat_enum
                    break

            # Map severity string to SeverityEnum safely
            sev_str = finding.severity.lower()
            severity = SeverityEnum.MEDIUM
            for sev_enum in SeverityEnum:
                if sev_enum.value == sev_str:
                    severity = sev_enum
                    break

            line_start = max(1, min(finding.line_start, len(code_lines) if code_lines else 1))
            line_end = max(line_start, min(finding.line_end, len(code_lines) if code_lines else 1))
            snippet = (
                finding.code_snippet
                or (code_lines[line_start - 1] if 0 <= line_start - 1 < len(code_lines) else "")
            )

            issues.append(
                Issue(
                    issue_id=f"ai-{idx+1}-{line_start}",
                    category=category,
                    severity=severity,
                    confidence=max(0.1, min(1.0, finding.confidence)),
                    line_start=line_start,
                    line_end=line_end,
                    code_snippet=snippet,
                    description=finding.description,
                    why_it_matters=finding.why_it_matters or "AI reasoning identified a potential code risk.",
                    detection_source=DetectionSourceEnum.AI,
                    detecting_tool=f"openai_{self.model_name}",
                )
            )

        return issues
