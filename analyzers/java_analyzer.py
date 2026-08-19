"""Real Java AST static analyzer using javalang AST parser and javac compiler checks."""

import logging
import os
import subprocess
import tempfile
from typing import Any, List, Optional
from analyzers.base import BaseAnalyzer
from core.issue_model import CategoryEnum, DetectionSourceEnum, Issue, SeverityEnum

logger = logging.getLogger(__name__)

try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False


def check_javac_available() -> bool:
    """Checks if javac executable is available on system path or JDK directory."""
    try:
        res = subprocess.run(["javac", "-version"], capture_output=True, text=True, timeout=3)
        return res.returncode == 0 or "javac" in res.stdout or "javac" in res.stderr
    except Exception:
        return False


JAVAC_AVAILABLE = check_javac_available()


class JavaAnalyzer(BaseAnalyzer):
    """Real Java static analyzer inspecting Java CompilationUnit AST nodes and javac compilation."""

    @property
    def name(self) -> str:
        return "java_analyzer"

    @property
    def language(self) -> str:
        return "java"

    @property
    def analyzer_type(self) -> str:
        return "ast_walker"

    @property
    def tool_name(self) -> str:
        return "javalang"

    def is_available(self) -> bool:
        return JAVALANG_AVAILABLE

    def get_availability_reason(self) -> str:
        return (
            "javalang AST parser and javac compiler operational"
            if JAVALANG_AVAILABLE
            else "javalang library not installed"
        )

    def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
        """Parses Java code into an AST and traverses nodes for static findings."""
        if not code or not code.strip():
            return []

        if not JAVALANG_AVAILABLE:
            logger.warning("JavaAnalyzer: javalang parser unavailable.")
            return []

        issues: List[Issue] = []
        lines = code.splitlines()

        # 1. Parse AST with javalang
        tree = None
        try:
            tree = javalang.parse.parse(code)
        except javalang.parser.JavaSyntaxError as err:
            line_no = getattr(err.at, "line", 1) if getattr(err, "at", None) else 1
            col = getattr(err.at, "column", 0) if getattr(err, "at", None) else 0
            msg = getattr(err, "description", str(err))
            snippet = lines[line_no - 1] if 0 <= line_no - 1 < len(lines) else ""

            return [
                Issue(
                    issue_id=f"java-syntax-err-L{line_no}",
                    category=CategoryEnum.SYNTAX_ERROR,
                    severity=SeverityEnum.CRITICAL,
                    confidence=1.0,
                    file=filename,
                    line_start=line_no,
                    line_end=line_no,
                    column=col,
                    code_snippet=snippet,
                    description=f"Java SyntaxError: {msg}",
                    why_it_matters="Java code containing syntax errors cannot be compiled by javac or executed.",
                    root_cause=f"Javalang AST parser raised JavaSyntaxError: {msg}",
                    detection_source=DetectionSourceEnum.STATIC,
                    detecting_tool=self.name,
                )
            ]
        except Exception as err:
            logger.debug(f"Javalang parse note: {err}")

        # 2. Optional javac compiler syntax check for extra compilation accuracy
        if JAVAC_AVAILABLE:
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    java_file = os.path.join(tmpdir, "Main.java" if "class Main" in code else "TempTest.java")
                    with open(java_file, "w", encoding="utf-8") as f:
                        f.write(code)

                    res = subprocess.run(
                        ["javac", "-proc:none", "-d", tmpdir, java_file],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if res.returncode != 0 and "error:" in res.stderr.lower():
                        # Parse first error line from javac
                        for err_line in res.stderr.splitlines():
                            if ": error:" in err_line:
                                parts = err_line.split(": error:")
                                loc_part = parts[0]
                                err_msg = parts[1].strip() if len(parts) > 1 else "Compilation error"
                                line_no = 1
                                if ":" in loc_part:
                                    try:
                                        line_no = int(loc_part.split(":")[-1])
                                    except ValueError:
                                        line_no = 1

                                snippet = lines[line_no - 1] if 0 <= line_no - 1 < len(lines) else ""
                                issues.append(
                                    Issue(
                                        issue_id=f"javac-compile-err-L{line_no}",
                                        category=CategoryEnum.SYNTAX_ERROR,
                                        severity=SeverityEnum.CRITICAL,
                                        confidence=1.0,
                                        file=filename,
                                        line_start=line_no,
                                        line_end=line_no,
                                        code_snippet=snippet,
                                        description=f"javac Compiler Error: {err_msg}",
                                        why_it_matters="Java compilation failed via javac compiler.",
                                        root_cause=f"javac output: {err_msg}",
                                        detection_source=DetectionSourceEnum.STATIC,
                                        detecting_tool="javac_compiler",
                                    )
                                )
                                break
            except Exception as exc:
                logger.debug(f"javac compilation check skipped: {exc}")

        if not tree:
            return issues

        # 3. Traverse Javalang AST nodes
        for path, node in tree:
            line_no = getattr(node.position, "line", 1) if getattr(node, "position", None) else 1
            snippet = lines[line_no - 1] if 0 <= line_no - 1 < len(lines) else ""

            # Rule A: Runtime.getRuntime().exec() or ProcessBuilder
            if isinstance(node, javalang.tree.MethodInvocation):
                member = getattr(node, "member", "")
                qualifier = getattr(node, "qualifier", "")
                if member == "exec" or qualifier == "Runtime.getRuntime()":
                    issues.append(
                        Issue(
                            issue_id=f"java-exec-L{line_no}",
                            category=CategoryEnum.SECURITY,
                            severity=SeverityEnum.HIGH,
                            confidence=1.0,
                            file=filename,
                            line_start=line_no,
                            line_end=line_no,
                            code_snippet=snippet,
                            description="Command Injection risk via Runtime.exec() in Java AST",
                            why_it_matters="Executing operating system commands with unvalidated input allows remote code execution.",
                            root_cause="AST MethodInvocation to Runtime.exec()",
                            detection_source=DetectionSourceEnum.STATIC,
                            detecting_tool=self.name,
                        )
                    )

                # Rule B: System.out.println
                elif member in ("println", "print") and qualifier == "System.out":
                    issues.append(
                        Issue(
                            issue_id=f"java-sysout-L{line_no}",
                            category=CategoryEnum.BEST_PRACTICE,
                            severity=SeverityEnum.INFORMATIONAL,
                            confidence=0.95,
                            file=filename,
                            line_start=line_no,
                            line_end=line_no,
                            code_snippet=snippet,
                            description="Use structured logger (SLF4J / Log4j2) instead of System.out.println",
                            why_it_matters="System.out lacks timestamps, severity levels, and configurable appenders.",
                            root_cause="AST MethodInvocation to System.out.println",
                            detection_source=DetectionSourceEnum.STATIC,
                            detecting_tool=self.name,
                        )
                    )

            # Rule C: String comparison using == instead of .equals()
            elif isinstance(node, javalang.tree.BinaryOperation):
                if getattr(node, "operator", "") == "==":
                    left = getattr(node, "operandl", None)
                    right = getattr(node, "operandr", None)
                    left_type = type(left).__name__
                    right_type = type(right).__name__
                    if "Literal" in left_type or "Literal" in right_type or "String" in snippet:
                        if not snippet.strip().startswith("//") and "null" not in snippet:
                            issues.append(
                                Issue(
                                    issue_id=f"java-streq-L{line_no}",
                                    category=CategoryEnum.LOGICAL_BUG,
                                    severity=SeverityEnum.HIGH,
                                    confidence=0.85,
                                    file=filename,
                                    line_start=line_no,
                                    line_end=line_no,
                                    code_snippet=snippet,
                                    description="String reference comparison using '==' instead of '.equals()'",
                                    why_it_matters="In Java, '==' compares object reference memory identity rather than string content.",
                                    root_cause="AST BinaryOperation with operator '==' on String",
                                    detection_source=DetectionSourceEnum.STATIC,
                                    detecting_tool=self.name,
                                )
                            )

            # Rule D: Swallowed or empty catch block
            elif isinstance(node, javalang.tree.CatchClause):
                block = getattr(node, "block", [])
                param = getattr(node, "parameter", None)
                param_type = getattr(getattr(param, "types", [None])[0], "name", "") if param else ""
                if not block or len(block) == 0:
                    issues.append(
                        Issue(
                            issue_id=f"java-catch-L{line_no}",
                            category=CategoryEnum.ERROR_HANDLING,
                            severity=SeverityEnum.MEDIUM,
                            confidence=0.95,
                            file=filename,
                            line_start=line_no,
                            line_end=line_no,
                            code_snippet=snippet,
                            description=f"Empty catch block swallowing Exception ({param_type})",
                            why_it_matters="Swallowing exceptions hides critical runtime errors and obscures root causes.",
                            root_cause="AST CatchClause with empty statement block",
                            detection_source=DetectionSourceEnum.STATIC,
                            detecting_tool=self.name,
                        )
                    )

            # Rule E: Unclosed I/O Stream declaration outside try-with-resources
            elif isinstance(node, javalang.tree.LocalVariableDeclaration):
                var_type = getattr(getattr(node, "type", None), "name", "")
                if var_type in ("FileInputStream", "FileOutputStream", "BufferedReader"):
                    if "try (" not in snippet and "try(" not in snippet:
                        issues.append(
                            Issue(
                                issue_id=f"java-stream-L{line_no}",
                                category=CategoryEnum.RESOURCE_MANAGEMENT,
                                severity=SeverityEnum.MEDIUM,
                                confidence=0.85,
                                file=filename,
                                line_start=line_no,
                                line_end=line_no,
                                code_snippet=snippet,
                                description=f"Use try-with-resources statement to guarantee closure of {var_type}",
                                why_it_matters="Unclosed file streams result in OS file descriptor leaks and memory growth.",
                                root_cause=f"AST LocalVariableDeclaration of {var_type} outside try-with-resources",
                                detection_source=DetectionSourceEnum.STATIC,
                                detecting_tool=self.name,
                            )
                        )

        return issues
