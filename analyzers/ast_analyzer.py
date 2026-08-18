"""AST Structural Analyzer detecting resource leaks, bare excepts, deep nesting, and parameter limits."""

import ast
from typing import List, Optional

from analyzers.base import BaseAnalyzer
from core.issue_model import (
    CategoryEnum,
    DetectionSourceEnum,
    Issue,
    SeverityEnum,
)


class ASTAnalyzer(BaseAnalyzer):
    """Custom AST node walker analyzing Python structural patterns."""

    @property
    def name(self) -> str:
        return "ast"

    def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
        """Performs structural AST analysis on code string."""
        issues: List[Issue] = []

        # 1. Parse AST
        try:
            tree = ast.parse(code, filename=filename)
        except (SyntaxError, IndentationError) as e:
            line_no = e.lineno or 1
            col_no = e.offset or 0
            snippet = self._get_code_snippet(code, line_no, line_no)
            issues.append(
                Issue(
                    issue_id=self._generate_issue_id("ast", "syntax-error", line_no),
                    category=CategoryEnum.SYNTAX_ERROR,
                    severity=SeverityEnum.CRITICAL,
                    confidence=1.0,
                    file=filename,
                    line_start=line_no,
                    line_end=line_no,
                    column=col_no,
                    code_snippet=snippet,
                    description=f"Syntax Error: {e.msg or 'Invalid syntax'}",
                    why_it_matters="Code containing syntax errors cannot be parsed or analyzed by static tools.",
                    root_cause=f"AST parser raised {type(e).__name__}",
                    detection_source=DetectionSourceEnum.STATIC,
                    detecting_tool="ast",
                )
            )
            return issues

        # 2. Walk AST to detect structural issues
        issues.extend(self._check_unclosed_files(tree, code, filename))
        issues.extend(self._check_bare_excepts(tree, code, filename))
        issues.extend(self._check_excessive_parameters(tree, code, filename))
        issues.extend(self._check_deep_nesting(tree, code, filename))

        return issues

    def _check_unclosed_files(
        self, tree: ast.AST, code: str, filename: str
    ) -> List[Issue]:
        """Detects calls to open() that are not managed by a 'with' context manager."""
        issues: List[Issue] = []

        # Collect all open() calls that appear as withitem context expressions
        with_open_nodes = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    for sub in ast.walk(item.context_expr):
                        if isinstance(sub, ast.Call):
                            with_open_nodes.add(sub)

        # Flag any open() Call not part of a 'with' statement
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                is_open_call = (
                    (isinstance(func, ast.Name) and func.id == "open")
                    or (
                        isinstance(func, ast.Attribute)
                        and func.attr == "open"
                        and isinstance(func.value, ast.Name)
                        and func.value.id in ("builtins", "io")
                    )
                )

                if is_open_call and node not in with_open_nodes:
                    line_start = getattr(node, "lineno", 1)
                    line_end = getattr(node, "end_lineno", line_start)
                    snippet = self._get_code_snippet(code, line_start, line_end)
                    issues.append(
                        Issue(
                            issue_id=self._generate_issue_id(
                                "ast", "unclosed-file-open", line_start
                            ),
                            category=CategoryEnum.RESOURCE_MANAGEMENT,
                            severity=SeverityEnum.MEDIUM,
                            confidence=1.0,
                            file=filename,
                            line_start=line_start,
                            line_end=line_end,
                            column=getattr(node, "col_offset", None),
                            code_snippet=snippet,
                            description="Unclosed file handle: 'open()' called without 'with' context manager.",
                            why_it_matters=(
                                "Failing to use a context manager ('with open(...)') when opening files "
                                "can result in unclosed file descriptors, memory leaks, and data corruption."
                            ),
                            root_cause="File opened without deterministic context manager management.",
                            detection_source=DetectionSourceEnum.STATIC,
                            detecting_tool="ast",
                            references=["CWE-775", "PEP-343"],
                        )
                    )
        return issues

    def _check_bare_excepts(
        self, tree: ast.AST, code: str, filename: str
    ) -> List[Issue]:
        """Detects bare 'except:' or 'except BaseException:' handlers."""
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                is_bare = node.type is None
                is_base_exception = (
                    isinstance(node.type, ast.Name)
                    and node.type.id == "BaseException"
                )

                if is_bare or is_base_exception:
                    line_start = getattr(node, "lineno", 1)
                    line_end = getattr(node, "end_lineno", line_start)
                    snippet = self._get_code_snippet(code, line_start, line_end)
                    issues.append(
                        Issue(
                            issue_id=self._generate_issue_id(
                                "ast", "bare-except", line_start
                            ),
                            category=CategoryEnum.ERROR_HANDLING,
                            severity=SeverityEnum.MEDIUM,
                            confidence=1.0,
                            file=filename,
                            line_start=line_start,
                            line_end=line_end,
                            column=getattr(node, "col_offset", None),
                            code_snippet=snippet,
                            description=(
                                "Bare 'except:' or catching 'BaseException' catches system exit "
                                "signals and keyboard interrupts."
                            ),
                            why_it_matters=(
                                "Catching overly broad exceptions masks bugs and prevents graceful "
                                "process termination (e.g., KeyboardInterrupt, SystemExit)."
                            ),
                            root_cause="Broad exception handler specified.",
                            detection_source=DetectionSourceEnum.STATIC,
                            detecting_tool="ast",
                            references=["PEP-8", "CWE-396"],
                        )
                    )
        return issues

    def _check_excessive_parameters(
        self, tree: ast.AST, code: str, filename: str
    ) -> List[Issue]:
        """Detects functions with more than 5 parameters."""
        issues: List[Issue] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = node.args
                # Count total formal parameters
                total_args = (
                    len(args.args)
                    + len(getattr(args, "posonlyargs", []))
                    + len(args.kwonlyargs)
                )

                if total_args > 5:
                    line_start = getattr(node, "lineno", 1)
                    line_end = getattr(node, "end_lineno", line_start)
                    snippet = self._get_code_snippet(code, line_start, line_start)
                    issues.append(
                        Issue(
                            issue_id=self._generate_issue_id(
                                "ast", "excessive-parameters", line_start
                            ),
                            category=CategoryEnum.CODE_QUALITY,
                            severity=SeverityEnum.LOW,
                            confidence=1.0,
                            file=filename,
                            line_start=line_start,
                            line_end=line_end,
                            column=getattr(node, "col_offset", None),
                            code_snippet=snippet,
                            description=(
                                f"Function '{node.name}' has {total_args} parameters "
                                f"(exceeds recommended maximum of 5)."
                            ),
                            why_it_matters=(
                                "Functions with too many parameters are difficult to test, "
                                "maintain, and call correctly. Consider grouping parameters into a dataclass or model."
                            ),
                            root_cause="Too many function parameters.",
                            detection_source=DetectionSourceEnum.STATIC,
                            detecting_tool="ast",
                            references=["Clean-Code-Parameter-Limits"],
                        )
                    )
        return issues

    def _check_deep_nesting(
        self, tree: ast.AST, code: str, filename: str
    ) -> List[Issue]:
        """Detects control-flow nesting deeper than 4 levels."""
        issues: List[Issue] = []

        def walk_nesting(node: ast.AST, current_depth: int) -> None:
            nesting_nodes = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith)
            is_nest = isinstance(node, nesting_nodes)
            next_depth = current_depth + 1 if is_nest else current_depth

            if is_nest and next_depth > 4:
                line_start = getattr(node, "lineno", 1)
                line_end = getattr(node, "end_lineno", line_start)
                snippet = self._get_code_snippet(code, line_start, line_start)
                issues.append(
                    Issue(
                        issue_id=self._generate_issue_id("ast", "deep-nesting", line_start),
                        category=CategoryEnum.MAINTAINABILITY,
                        severity=SeverityEnum.LOW,
                        confidence=1.0,
                        file=filename,
                        line_start=line_start,
                        line_end=line_end,
                        column=getattr(node, "col_offset", None),
                        code_snippet=snippet,
                        description=f"Deep control-flow nesting ({next_depth} levels deep > 4).",
                        why_it_matters="Deeply nested blocks increase cognitive complexity and make code hard to read and test.",
                        root_cause="Excessive nesting of conditional and loop blocks.",
                        detection_source=DetectionSourceEnum.STATIC,
                        detecting_tool="ast",
                        references=["Cognitive-Complexity"],
                    )
                )

            # Recurse children
            for child in ast.iter_child_nodes(node):
                # Reset nesting counter for nested function/class definitions
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    walk_nesting(child, 0)
                else:
                    walk_nesting(child, next_depth)

        walk_nesting(tree, 0)
        return issues
