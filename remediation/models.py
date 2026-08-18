"""Pydantic models for remediation and test generation."""

from typing import Optional
from pydantic import BaseModel, Field
from core.issue_model import ValidationStatusEnum


class FixGenerationRequest(BaseModel):
    """Payload request for generating code fixes."""

    issue_id: str
    code_snippet: str
    full_code: str
    description: str


class FixValidationResult(BaseModel):
    """Result of static AST validation on proposed fix snippet."""

    is_valid: bool
    status: ValidationStatusEnum
    error_message: Optional[str] = None
