"""Automated Fix Generator conforming to FixGeneratorProtocol with multi-language support."""

import logging
from typing import Optional
from core.interfaces import FixGeneratorProtocol
from core.issue_model import CategoryEnum, Fix, Issue, ValidationStatusEnum
from remediation.validator import compute_unified_diff, validate_code_syntax

logger = logging.getLogger(__name__)


class FixGenerator(FixGeneratorProtocol):
    """Generates suggested remediation fixes for detected code issues across supported languages."""

    def generate_fix(self, issue: Issue, code: str, language: str = "python") -> Optional[Fix]:
        """Generates a suggested fix, corrected code snippet, and diff for an Issue."""
        if not issue or not code:
            return None

        lines = code.splitlines()
        target_line_idx = max(0, min(issue.line_start - 1, len(lines) - 1)) if lines else 0
        original_line = lines[target_line_idx] if lines else issue.code_snippet

        suggested_fix = ""
        corrected_line = original_line
        lang_clean = (language or "python").lower().strip()

        desc_lower = issue.description.lower()
        cat = issue.category

        # Language-specific remediation rules
        if lang_clean in ("python", "py"):
            if "bare except" in desc_lower or "except:" in original_line:
                suggested_fix = "Replace bare 'except:' with 'except Exception:' to avoid catching system exit signals."
                corrected_line = original_line.replace("except:", "except Exception:")
            elif "wildcard import" in desc_lower or "import *" in original_line:
                suggested_fix = "Specify explicit module imports instead of wildcard 'import *'."
                corrected_line = original_line.replace("import *", "import module_name  # Specify exact imports")
            elif "eval" in desc_lower or "eval(" in original_line:
                suggested_fix = "Avoid eval(). Use ast.literal_eval() for safe literal evaluation or parse structured data."
                corrected_line = original_line.replace("eval(", "ast.literal_eval(")
            elif "exec" in desc_lower or "exec(" in original_line:
                suggested_fix = "Remove exec(). Execute code through defined functions rather than dynamic execution."
                corrected_line = f"# {original_line}  # REPLACED: Avoid dynamic exec()"
            elif "open(" in original_line and "with" not in original_line:
                suggested_fix = "Use a 'with' statement context manager to ensure proper file resource cleanup."
                corrected_line = f"with {original_line.strip()}:  # Ensure resource cleanup"

        elif lang_clean in ("javascript", "typescript", "js", "ts", "jsx", "tsx"):
            if "eval" in desc_lower or "eval(" in original_line:
                suggested_fix = "Avoid eval(). Parse structured JSON using JSON.parse() or refactor dynamic invocation."
                corrected_line = original_line.replace("eval(", "JSON.parse(")
            elif "var" in desc_lower or original_line.strip().startswith("var "):
                suggested_fix = "Replace 'var' with 'const' or 'let' for block-scoped variable declaration."
                corrected_line = original_line.replace("var ", "const ", 1)
            elif "===" not in original_line and "==" in original_line:
                suggested_fix = "Use strict equality '===' instead of loose equality '=='."
                corrected_line = original_line.replace("==", "===")
            elif "innerhtml" in desc_lower or ".innerhtml" in original_line.lower():
                suggested_fix = "Use 'textContent' or 'innerText' instead of 'innerHTML' to prevent XSS script injection."
                corrected_line = original_line.replace(".innerHTML", ".textContent")
            elif "console.log" in desc_lower or "console.log(" in original_line:
                suggested_fix = "Remove leftover debug console.log statement."
                corrected_line = f"// {original_line}  // REMOVED DEBUG LOG"

        elif lang_clean == "java":
            if "runtime.exec" in desc_lower or "Runtime.getRuntime().exec" in original_line:
                suggested_fix = "Use ProcessBuilder with parameterized argument list to prevent command injection."
                corrected_line = f"// {original_line}  // REPLACED: Use ProcessBuilder"
            elif "==" in original_line and "equals" not in original_line and ("\"" in original_line or "str" in desc_lower):
                suggested_fix = "Use string.equals(other) instead of '==' for String value comparison."
                corrected_line = original_line.replace("==", ".equals(") + ")"
            elif "system.out.println" in desc_lower or "System.out.println" in original_line:
                suggested_fix = "Use a logger instance (logger.info / logger.debug) instead of System.out.println."
                corrected_line = original_line.replace("System.out.println", "logger.info")
            elif "catch" in desc_lower and "exception" in desc_lower:
                suggested_fix = "Log or rethrow exception instead of catching generically without handling."
                corrected_line = original_line.replace("catch (Exception e) {}", "catch (Exception e) { logger.error(\"Error occurred\", e); }")

        if not suggested_fix:
            suggested_fix = f"Remediate issue: {issue.description}"

        # Construct full corrected code
        corrected_lines = list(lines)
        if lines and target_line_idx < len(corrected_lines):
            corrected_lines[target_line_idx] = corrected_line
        corrected_full_code = "\n".join(corrected_lines)

        # Validate syntax based on language
        is_valid, status, msg = validate_code_syntax(corrected_full_code, language=lang_clean)

        diff = compute_unified_diff(code, corrected_full_code, filename=issue.file or "submitted_code")

        return Fix(
            suggested_fix=suggested_fix,
            corrected_code=corrected_full_code if is_valid else corrected_line,
            diff=diff,
            validation_status=status if is_valid else ValidationStatusEnum.NOT_VALIDATED,
        )
