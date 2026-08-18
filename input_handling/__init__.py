"""Input handling package initialization."""

from input_handling.language_detection import detect_language
from input_handling.preprocessing import preprocess_code
from input_handling.validation import validate_input

__all__ = ["validate_input", "detect_language", "preprocess_code"]
