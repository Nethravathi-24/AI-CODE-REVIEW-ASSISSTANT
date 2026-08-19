"""Comprehensive unit tests for the input-handling layer.

Covers:
- Input validation (valid, empty, oversized, binary, invalid file types)
- UTF-8 decoding & BOM handling
- Language detection & heuristics
- Manual language override
- CRLF -> LF normalization
- Original code and line number preservation
- AST syntax validation & Issue generation
- End-to-end process_input flow & early stoppage
- Zero code execution security guarantee
"""

import ast
import pytest

from core.issue_model import CategoryEnum, DetectionSourceEnum, SeverityEnum
from input_handling import (
    InputProcessingResult,
    LanguageDetectionResult,
    PreprocessedCode,
    ValidationErrorType,
    ValidationResult,
    detect_language,
    preprocess_code,
    process_input,
    validate_input,
)


# ============================================================================
# 1. Input Validation Tests
# ============================================================================


def test_validate_valid_string_input():
    """Test standard valid Python snippet validation."""
    code = "def hello():\n    return 'world'"
    result = validate_input(code, filename="test.py")

    assert result.is_valid is True
    assert result.error_type is None
    assert result.error_message is None
    assert result.raw_code == code
    assert result.char_count == len(code)
    assert result.byte_size == len(code.encode("utf-8"))
    assert result.filename == "test.py"


def test_validate_valid_bytes_input():
    """Test valid UTF-8 encoded bytes input."""
    code_str = "print('Hello from bytes!')"
    code_bytes = code_str.encode("utf-8")
    result = validate_input(code_bytes, filename="snippet.py")

    assert result.is_valid is True
    assert result.raw_code == code_str
    assert result.byte_size == len(code_bytes)
    assert result.char_count == len(code_str)


@pytest.mark.parametrize(
    "empty_input",
    [
        "",
        "   ",
        "\t\t\n\r\n  ",
        b"",
        b"   \r\n\t  ",
        None,
    ],
)
def test_validate_empty_and_whitespace_input(empty_input):
    """Test rejection of empty, whitespace-only, and None inputs."""
    result = validate_input(empty_input)

    assert result.is_valid is False
    assert result.error_type == ValidationErrorType.EMPTY_INPUT
    assert "empty" in result.error_message.lower() or "missing" in result.error_message.lower()


def test_validate_oversized_bytes():
    """Test rejection of inputs exceeding the 200 KB default file size limit."""
    # 201 KB input
    oversized_data = b"a = 1\n" * (35 * 1024)
    assert len(oversized_data) > 200 * 1024

    result = validate_input(oversized_data, filename="big_file.py")

    assert result.is_valid is False
    assert result.error_type == ValidationErrorType.OVERSIZED_BYTES
    assert "exceeds limit" in result.error_message


def test_validate_oversized_characters():
    """Test rejection of inputs exceeding the 50,000 character limit."""
    long_code = "# Comment\n" + "x = 1\n" * 10000
    assert len(long_code) > 50000

    result = validate_input(long_code)

    assert result.is_valid is False
    assert result.error_type == ValidationErrorType.OVERSIZED_CHARS
    assert "character limit" in result.error_message


def test_validate_custom_configurable_limits():
    """Test overriding max_size_kb and max_chars with custom values."""
    snippet = "def foo(): pass"

    # Size limit of 1 byte
    res1 = validate_input(snippet, max_size_kb=0)
    assert res1.is_valid is False
    assert res1.error_type == ValidationErrorType.OVERSIZED_BYTES

    # Char limit of 5 chars
    res2 = validate_input(snippet, max_chars=5)
    assert res2.is_valid is False
    assert res2.error_type == ValidationErrorType.OVERSIZED_CHARS


def test_validate_binary_input_with_null_bytes():
    """Test safe detection and rejection of binary files containing null bytes."""
    binary_bytes = b"PK\x03\x04\x00\x00\x00\x00some_binary_zip_data"
    result = validate_input(binary_bytes, filename="archive.zip")

    assert result.is_valid is False
    assert result.error_type == ValidationErrorType.BINARY_INPUT
    assert "binary" in result.error_message.lower()

    binary_str = "def foo():\x00 pass"
    res_str = validate_input(binary_str)
    assert res_str.is_valid is False
    assert res_str.error_type == ValidationErrorType.BINARY_INPUT


