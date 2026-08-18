"""Pydantic schemas for result fusion and deduplication."""

from typing import List, Optional
from pydantic import BaseModel, Field


class FusionConfig(BaseModel):
    """Configuration settings for findings fusion service."""

    line_tolerance: int = Field(default=2, ge=0, description="Max line distance for matching overlapping issues")
    confidence_boost_on_corroboration: float = Field(default=0.15, ge=0.0, le=0.5, description="Confidence boost when static and AI agree")
    prefer_ai_explanation: bool = Field(default=True, description="Whether to use detailed AI description on corroborated findings")
