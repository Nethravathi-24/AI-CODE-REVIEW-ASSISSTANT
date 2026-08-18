"""Alias compatibility module for validator.py."""

from input_handling.models import ValidationErrorType, ValidationResult
from input_handling.validator import validate_input

__all__ = ["validate_input", "ValidationResult", "ValidationErrorType"]
