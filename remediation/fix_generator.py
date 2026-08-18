"""Automated Fix Generator conforming to FixGeneratorProtocol."""

import logging
from typing import Optional
from core.interfaces import FixGeneratorProtocol
from core.issue_model import CategoryEnum, Fix, Issue, ValidationStatusEnum
from remediation.validator import compute_unified_diff, validate_python_syntax

logger = logging.getLogger(__name__)


class FixGenerator(FixGeneratorProtocol):
    """Generates suggested remediation fixes for detected code issues."""

    def generate_fix(self, issue: Issue, code: str) -> Optional[Fix]:
        """Generates a suggested fix, corrected code snippet, and diff for an Issue."""
        if not issue or not code:
            return None

        lines = code.splitlines()
        target_line_idx = max(0, min(issue.line_start - 1, len(lines) - 1)) if lines else 0
        original_line = lines[target_line_idx] if lines else issue.code_snippet

        suggested_fix = ""
        corrected_line = original_line

        # Deterministic remediation rules based on issue categories & descriptions
        desc_lower = issue.description.lower()
        cat = issue.category

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

        elif cat == CategoryEnum.READABILITY or "line too long" in desc_lower:
            suggested_fix = "Break line to respect PEP 8 length limits (79 characters)."
            suggested_fix = "Refactor code into multi-line layout to adhere to PEP 8 standards."

        if not suggested_fix:
            suggested_fix = f"Remediate issue: {issue.description}"

        # Construct full corrected code if line replacement happened
        corrected_lines = list(lines)
        if lines and target_line_idx < len(corrected_lines):
            corrected_lines[target_line_idx] = corrected_line
        corrected_full_code = "\n".join(corrected_lines)

        # Validate syntax of corrected full code or snippet safely
        is_valid, status, msg = validate_python_syntax(corrected_full_code)

        diff = compute_unified_diff(code, corrected_full_code)

        return Fix(
            suggested_fix=suggested_fix,
            corrected_code=corrected_full_code if is_valid else corrected_line,
            diff=diff,
            validation_status=status if is_valid else ValidationStatusEnum.NOT_VALIDATED,
        )
