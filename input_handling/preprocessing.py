"""Alias compatibility module for preprocessor.py."""

from input_handling.models import PreprocessedCode
from input_handling.preprocessor import preprocess_code

__all__ = ["preprocess_code", "PreprocessedCode"]
