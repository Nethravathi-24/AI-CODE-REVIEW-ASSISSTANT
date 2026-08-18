"""Unit tests for the input_handling package."""

import pytest
from input_handling import (
    detect_language,
    preprocess_code,
    process_input,
    validate_input,
)


def test_valid_python_input_validation():
    """Test 1: Valid Python string input passes validation."""
    code = "def add(a, b):\n    return a + b\n"
    res = validate_input(code)
    assert res.is_valid is True
    assert res.error_type is None
    assert res.decoded_content == code
    assert res.encoding_used == "utf-8"


def test_empty_input_validation():
    """Test 2: Empty input is rejected with clear error message."""
    res = validate_input("")
    assert res.is_valid is False
    assert res.error_type == "empty_input"
    assert "Please paste or upload code" in res.error_message


def test_whitespace_only_input_validation():
    """Test 3: Whitespace-only input is rejected."""
    res = validate_input("   \n\t   \n")
    assert res.is_valid is False
    assert res.error_type == "whitespace_input"
    assert "whitespace" in res.error_message


def test_oversized_input_validation():
    """Test 4: Input exceeding max character limit is rejected."""
    code = "a" * 100
    res = validate_input(code, max_chars=50)
    assert res.is_valid is False
    assert res.error_type == "oversized_input"
    assert "exceeds maximum limit" in res.error_message


def test_unsupported_file_extension():
    """Test 5: Unsupported file extension (e.g. .exe) is rejected."""
    res = validate_input("print('hello')", filename="payload.exe")
    assert res.is_valid is False
    assert res.error_type == "unsupported_extension"
    assert "Unsupported file type '.exe'" in res.error_message


def test_valid_utf8_bytes_validation():
    """Test 6: Valid UTF-8 encoded bytes are decoded properly."""
    raw_bytes = b"def main():\n    print('Hello World')\n"
    res = validate_input(raw_bytes, filename="script.py")
    assert res.is_valid is True
    assert res.decoded_content == "def main():\n    print('Hello World')\n"
    assert res.encoding_used == "utf-8"


def test_fallback_encoding_behavior():
    """Test 7: Non-UTF8 latin-1 bytes trigger fallback encoding with warning."""
    # Byte sequence invalid in UTF-8 but valid in latin-1 (e.g. Ren\xe9)
    raw_bytes = b"# Author: Ren\xe9\nx = 42\n"
    res = validate_input(raw_bytes)
    assert res.is_valid is True
    assert res.encoding_used == "latin-1"
    assert res.encoding_warning is not None
    assert "fallback encoding" in res.encoding_warning
    assert "René" in res.decoded_content


def test_binary_input_rejection():
    """Test 8: Unreadable binary data containing null bytes is rejected."""
    binary_data = b"\x00\x01\x02\x03\x04\x00\xff\xfe\xfd"
    res = validate_input(binary_data)
    assert res.is_valid is False
    assert res.error_type == "binary_input"
    assert "binary content detected" in res.error_message


def test_language_detection_file_extension():
    """Test 9: Python detected via .py file extension."""
    res = detect_language("x = 10", filename="test_app.py")
    assert res.detected_language == "python"
    assert res.confidence == 1.0
    assert res.source == "file_extension"
    assert res.is_supported is True


def test_language_detection_heuristics():
    """Test 10: Python detected via keyword pattern heuristics."""
    code = "import os\n\ndef run():\n    class Worker:\n        pass\n"
    res = detect_language(code)
    assert res.detected_language == "python"
    assert res.confidence >= 0.8
    assert res.source == "heuristics"
    assert res.is_supported is True


def test_language_detection_manual_override():
    """Test 11: Manual language override takes precedence over detection."""
    code = "unknown syntax line"
    res = detect_language(code, override_language="Python")
    assert res.detected_language == "python"
    assert res.confidence == 1.0
    assert res.source == "override"
    assert res.is_supported is True


def test_crlf_normalization_and_original_preservation():
    """Test 12: Preprocessor normalizes CRLF -> LF while preserving original source code."""
    crlf_code = "def foo():\r\n    a = 1\r\n    return a\r\n"
    res = preprocess_code(crlf_code)
    assert res.original_code == crlf_code
    assert res.normalized_code == "def foo():\n    a = 1\n    return a\n"
    assert "\r" not in res.normalized_code
    assert res.line_count == 4


def test_valid_python_ast_parsing():
    """Test 13: Valid Python code passes AST syntax validation."""
    code = "def compute(x):\n    return x * 2\n"
    res = preprocess_code(code)
    assert res.is_syntax_valid is True
    assert res.syntax_error_message is None
    assert res.syntax_error_lineno is None


def test_invalid_python_syntax_ast_parsing():
    """Test 14: Syntactically invalid Python captures line number and error message without crashing."""
    invalid_code = "def broken_func(:\n    pass\n"
    res = preprocess_code(invalid_code)
    assert res.is_syntax_valid is False
    assert res.syntax_error_message is not None
    assert res.syntax_error_lineno == 1


def test_malformed_input_type():
    """Test 15: Malformed non-string/non-bytes input is rejected cleanly."""
    res = validate_input(12345)  # type: ignore
    assert res.is_valid is False
    assert res.error_type == "malformed_input"


def test_full_input_pipeline_process_input():
    """Test 16: process_input facade coordinates validation, detection, and preprocessing end-to-end."""
    code = "def add(x, y):\r\n    return x + y\r\n"
    pipeline_res = process_input(code, filename="math_utils.py")
    assert pipeline_res.validation.is_valid is True
    assert pipeline_res.language.detected_language == "python"
    assert pipeline_res.preprocessed is not None
    assert pipeline_res.preprocessed.is_syntax_valid is True
    assert pipeline_res.preprocessed.normalized_code == "def add(x, y):\n    return x + y\n"
