"""AST-based static analyzer for Python structural issues and syntax errors."""

import ast
import logging
from typing import List, Optional, Set

from analyzers.base import BaseAnalyzer
from core.issue_model import CategoryEnum, Issue, SeverityEnum

logger = logging.getLogger(__name__)


class _ASTVisitor(ast.NodeVisitor):
    """Internal AST NodeVisitor for anti-patterns and structural defects."""

    def __init__(
        self, code: str, filename: str, analyzer: BaseAnalyzer
    ) -> None:
        super().__init__()
        self.code = code
        self.filename = filename
        self.analyzer = analyzer
        self.issues: List[Issue] = []
        self._nesting_depth = 0
        self._with_context_calls: Set[int] = set()
        self._class_depth = 0

    def _get_line_bounds(
        self, node: ast.AST
    ) -> tuple[int, int, Optional[int]]:
        line_start = getattr(node, "lineno", 1)
        line_end = getattr(node, "end_lineno", line_start) or line_start
        col = getattr(node, "col_offset", None)
        return line_start, line_end, col

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._class_depth += 1
        self.generic_visit(node)
        self._class_depth -= 1

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                self._with_context_calls.add(id(item.context_expr))
        self._visit_nested_block(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                self._with_context_calls.add(id(item.context_expr))
        self._visit_nested_block(node)

    def visit_If(self, node: ast.If) -> None:
        self._visit_nested_block(node)

    def visit_For(self, node: ast.For) -> None:
        self._visit_nested_block(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_nested_block(node)

    def visit_While(self, node: ast.While) -> None:
        self._visit_nested_block(node)

    def visit_Try(self, node: ast.Try) -> None:
        self._visit_nested_block(node)

    def _visit_nested_block(self, node: ast.AST) -> None:
        self._nesting_depth += 1
        if self._nesting_depth > 4:
            line_start, line_end, col = self._get_line_bounds(node)
            self.issues.append(
                self.analyzer.build_issue(
                    category=CategoryEnum.MAINTAINABILITY,
                    description=(
                        f"Deeply nested control structure "
                        f"(depth: {self._nesting_depth} > 4)"
                    ),
                    why_it_matters=(
                        "Deeply nested control structures significantly "
                        "reduce code readability, increase cognitive "
                        "complexity, and make maintenance error-prone."
                    ),
                    code=self.code,
                    line_start=line_start,
                    line_end=line_end,
                    column=col,
                    file=self.filename,
                    confidence=1.0,
                )
            )
        self.generic_visit(node)
        self._nesting_depth -= 1

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        line_start, line_end, col = self._get_line_bounds(node)
        if node.type is None:
            self.issues.append(
                self.analyzer.build_issue(
                    category=CategoryEnum.ERROR_HANDLING,
                    description=(
                        "Bare 'except:' clause caught without specifying "
                        "exception type"
                    ),
                    why_it_matters=(
                        "Bare except clauses catch all exceptions including "
                        "SystemExit, KeyboardInterrupt, and MemoryError, "
                        "masking critical bugs and hindering debugging."
                    ),
                    code=self.code,
                    line_start=line_start,
                    line_end=line_end,
                    column=col,
                    file=self.filename,
                    confidence=1.0,
                )
            )
        elif len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.issues.append(
                self.analyzer.build_issue(
                    category=CategoryEnum.ERROR_HANDLING,
                    description=(
                        "Empty except block silently suppresses exceptions "
                        "with 'pass'"
                    ),
                    why_it_matters=(
                        "Silently suppressing exceptions without handling or "
                        "logging them conceals runtime errors and makes "
                        "failures difficult to diagnose."
                    ),
                    code=self.code,
                    line_start=line_start,
                    line_end=line_end,
                    column=col,
                    file=self.filename,
                    confidence=0.95,
                )
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        is_open_call = False
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            is_open_call = True
        elif (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "open"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "io"
        ):
            is_open_call = True

        if is_open_call and id(node) not in self._with_context_calls:
            line_start, line_end, col = self._get_line_bounds(node)
            self.issues.append(
                self.analyzer.build_issue(
                    category=CategoryEnum.RESOURCE_MANAGEMENT,
                    description=(
                        "File opened without using a 'with' statement "
                        "context manager"
                    ),
                    why_it_matters=(
                        "Opening files without a context manager can lead to "
                        "unclosed file handles and resource leaks if "
                        "exceptions occur before close() is called."
                    ),
                    code=self.code,
                    line_start=line_start,
                    line_end=line_end,
                    column=col,
                    file=self.filename,
                    confidence=0.9,
                )
            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function_parameters(node)
        saved_depth = self._nesting_depth
        self._nesting_depth = 0
        self.generic_visit(node)
        self._nesting_depth = saved_depth

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function_parameters(node)
        saved_depth = self._nesting_depth
        self._nesting_depth = 0
        self.generic_visit(node)
        self._nesting_depth = saved_depth

    def _check_function_parameters(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        all_args = list(node.args.args) + list(node.args.kwonlyargs)
        if self._class_depth > 0 and all_args:
            first_arg_name = all_args[0].arg
            if first_arg_name in ("self", "cls"):
                all_args = all_args[1:]

        param_count = len(all_args)
        if param_count > 5:
            line_start, line_end, col = self._get_line_bounds(node)
            self.issues.append(
                self.analyzer.build_issue(
                    category=CategoryEnum.MAINTAINABILITY,
                    description=(
                        f"Function '{node.name}' has too many parameters "
                        f"({param_count} > 5)"
                    ),
                    why_it_matters=(
                        "Functions with more than 5 parameters are difficult "
                        "to understand, test, and maintain. Consider "
                        "grouping related parameters into a dataclass, "
                        "pydantic model, or configuration dictionary."
                    ),
                    code=self.code,
                    line_start=line_start,
                    line_end=line_end,
                    column=col,
                    file=self.filename,
                    confidence=1.0,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name == "*":
                line_start, line_end, col = self._get_line_bounds(node)
                module_name = node.module or "module"
                self.issues.append(
                    self.analyzer.build_issue(
                        category=CategoryEnum.BEST_PRACTICE,
                        description=(
                            f"Wildcard import 'from {module_name} import *' "
                            "pollutes namespace"
                        ),
                        why_it_matters=(
                            "Star imports pollute the local namespace with "
                            "unknown identifiers, making code hard to read "
                            "and increasing the risk of name collisions."
                        ),
                        code=self.code,
                        line_start=line_start,
                        line_end=line_end,
                        column=col,
                        file=self.filename,
                        confidence=1.0,
                    )
                )
        self.generic_visit(node)


class ASTAnalyzer(BaseAnalyzer):
    """Safe Python AST-based static analyzer for structural issues."""

    @property
    def name(self) -> str:
        return "ast_analyzer"

    def analyze(
        self, code: str, filename: str = "submitted_snippet"
    ) -> List[Issue]:
        """Parses and analyzes code using Python standard library AST."""
        if not code or not code.strip():
            return []

        try:
            tree = ast.parse(code, filename=filename)
        except SyntaxError as e:
            line_num = max(1, e.lineno or 1)
            col_num = e.offset - 1 if e.offset and e.offset > 0 else 0
            return [
                self.build_issue(
                    category=CategoryEnum.SYNTAX_ERROR,
                    description=f"SyntaxError: {e.msg}",
                    why_it_matters=(
                        "Syntax errors prevent Python code from compiling "
                        "or executing."
                    ),
                    code=code,
                    line_start=line_num,
                    line_end=line_num,
                    column=col_num,
                    severity=SeverityEnum.CRITICAL,
                    confidence=1.0,
                    file=filename,
                )
            ]
        except Exception as e:
            logger.error(
                f"AST parsing failed for {filename}: {e}", exc_info=True
            )
            return []

        try:
            visitor = _ASTVisitor(code, filename, self)
            visitor.visit(tree)
            return visitor.issues
        except Exception as e:
            logger.error(f"AST analysis visitor error: {e}", exc_info=True)
            return []
