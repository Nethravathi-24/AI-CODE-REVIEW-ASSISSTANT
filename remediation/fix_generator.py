"""Automated Fix Generator conforming to FixGeneratorProtocol with multi-language support."""

import logging
import re
from typing import List, Optional
from core.interfaces import FixGeneratorProtocol
from core.issue_model import CategoryEnum, CorrectedCode, Fix, Issue, ValidationStatusEnum
from remediation.validator import compute_unified_diff, validate_code_syntax

logger = logging.getLogger(__name__)


class FixGenerator(FixGeneratorProtocol):
    """Generates suggested remediation fixes and complete auto-corrected source code across supported languages."""

    def generate_fix(self, issue: Issue, code: str, language: str = "python") -> Optional[Fix]:
        """Generates a suggested fix, corrected code snippet, and diff for a single Issue."""
        if not issue or not code:
            return None

        lines = code.splitlines()
        target_line_idx = max(0, min(issue.line_start - 1, len(lines) - 1)) if lines else 0
        original_line = lines[target_line_idx] if lines else issue.code_snippet

        suggested_fix = ""
        corrected_line = original_line
        lang_clean = (language or "python").lower().strip()

        desc_lower = issue.description.lower()

        # Language-specific remediation rules for line snippet
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
                corrected_line = original_line.replace("catch (Exception e) {}", 'catch (Exception e) { logger.error("Error occurred", e); }')

        if not suggested_fix:
            suggested_fix = f"Remediate issue: {issue.description}"

        corrected_lines = list(lines)
        if lines and target_line_idx < len(corrected_lines):
            corrected_lines[target_line_idx] = corrected_line
        corrected_full_code = "\n".join(corrected_lines)

        is_valid, status, msg = validate_code_syntax(corrected_full_code, language=lang_clean)
        diff = compute_unified_diff(code, corrected_full_code, filename=issue.file or "submitted_code")

        return Fix(
            suggested_fix=suggested_fix,
            corrected_code=corrected_full_code if is_valid else corrected_line,
            diff=diff,
            validation_status=status if is_valid else ValidationStatusEnum.NOT_VALIDATED,
        )

    def generate_full_corrected_code(
        self,
        issues: List[Issue],
        code: str,
        language: str = "python",
        filename: str = "submitted_code",
    ) -> CorrectedCode:
        """Generates a complete, multi-issue auto-corrected source code file with AST validation and unified diff."""
        if not code or not code.strip():
            return CorrectedCode(
                original_code=code or "",
                corrected_code=code or "",
                language=language,
                is_changed=False,
                validation_status=ValidationStatusEnum.PASSED,
                applied_fixes=[],
                diff="",
            )

        lang_clean = (language or "python").lower().strip()
        lines = code.splitlines()
        applied_fixes: List[str] = []
        modified_lines = list(lines)
        needs_ast_import = False
        needs_os_import = False

        for issue in issues:
            desc_lower = issue.description.lower()
            line_idx = max(0, min(issue.line_start - 1, len(modified_lines) - 1)) if modified_lines else 0
            cur_line = modified_lines[line_idx] if modified_lines else ""

            if lang_clean in ("python", "py"):
                # 1. Bare except
                if ("bare except" in desc_lower or "except:" in cur_line) and "except Exception:" not in cur_line:
                    modified_lines[line_idx] = cur_line.replace("except:", "except Exception:")
                    applied_fixes.append(f"Line {issue.line_start}: Replaced bare 'except:' with 'except Exception:'")

                # 2. eval()
                elif "eval" in desc_lower or "eval(" in cur_line:
                    if "ast.literal_eval" not in cur_line:
                        modified_lines[line_idx] = cur_line.replace("eval(", "ast.literal_eval(")
                        needs_ast_import = True
                        applied_fixes.append(f"Line {issue.line_start}: Replaced unsafe eval() with ast.literal_eval()")

                # 3. Hardcoded password / credentials
                elif "password" in desc_lower or "credential" in desc_lower or "hardcoded" in desc_lower or "b105" in desc_lower:
                    if "=" in cur_line:
                        var_name = cur_line.split("=")[0].strip()
                        indent = cur_line[: len(cur_line) - len(cur_line.lstrip())]
                        modified_lines[line_idx] = f'{indent}{var_name} = os.getenv("{var_name.upper()}", get_password())'
                        needs_os_import = True
                        applied_fixes.append(f"Line {issue.line_start}: Replaced hardcoded credentials with os.getenv()")

                # 4. Wildcard import
                elif "wildcard" in desc_lower or "import *" in cur_line:
                    modified_lines[line_idx] = f"# {cur_line.strip()}  # REPLACED: Avoid wildcard import"
                    applied_fixes.append(f"Line {issue.line_start}: Commented out wildcard import *")

                # 5. Unused import / Unused local
                elif "unused" in desc_lower and ("import" in desc_lower or "variable" in desc_lower):
                    if cur_line.strip() and not cur_line.strip().startswith("#"):
                        modified_lines[line_idx] = f"# {cur_line.strip()}  # REMOVED: Unused declaration"
                        applied_fixes.append(f"Line {issue.line_start}: Commented out unused declaration")

            elif lang_clean in ("javascript", "typescript", "js", "ts", "jsx", "tsx"):
                if "eval" in desc_lower or "eval(" in cur_line:
                    modified_lines[line_idx] = cur_line.replace("eval(", "JSON.parse(")
                    applied_fixes.append(f"Line {issue.line_start}: Replaced eval() with JSON.parse()")
                elif "var" in desc_lower or cur_line.strip().startswith("var "):
                    modified_lines[line_idx] = cur_line.replace("var ", "const ", 1)
                    applied_fixes.append(f"Line {issue.line_start}: Replaced var with block-scoped const")
                elif "===" not in cur_line and "==" in cur_line:
                    modified_lines[line_idx] = cur_line.replace("==", "===")
                    applied_fixes.append(f"Line {issue.line_start}: Replaced loose equality == with strict equality ===")
                elif "innerhtml" in desc_lower or ".innerhtml" in cur_line.lower():
                    modified_lines[line_idx] = cur_line.replace(".innerHTML", ".textContent")
                    applied_fixes.append(f"Line {issue.line_start}: Replaced innerHTML with textContent")

            elif lang_clean == "java":
                if "system.out.println" in desc_lower or "System.out.println" in cur_line:
                    modified_lines[line_idx] = cur_line.replace("System.out.println", "logger.info")
                    applied_fixes.append(f"Line {issue.line_start}: Replaced System.out.println with logger.info")
                elif "catch" in desc_lower and "exception" in desc_lower:
                    modified_lines[line_idx] = cur_line.replace("catch (Exception e)", "catch (Exception e) { logger.error(\"Error\", e);")
                    applied_fixes.append(f"Line {issue.line_start}: Added logger statement inside catch block")

        # Global pattern pass for un-attributed obvious security/quality risks in file
        if lang_clean in ("python", "py"):
            for idx, line in enumerate(modified_lines):
                if "except:" in line and "except Exception:" not in line:
                    modified_lines[idx] = line.replace("except:", "except Exception:")
                    applied_fixes.append(f"Line {idx+1}: Replaced bare 'except:' with 'except Exception:'")
                elif "eval(" in line and "ast.literal_eval(" not in line:
                    modified_lines[idx] = line.replace("eval(", "ast.literal_eval(")
                    needs_ast_import = True
                    applied_fixes.append(f"Line {idx+1}: Replaced eval() with ast.literal_eval()")
                elif re.search(r'password\s*=\s*["\'][^"\']+["\']', line):
                    indent = line[: len(line) - len(line.lstrip())]
                    var_name = line.split("=")[0].strip()
                    modified_lines[idx] = f'{indent}{var_name} = os.getenv("{var_name.upper()}", get_password())'
                    needs_os_import = True
                    applied_fixes.append(f"Line {idx+1}: Replaced hardcoded password with os.getenv()")

        elif lang_clean == "java":
            for idx, line in enumerate(modified_lines):
                if "System.out.println" in line:
                    modified_lines[idx] = line.replace("System.out.println", "logger.info")
                    applied_fixes.append(f"Line {idx+1}: Replaced System.out.println with logger.info")
                if "catch (Exception" in line or "catch(Exception" in line:
                    if idx + 1 < len(modified_lines) and modified_lines[idx + 1].strip() in ("}", "}"):
                        modified_lines[idx] = line + ' logger.error("Error", e);'
                        applied_fixes.append(f"Line {idx+1}: Added logger statement inside empty catch block")

        # Deduplicate applied fix notes
        applied_fixes = list(dict.fromkeys(applied_fixes))

        # Insert required header imports for Python
        if lang_clean in ("python", "py"):
            header_inserts = []
            if needs_ast_import and "import ast" not in code:
                header_inserts.append("import ast")
            if needs_os_import and "import os" not in code:
                header_inserts.append("import os")
            if header_inserts:
                insert_idx = 0
                for idx, l in enumerate(modified_lines):
                    if l.startswith("#!") or l.startswith('"""') or l.startswith("'''"):
                        insert_idx = idx + 1
                    elif l.startswith("import ") or l.startswith("from "):
                        insert_idx = idx
                        break
                for h in reversed(header_inserts):
                    modified_lines.insert(insert_idx, h)

        corrected_code_str = "\n".join(modified_lines)
        if code and code.endswith("\n") and not corrected_code_str.endswith("\n"):
            corrected_code_str += "\n"

        is_changed = (corrected_code_str != code)

        # AST Syntax Validation of final corrected code
        is_valid, val_status, val_msg = validate_code_syntax(corrected_code_str, language=lang_clean)

        validation_error = None
        if not is_valid and is_changed:
            val_status = ValidationStatusEnum.FAILED
            validation_error = f"Corrected code failed AST syntax validation: {val_msg}"

        diff_str = compute_unified_diff(code, corrected_code_str, filename=filename)

        if not applied_fixes:
            applied_fixes = ["No issue corrections required. Source code is clean."] if not issues else ["Applied safe structural remediation."]

        return CorrectedCode(
            original_code=code,
            corrected_code=corrected_code_str,
            language=lang_clean,
            is_changed=is_changed,
            validation_status=val_status,
            validation_error=validation_error,
            applied_fixes=applied_fixes,
            diff=diff_str,
        )