def test_validate_invalid_utf8_decoding():
    """Test rejection of corrupt non-UTF8 byte streams."""
    invalid_utf8 = b"\x80\x81\x82\xff\xfe"
    result = validate_input(invalid_utf8)

    assert result.is_valid is False
    assert result.error_type == ValidationErrorType.DECODING_ERROR
    assert "utf-8" in result.error_message.lower()


def test_validate_utf8_bom_handling():
    """Test that UTF-8 BOM is cleanly decoded and stripped from input."""
    raw_with_bom = "\ufeffdef calculate():\n    return 42"
    result = validate_input(raw_with_bom)

    assert result.is_valid is True
    assert not result.raw_code.startswith("\ufeff")
    assert result.raw_code.startswith("def calculate():")

    bytes_with_bom = b"\xef\xbb\xbfdef calculate():\n    return 42"
    result_bytes = validate_input(bytes_with_bom)
    assert result_bytes.is_valid is True
    assert not result_bytes.raw_code.startswith("\ufeff")
    assert result_bytes.raw_code.startswith("def calculate():")


def test_validate_unicode_characters():
    """Test handling of multi-byte UTF-8 Unicode (emojis, accented characters, Asian characters)."""
    unicode_code = (
        "# 🚀 Calculation Service for Zürich & 東京\n"
        "def greet(name: str = 'Müller') -> str:\n"
        "    return f'Grüezi {name}! 👋'\n"
    )
    result = validate_input(unicode_code.encode("utf-8"), filename="greet.py")

    assert result.is_valid is True
    assert "Grüezi" in result.raw_code
    assert "東京" in result.raw_code


@pytest.mark.parametrize(
    "invalid_filename",
    [
        "script.exe",
        "library.dll",
        "image.png",
        "document.pdf",
        "archive.tar.gz",
    ],
)
def test_validate_non_python_file_extensions(invalid_filename):
    """Test that unsupported file extensions are rejected when filename is provided."""
    code = "def foo(): pass"
    result = validate_input(code, filename=invalid_filename)

    assert result.is_valid is False
    assert result.error_type == ValidationErrorType.INVALID_FILE_TYPE
    assert "Invalid file extension" in result.error_message


@pytest.mark.parametrize(
    "valid_filename",
    [
        "main.py",
        "service.PY",
        "gui_app.pyw",
        "app.js",
        "service.ts",
        "Main.java",
        "path/to/module.py",
        "submitted_snippet",
        "<stdin>",
        "snippet.py",
    ],
)
def test_validate_valid_python_file_extensions(valid_filename):
    """Test acceptance of valid Python file extensions."""
    code = "def foo(): pass"
    result = validate_input(code, filename=valid_filename)

    assert result.is_valid is True
    assert result.error_type is None


# ============================================================================
# 2. Language Detection Tests
# ============================================================================


def test_language_detection_python_extension():
    """Test language detection with .py extension."""
    code = "x = 42\ny = x * 2"
    result = detect_language(code, filename="calculate.py")

    assert result.is_python is True
    assert result.language == "python"
    assert result.confidence >= 0.70


def test_language_detection_python_keywords():
    """Test language detection from Python keyword signatures without extension."""
    code = (
        "import os\n"
        "from typing import List\n\n"
        "class DataProcessor:\n"
        "    def __init__(self, data: List[int]):\n"
        "        self.data = data\n\n"
        "    async def process(self):\n"
        "        if not self.data:\n"
        "            return None\n"
        "        return [x * 2 for x in self.data]\n\n"
        "if __name__ == '__main__':\n"
        "    print('Running processor')"
    )
    result = detect_language(code)

    assert result.is_python is True
    assert result.language == "python"
    assert result.confidence >= 0.85
    assert "function_def" in result.matched_signatures
    assert "class_def" in result.matched_signatures
    assert "main_guard" in result.matched_signatures


