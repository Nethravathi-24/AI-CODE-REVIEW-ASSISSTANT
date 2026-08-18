"""Input Handling package providing validation, language detection, and preprocessing."""

from typing import Optional, Union

from input_handling.language_detector import detect_language
from input_handling.models import (
    InputProcessingResult,
    LanguageDetectionResult,
    PreprocessedCode,
    ValidationErrorType,
    ValidationResult,
)
from input_handling.preprocessor import preprocess_code
from input_handling.validator import validate_input


def process_input(
    code: Union[str, bytes, None],
    filename: Optional[str] = None,
    manual_override: Optional[str] = None,
    max_size_kb: Optional[int] = None,
    max_chars: Optional[int] = None,
    allow_empty: bool = False,
) -> InputProcessingResult:
    """Executes the full input handling sequence: Validation -> Detection -> Preprocessing.

    Invalid inputs are stopped early at the validation phase.

    Args:
        code: Submitted code (str, bytes, or None).
        filename: Optional filename or identifier.
        manual_override: Optional manual language override string.
        max_size_kb: Optional max file size in KB.
        max_chars: Optional max character count.
        allow_empty: Whether to allow whitespace/empty inputs.

    Returns:
        InputProcessingResult: Comprehensive result from the input handling pipeline.
    """
    # 1. Validation Stage
    validation_result = validate_input(
        code=code,
        filename=filename,
        max_size_kb=max_size_kb,
        max_chars=max_chars,
        allow_empty=allow_empty,
    )

    if not validation_result.is_valid:
        return InputProcessingResult(
            is_valid=False,
            validation=validation_result,
            error_message=validation_result.error_message,
        )

    # 2. Language Detection Stage
    language_result = detect_language(
        code=validation_result.raw_code,
        filename=filename,
        manual_override=manual_override,
    )

    # 3. Preprocessing Stage (CRLF normalization, AST syntax checking)
    preprocessed_result = preprocess_code(
        code=validation_result.raw_code,
        filename=filename or "submitted_snippet",
    )

    return InputProcessingResult(
        is_valid=True,
        validation=validation_result,
        language=language_result,
        preprocessed=preprocessed_result,
    )


__all__ = [
    "validate_input",
    "detect_language",
    "preprocess_code",
    "process_input",
    "ValidationResult",
    "ValidationErrorType",
    "LanguageDetectionResult",
    "PreprocessedCode",
    "InputProcessingResult",
]
