"""Input validation component for AI Code Review Assistant."""

import os
from typing import Optional, Union, Set
from config.settings import settings
from input_handling.models import ValidationResult

# Supported file extensions for MVP (Python primary)
SUPPORTED_EXTENSIONS: Set[str] = {".py", ".txt"}


def _is_binary_bytes(raw_bytes: bytes) -> bool:
    """Checks if raw bytes contain non-text/binary characters or null bytes."""
    if b"\x00" in raw_bytes[:8192]:
        return True
    # Count non-printable control characters (excluding standard whitespace like \n, \r, \t)
    control_chars = sum(
        1 for b in raw_bytes[:4096] if b < 32 and b not in (9, 10, 13)
    )
    if len(raw_bytes) > 0 and (control_chars / min(len(raw_bytes), 4096)) > 0.30:
        return True
    return False


def validate_input(
    input_data: Union[str, bytes],
    filename: Optional[str] = None,
    max_size_kb: Optional[int] = None,
    max_chars: Optional[int] = None,
) -> ValidationResult:
    """Validates raw input data for size, encoding, binary content, and supported extension.

    Args:
        input_data: Raw code string or file bytes.
        filename: Optional filename if uploaded.
        max_size_kb: Maximum allowed size in KB (defaults to settings.MAX_FILE_SIZE_KB).
        max_chars: Maximum allowed characters (defaults to settings.MAX_CODE_CHARS).

    Returns:
        ValidationResult: Pydantic model with validation status and error/decoded data.
    """
    limit_kb = max_size_kb if max_size_kb is not None else settings.MAX_FILE_SIZE_KB
    limit_chars = max_chars if max_chars is not None else settings.MAX_CODE_CHARS

    # 1. File Extension Validation (if filename is provided)
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext and ext not in SUPPORTED_EXTENSIONS:
            supported_str = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            return ValidationResult(
                is_valid=False,
                error_type="unsupported_extension",
                error_message=f"Unsupported file type '{ext}'. Supported types: {supported_str}",
            )

    # 2. Byte Decoding & Binary Detection
    decoded_text: str = ""
    encoding_used: str = "utf-8"
    encoding_warning: Optional[str] = None

    if isinstance(input_data, bytes):
        # Size check on raw bytes
        byte_size_kb = len(input_data) / 1024.0
        if byte_size_kb > limit_kb:
            return ValidationResult(
                is_valid=False,
                error_type="oversized_input",
                error_message=f"File size ({byte_size_kb:.1f} KB) exceeds maximum limit of {limit_kb} KB.",
            )

        if _is_binary_bytes(input_data):
            return ValidationResult(
                is_valid=False,
                error_type="binary_input",
                error_message="This does not appear to be readable source code (binary content detected).",
            )

        # Attempt UTF-8 decode with fallback
        try:
            decoded_text = input_data.decode("utf-8")
            encoding_used = "utf-8"
        except UnicodeDecodeError:
            try:
                decoded_text = input_data.decode("latin-1")
                encoding_used = "latin-1"
                encoding_warning = "UTF-8 decoding failed. File decoded using fallback encoding (latin-1)."
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    error_type="encoding_error",
                    error_message=f"Failed to decode input content: {str(e)}",
                )
    elif isinstance(input_data, str):
        decoded_text = input_data
        # Check for null bytes in string
        if "\x00" in decoded_text:
            return ValidationResult(
                is_valid=False,
                error_type="binary_input",
                error_message="This does not appear to be readable source code (binary content detected).",
            )

        # Size check on string length/size
        str_size_kb = len(decoded_text.encode("utf-8")) / 1024.0
        if str_size_kb > limit_kb:
            return ValidationResult(
                is_valid=False,
                error_type="oversized_input",
                error_message=f"File size ({str_size_kb:.1f} KB) exceeds maximum limit of {limit_kb} KB.",
            )
    else:
        return ValidationResult(
            is_valid=False,
            error_type="malformed_input",
            error_message="Input data must be a string or bytes.",
        )

    # 3. Empty & Whitespace Validation
    if len(decoded_text) == 0:
        return ValidationResult(
            is_valid=False,
            error_type="empty_input",
            error_message="Please paste or upload code before starting a review",
        )

    if decoded_text.strip() == "":
        return ValidationResult(
            is_valid=False,
            error_type="whitespace_input",
            error_message="Provided input contains only whitespace.",
        )

    # 4. Character Limit Check
    if len(decoded_text) > limit_chars:
        return ValidationResult(
            is_valid=False,
            error_type="oversized_input",
            error_message=f"Code length ({len(decoded_text)} characters) exceeds maximum limit of {limit_chars} characters.",
        )

    return ValidationResult(
        is_valid=True,
        decoded_content=decoded_text,
        encoding_used=encoding_used,
        encoding_warning=encoding_warning,
    )
