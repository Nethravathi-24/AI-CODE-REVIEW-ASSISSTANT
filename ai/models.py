"""Pydantic schemas for AI review reasoning output."""

from typing import List, Optional
from pydantic import BaseModel, Field


class AIFinding(BaseModel):
    """Structured AI review finding produced by LLM reasoning chain."""

    category: str = Field(description="Issue category e.g. logical_bug, security, runtime_problem, maintainability")
    severity: str = Field(description="Severity: critical, high, medium, low, informational")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Confidence level between 0.0 and 1.0")
    line_start: int = Field(default=1, ge=1, description="Starting line number")
    line_end: int = Field(default=1, ge=1, description="Ending line number")
    code_snippet: str = Field(default="", description="Relevant line of code snippet")
    description: str = Field(description="Clear summary of what the issue is")
    why_it_matters: str = Field(description="Explanation of risk, impact, or why it matters")
    suggested_fix: Optional[str] = Field(default=None, description="Recommended remediation action")
    corrected_code: Optional[str] = Field(default=None, description="Corrected snippet replacement")


class AIReviewResponse(BaseModel):
    """Container payload for structured LLM response."""

    findings: List[AIFinding] = Field(default_factory=list, description="List of AI detected findings")
    summary_notes: str = Field(default="", description="High level summary of AI review reasoning")
