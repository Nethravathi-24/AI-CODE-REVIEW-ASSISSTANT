"""Input handling package providing validation, language detection, and preprocessing."""

from typing import Optional, Union
from input_handling.models import (
    InputPipelineResult,
    LanguageDetectionResult,
    PreprocessorResult,
    ValidationResult,
)
from input_handling.validator import validate_input
from input_handling.language_detector import detect_language
from input_handling.preprocessor import preprocess_code


def process_input(
    input_data: Union[str, bytes],
    filename: Optional[str] = None,
    override_language: Optional[str] = None,
    max_size_kb: Optional[int] = None,
    max_chars: Optional[int] = None,
) -> InputPipelineResult:
    """Full input handling pipeline coordinating validation, language detection, and preprocessing.

    Args:
        input_data: Raw code string or file bytes.
        filename: Optional filename if uploaded.
        override_language: Optional manual language override selection.
        max_size_kb: Optional file size limit in KB.
        max_chars: Optional character length limit.

    Returns:
        InputPipelineResult: Complete input processing result payload.
    """
    validation_res = validate_input(
        input_data, filename=filename, max_size_kb=max_size_kb, max_chars=max_chars
    )

    if not validation_res.is_valid or validation_res.decoded_content is None:
        # Return validation failure without running downstream detection/preprocessing
        fallback_lang = LanguageDetectionResult(
            detected_language="unknown",
            confidence=0.0,
            source="fallback",
            is_supported=False,
        )
        return InputPipelineResult(validation=validation_res, language=fallback_lang)

    # Detect language using decoded text
    lang_res = detect_language(
        validation_res.decoded_content,
        filename=filename,
        override_language=override_language,
    )

    # Preprocess code and validate syntax
    prep_res = preprocess_code(validation_res.decoded_content)

    return InputPipelineResult(
        validation=validation_res,
        language=lang_res,
        preprocessed=prep_res,
    )


__all__ = [
    "validate_input",
    "detect_language",
    "preprocess_code",
    "process_input",
    "ValidationResult",
    "LanguageDetectionResult",
    "PreprocessorResult",
    "InputPipelineResult",
]