def test_language_detection_manual_override():
    """Test manual language override takes highest priority."""
    # JavaScript code with manual Python override
    js_code = "function add(a, b) { return a + b; }"
    result = detect_language(js_code, manual_override="python")

    assert result.is_python is True
    assert result.language == "python"
    assert result.confidence == 1.0
    assert result.detection_method == "manual_override"

    # Python code with manual non-python override
    py_code = "def foo(): pass"
    result_non_py = detect_language(py_code, manual_override="javascript")
    assert result_non_py.is_python is False
    assert result_non_py.language == "javascript"
    assert result_non_py.confidence == 1.0


@pytest.mark.parametrize(
    "non_python_code, expected_lang",
    [
        ("function add(a, b) {\n  console.log(a);\n  return a + b;\n}", "javascript"),
        ("public class App {\n  public static void main(String[] args) {\n    System.out.println(1);\n  }\n}", "java"),
        ("#include <iostream>\n#include <vector>\nint main() {\n  std::cout << 1;\n}", "c_cpp"),
        ("package main\nimport \"fmt\"\nfunc main() {\n  fmt.Println(1)\n}", "go"),
        ("fn main() {\n  let mut x = 5;\n  println!(\"{}\", x);\n}", "rust"),
        ("<!DOCTYPE html>\n<html><head><title>Test</title></head><body><div>Hi</div></body></html>", "html"),
    ],
)
def test_language_detection_non_python_languages(non_python_code, expected_lang):
    """Test detection of non-Python snippets with low Python confidence."""
    result = detect_language(non_python_code)

    assert result.is_python is False
    assert result.language == expected_lang


def test_language_detection_ambiguous_code():
    """Test fallback for ambiguous snippets with no distinctive signatures."""
    code = "1 + 1"
    result = detect_language(code)

    assert result.is_python is False or result.confidence < 0.50
    if not result.is_python:
        assert result.language == "unknown"


# ============================================================================
# 3. Code Preprocessing & Normalization Tests
# ============================================================================


def test_crlf_to_lf_normalization():
    """Test normalization of Windows CRLF and legacy CR line endings to LF."""
    windows_code = "def first_line():\r\n    a = 1\r\n    b = 2\r\n    return a + b\r\n"
    mac_code = "def first_line():\r    a = 1\r    b = 2\r    return a + b\r"
    mixed_code = "def first_line():\r\n    a = 1\r    b = 2\n    return a + b\n"

    res_win = preprocess_code(windows_code)
    res_mac = preprocess_code(mac_code)
    res_mix = preprocess_code(mixed_code)

    assert "\r" not in res_win.normalized_code
    assert "\r" not in res_mac.normalized_code
    assert "\r" not in res_mix.normalized_code

    assert res_win.normalized_code == "def first_line():\n    a = 1\n    b = 2\n    return a + b\n"
    assert res_mac.normalized_code == "def first_line():\n    a = 1\n    b = 2\n    return a + b\n"
    assert res_mix.normalized_code == "def first_line():\n    a = 1\n    b = 2\n    return a + b\n"


def test_original_code_preservation():
    """Test that original_code is preserved with exact original bytes/CRLF untouched."""
    raw_code = "def add(x, y):\r\n    return x + y\r\n"
    result = preprocess_code(raw_code)

    assert result.original_code == raw_code
    assert "\r\n" in result.original_code
    assert "\r\n" not in result.normalized_code


def test_line_number_preservation_and_offsets():
    """Test that line count, 1-indexed line retrieval, and offsets remain accurate."""
    code = "line1 = 1\nline2 = 2\nline3 = 3\nline4 = 4\nline5 = 5"
    result = preprocess_code(code)

    assert result.line_count == 5
    assert len(result.line_offsets) == 5
    assert result.line_offsets[0] == 0
    assert result.line_offsets[1] == len("line1 = 1\n")

    assert result.get_line(1) == "line1 = 1"
    assert result.get_line(3) == "line3 = 3"
    assert result.get_line(5) == "line5 = 5"
    assert result.get_line(0) == ""
    assert result.get_line(99) == ""


def test_ast_syntax_valid_code():
    """Test AST parsing of syntactically valid Python code."""
    valid_code = (
        "def compute(values: list[int]) -> int:\n"
        "    total = 0\n"
        "    for val in values:\n"
        "        total += val\n"
        "    return total\n"
    )
    result = preprocess_code(valid_code, filename="compute.py")

    assert result.is_valid_syntax is True
    assert result.syntax_error is None
    assert isinstance(result.ast_tree, ast.AST)


