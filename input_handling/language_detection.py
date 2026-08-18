"""Alias compatibility module for language_detector.py."""

from input_handling.language_detector import detect_language
from input_handling.models import LanguageDetectionResult

__all__ = ["detect_language", "LanguageDetectionResult"]
