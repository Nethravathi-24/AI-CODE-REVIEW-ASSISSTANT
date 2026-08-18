"""Pydantic domain models and schemas for the input-handling pipeline layer."""

from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from core.issue_model import Issue


class ValidationErrorType(str, Enum):
    """Categorized failure types for input validation."""

    EMPTY_INPUT = "empty_input"
    OVERSIZED_BYTES = "oversized_bytes"
    OVERSIZED_CHARS = "oversized_chars"
    BINARY_INPUT = "binary_input"
    DECODING_ERROR = "decoding_error"
    INVALID_FILE_TYPE = "invalid_file_type"


class ValidationResult(BaseModel):
    """Result of validating raw code input against size, encoding, and format boundaries."""

    is_valid: bool = Field(description="Whether the input passed all validation checks")
    error_message: Optional[str] = Field(
        default=None, description="Human-readable validation failure reason"
    )
    error_type: Optional[ValidationErrorType] = Field(
        default=None, description="Specific category of validation failure"
    )
    byte_size: int = Field(default=0, ge=0, description="Size of input in bytes")
    char_count: int = Field(default=0, ge=0, description="Length of input in characters")
    raw_code: str = Field(default="", description="Decoded/cleaned code text")
    filename: Optional[str] = Field(
        default=None, description="Filename or identifier if provided"
    )


class LanguageDetectionResult(BaseModel):
    """Result of language detection heuristic and override analysis."""

    language: str = Field(
        default="python",
        description="Detected language identifier (e.g. 'python', 'unknown')",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        default=1.0,
        description="Confidence score between 0.0 and 1.0",
    )
    is_python: bool = Field(
        default=True, description="Whether the language was classified as Python"
    )
    detection_method: str = Field(
        default="heuristic",
        description="Method used: 'manual_override', 'file_extension', 'heuristic', 'fallback'",
    )
    matched_signatures: List[str] = Field(
        default_factory=list,
        description="Signatures or keywords that contributed to detection",
    )


class PreprocessedCode(BaseModel):
    """Result of code preprocessing, line mapping, and AST syntax validation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    original_code: str = Field(
        description="Original, unmodified code string as submitted"
    )
    normalized_code: str = Field(
        description="Normalized code string (LF line endings, BOM removed)"
    )
    line_count: int = Field(ge=0, description="Total number of lines in code")
    line_offsets: List[int] = Field(
        default_factory=list,
        description="0-indexed character offsets for start of each line in normalized code",
    )
    is_valid_syntax: bool = Field(
        default=True, description="True if AST parse succeeds, False on SyntaxError"
    )
    syntax_error: Optional[Issue] = Field(
        default=None,
        description="Structured Issue finding if syntax error occurred during AST parsing",
    )
    ast_tree: Optional[Any] = Field(
        default=None,
        exclude=True,
        description="Parsed ast.AST root node if syntax is valid",
    )

    def get_line(self, line_number: int) -> str:
        """Returns the 1-indexed line text from the normalized code.

        Args:
            line_number: 1-indexed line number.

        Returns:
            str: The corresponding line text or empty string if out of range.
        """
        if line_number < 1:
            return ""
        lines = self.normalized_code.split("\n")
        if line_number <= len(lines):
            return lines[line_number - 1]
        return ""


class InputProcessingResult(BaseModel):
    """Aggregate result from the entire input-handling sequence."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    is_valid: bool = Field(
        description="Whether input successfully passed validation and preprocessing"
    )
    validation: ValidationResult = Field(description="Validation stage result")
    language: Optional[LanguageDetectionResult] = Field(
        default=None, description="Language detection result"
    )
    preprocessed: Optional[PreprocessedCode] = Field(
        default=None, description="Preprocessing and AST syntax check result"
    )
    error_message: Optional[str] = Field(
        default=None, description="Overall error message if processing halted"
    )