@pytest.mark.parametrize(
    "invalid_code, expected_line, error_pattern",
    [
        ("def broken_syntax(:\n    pass", 1, "invalid syntax"),
        ("x = 10\nif x > 5\n    print('missing colon')", 2, "expected ':'"),
        ("def indent_error():\nprint('no indent')", 2, "expected an indented block"),
        ("numbers = [1, 2, 3\nprint(numbers)", 2, "closing parenthesis"),
    ],
)
def test_ast_syntax_invalid_code_generates_issue(invalid_code, expected_line, error_pattern):
    """Test that syntax errors are safely caught, generating a structured CRITICAL Issue."""
    result = preprocess_code(invalid_code, filename="bad_syntax.py")

    assert result.is_valid_syntax is False
    assert result.ast_tree is None
    assert result.syntax_error is not None

    issue = result.syntax_error
    assert issue.category == CategoryEnum.SYNTAX_ERROR
    assert issue.severity == SeverityEnum.CRITICAL
    assert issue.confidence == 1.0
    assert issue.detection_source == DetectionSourceEnum.STATIC
    assert issue.detecting_tool == "ast_parser"
    assert issue.file == "bad_syntax.py"
    assert issue.line_start >= 1
    assert issue.code_snippet != ""
    assert "Syntax Error:" in issue.description


# ============================================================================
# 4. End-to-End Pipeline & Integration Flow Tests
# ============================================================================


def test_process_input_valid_python_full_flow():
    """Test complete flow: Input -> Validation -> Detection -> Preprocessing."""
    code = (
        "import math\r\n\r\n"
        "def circle_area(radius: float) -> float:\r\n"
        "    return math.pi * (radius ** 2)\r\n"
    )

    res = process_input(code, filename="math_utils.py")

    assert isinstance(res, InputProcessingResult)
    assert res.is_valid is True
    assert res.error_message is None

    # 1. Validation passed
    assert res.validation.is_valid is True
    assert res.validation.filename == "math_utils.py"

    # 2. Language detected as Python
    assert res.language is not None
    assert res.language.is_python is True
    assert res.language.language == "python"

    # 3. Preprocessed cleanly
    assert res.preprocessed is not None
    assert res.preprocessed.is_valid_syntax is True
    assert res.preprocessed.syntax_error is None
    assert "\r\n" not in res.preprocessed.normalized_code
    assert "\r\n" in res.preprocessed.original_code


def test_process_input_invalid_input_stops_early():
    """Test that invalid inputs stop immediately at validation stage before detection/preprocessing."""
    # Empty input
    res_empty = process_input("   \n\t  ")
    assert res_empty.is_valid is False
    assert res_empty.validation.is_valid is False
    assert res_empty.language is None
    assert res_empty.preprocessed is None
    assert res_empty.error_message is not None

    # Binary input
    res_bin = process_input(b"\x00\x01\x02\x03\x04")
    assert res_bin.is_valid is False
    assert res_bin.language is None
    assert res_bin.preprocessed is None


def test_process_input_with_syntax_error():
    """Test that valid input with syntax error completes preprocessing with syntax_error Issue."""
    bad_code = "def bad_func(:\n    pass"
    res = process_input(bad_code, filename="snippet.py")

    assert res.is_valid is True  # Input itself is valid text
    assert res.validation.is_valid is True
    assert res.language.is_python is True
    assert res.preprocessed.is_valid_syntax is False
    assert res.preprocessed.syntax_error is not None
    assert res.preprocessed.syntax_error.category == CategoryEnum.SYNTAX_ERROR


# ============================================================================
# 5. Security Safeguard Verification (Zero Code Execution)
# ============================================================================


def test_zero_code_execution_constraint():
    """Verify that dangerous or side-effect heavy code is never executed during validation/preprocessing."""
    dangerous_code = (
        "import sys\n"
        "import os\n"
        "# This should never execute!\n"
        "raise RuntimeError('EXECUTION_ATTEMPT_DETECTED')\n"
    )

    # Must process without raising the RuntimeError in dangerous_code
    res = process_input(dangerous_code, filename="dangerous.py")

    assert res.is_valid is True
    assert res.preprocessed.is_valid_syntax is True
    assert res.preprocessed.syntax_error is None
