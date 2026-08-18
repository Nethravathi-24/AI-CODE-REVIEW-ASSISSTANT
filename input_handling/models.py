"""Pydantic domain models for the input handling layer."""

from typing import Optional
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Result of input validation checks."""

    is_valid: bool = Field(description="True if input passed all validation checks")
    error_message: Optional[str] = Field(
        default=None, description="Human-readable error description if validation failed"
    )
    error_type: Optional[str] = Field(
        default=None,
        description="Error classification (e.g. empty_input, oversized_input, binary_input)",
    )
    decoded_content: Optional[str] = Field(
        default=None, description="Decoded text content if validation succeeded"
    )
    encoding_used: Optional[str] = Field(
        default="utf-8", description="Encoding format used to decode input"
    )
    encoding_warning: Optional[str] = Field(
        default=None, description="Warning if fallback encoding was required"
    )


class LanguageDetectionResult(BaseModel):
    """Result of programming language detection."""

    detected_language: str = Field(
        description="Detected programming language name (e.g. 'python', 'unknown')"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Detection confidence score between 0.0 and 1.0"
    )
    source: str = Field(
        description="Detection signal source (e.g. 'override', 'file_extension', 'heuristics', 'fallback')"
    )
    is_supported: bool = Field(
        description="True if the language is supported by static analysis tools"
    )


class PreprocessorResult(BaseModel):
    """Result of code preprocessing and AST syntax validation."""

    original_code: str = Field(description="Exact original submitted source code")
    normalized_code: str = Field(description="Line-ending normalized code (LF)")
    is_syntax_valid: bool = Field(description="True if Python AST parsing succeeded")
    syntax_error_message: Optional[str] = Field(
        default=None, description="Syntax error message if AST parse failed"
    )
    syntax_error_lineno: Optional[int] = Field(
        default=None, description="Line number of syntax error"
    )
    syntax_error_offset: Optional[int] = Field(
        default=None, description="Column offset of syntax error"
    )
    line_count: int = Field(ge=0, description="Total line count of normalized code")


class InputPipelineResult(BaseModel):
    """Aggregated container for complete input processing pipeline."""

    validation: ValidationResult
    language: LanguageDetectionResult
    preprocessed: Optional[PreprocessorResult] = None
