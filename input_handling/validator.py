"""Input validation module for code size, encoding, binary safety, and file type checks."""

import os
from typing import Optional, Union

from input_handling.models import ValidationErrorType, ValidationResult
from services.config_service import get_settings


def validate_input(
    code: Union[str, bytes, None],
    filename: Optional[str] = None,
    max_size_kb: Optional[int] = None,
    max_chars: Optional[int] = None,
    allow_empty: bool = False,
) -> ValidationResult:
    """Validates raw submitted code against size limits, UTF-8 encoding, binary safety, and file extension.

    Args:
        code: The raw code submitted as string, bytes, or None.
        filename: Optional filename or identifier for file-type validation.
        max_size_kb: Optional max file size in KB override (defaults to Settings.MAX_FILE_SIZE_KB).
        max_chars: Optional max character count override (defaults to Settings.MAX_CODE_CHARS).
        allow_empty: Whether to allow whitespace/empty inputs (default: False).

    Returns:
        ValidationResult: Model indicating validation success or specific failure reason.
    """
    settings = get_settings()
    effective_max_kb = max_size_kb if max_size_kb is not None else settings.MAX_FILE_SIZE_KB
    effective_max_chars = max_chars if max_chars is not None else settings.MAX_CODE_CHARS
    max_bytes = effective_max_kb * 1024

    # 1. Null / None check
    if code is None:
        return ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.EMPTY_INPUT,
            error_message="Input code is missing or empty. Please provide code to review.",
            filename=filename,
        )

    # 2. Type handling, binary check, and UTF-8 decoding
    if isinstance(code, bytes):
        byte_size = len(code)

        # Early check for oversized bytes
        if byte_size > max_bytes:
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.OVERSIZED_BYTES,
                error_message=(
                    f"File size exceeds limit of {effective_max_kb} KB "
                    f"({byte_size / 1024:.1f} KB)."
                ),
                byte_size=byte_size,
                filename=filename,
            )

        # Safe binary check: null byte heuristic
        if b"\x00" in code:
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.BINARY_INPUT,
                error_message=(
                    "Binary or non-text file detected. Only UTF-8 plain text code files are supported."
                ),
                byte_size=byte_size,
                filename=filename,
            )

        # UTF-8 decoding (using utf-8-sig to automatically strip BOM if present)
        try:
            decoded_code = code.decode("utf-8-sig")
        except UnicodeDecodeError:
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.DECODING_ERROR,
                error_message=(
                    "Failed to decode input as UTF-8. Please ensure the file is valid UTF-8 encoded text."
                ),
                byte_size=byte_size,
                filename=filename,
            )
        char_count = len(decoded_code)

    elif isinstance(code, str):
        # Strip UTF-8 BOM if present in string
        decoded_code = code.lstrip("\ufeff")

        # Binary check on string (null bytes)
        if "\x00" in decoded_code:
            encoded_bytes = decoded_code.encode("utf-8", errors="replace")
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.BINARY_INPUT,
                error_message=(
                    "Binary or non-text content detected (contains null bytes). "
                    "Only plain text code is supported."
                ),
                byte_size=len(encoded_bytes),
                char_count=len(decoded_code),
                filename=filename,
            )

        encoded_bytes = decoded_code.encode("utf-8")
        byte_size = len(encoded_bytes)
        char_count = len(decoded_code)

    else:
        return ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.BINARY_INPUT,
            error_message=(
                f"Unsupported input type '{type(code).__name__}'. Expected str or bytes."
            ),
            filename=filename,
        )

    # 3. Oversized check (byte size & character count)
    if byte_size > max_bytes:
        return ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.OVERSIZED_BYTES,
            error_message=(
                f"File size exceeds limit of {effective_max_kb} KB "
                f"({byte_size / 1024:.1f} KB)."
            ),
            byte_size=byte_size,
            char_count=char_count,
            filename=filename,
        )

    if char_count > effective_max_chars:
        return ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.OVERSIZED_CHARS,
            error_message=(
                f"Code exceeds maximum character limit of {effective_max_chars:,} characters "
                f"({char_count:,} characters)."
            ),
            byte_size=byte_size,
            char_count=char_count,
            filename=filename,
        )

    # 4. Empty / Whitespace-only check
    if not allow_empty and not decoded_code.strip():
        return ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.EMPTY_INPUT,
            error_message="Input code is empty or contains only whitespace. Please provide code to review.",
            byte_size=byte_size,
            char_count=char_count,
            raw_code=decoded_code,
            filename=filename,
        )

    # 5. File extension validation for supported source files if filename is provided
    if filename:
        clean_filename = filename.strip()
        ignored_placeholders = {"submitted_snippet", "<stdin>", "snippet.py", ""}
        if clean_filename not in ignored_placeholders:
            ext = os.path.splitext(clean_filename)[1].lower()
            supported_exts = (".py", ".pyw", ".js", ".jsx", ".ts", ".tsx", ".java")
            if ext and ext not in supported_exts:
                return ValidationResult(
                    is_valid=False,
                    error_type=ValidationErrorType.INVALID_FILE_TYPE,
                    error_message=(
                        f"Invalid file extension '{ext}' for file '{clean_filename}'. "
                        "Supported extensions: .py, .pyw, .js, .jsx, .ts, .tsx, .java"
                    ),
                    byte_size=byte_size,
                    char_count=char_count,
                    raw_code=decoded_code,
                    filename=clean_filename,
                )

    return ValidationResult(
        is_valid=True,
        byte_size=byte_size,
        char_count=char_count,
        raw_code=decoded_code,
        filename=filename,
    )
