"""Real TypeScript AST static analyzer using tree-sitter-typescript AST parser."""

import logging
from typing import Any, List, Optional
from analyzers.base import BaseAnalyzer
from core.issue_model import CategoryEnum, DetectionSourceEnum, Issue, SeverityEnum

logger = logging.getLogger(__name__)

try:
    import tree_sitter
    import tree_sitter_typescript
    TREE_SITTER_TS_AVAILABLE = True
except ImportError:
    TREE_SITTER_TS_AVAILABLE = False


class TSAnalyzer(BaseAnalyzer):
    """Real TypeScript static analyzer traversing Tree-Sitter AST syntax tree nodes."""

    @property
    def name(self) -> str:
        return "ts_analyzer"

    @property
    def language(self) -> str:
        return "typescript"

    @property
    def analyzer_type(self) -> str:
        return "ast_walker"

    @property
    def tool_name(self) -> str:
        return "tree_sitter_typescript"

    def is_available(self) -> bool:
        return TREE_SITTER_TS_AVAILABLE

    def get_availability_reason(self) -> str:
        return (
            "Tree-Sitter TypeScript AST parser operational"
            if TREE_SITTER_TS_AVAILABLE
            else "tree-sitter or tree-sitter-typescript library not installed"
        )

    def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
        """Parses TypeScript/TSX code into a Tree-Sitter AST and inspects syntax nodes."""
        if not code or not code.strip():
            return []

        if not TREE_SITTER_TS_AVAILABLE:
            logger.warning("TSAnalyzer: tree-sitter-typescript unavailable.")
            return []

        issues: List[Issue] = []
        lines = code.splitlines()

        # 1. Initialize Tree-Sitter Parser for TypeScript / TSX
        try:
            is_tsx = filename.lower().endswith(".tsx")
            ts_lang_fn = (
                tree_sitter_typescript.language_tsx
                if is_tsx
                else tree_sitter_typescript.language_typescript
            )
            lang = tree_sitter.Language(ts_lang_fn())
            parser = tree_sitter.Parser(lang)
            tree = parser.parse(code.encode("utf-8"))
        except Exception as err:
            logger.error(f"TSAnalyzer tree-sitter parse failed: {err}")
            return []

        if not tree or not tree.root_node:
            return []

        # 2. Traverse Tree-Sitter AST
        def visit(node: Any) -> None:
            # Check for syntax error node
            if node.type in ("ERROR", "MISSING"):
                start_line = node.start_point[0] + 1
                col = node.start_point[1]
                snippet = lines[start_line - 1] if 0 <= start_line - 1 < len(lines) else ""
                issues.append(
                    Issue(
                        issue_id=f"ts-syntax-err-L{start_line}",
                        category=CategoryEnum.SYNTAX_ERROR,
                        severity=SeverityEnum.CRITICAL,
                        confidence=1.0,
                        file=filename,
                        line_start=start_line,
                        line_end=start_line,
                        column=col,
                        code_snippet=snippet,
                        description="TypeScript SyntaxError detected in Tree-Sitter AST",
                        why_it_matters="TypeScript code containing syntax errors cannot be compiled or executed.",
                        root_cause=f"Tree-Sitter parser detected {node.type} node",
                        detection_source=DetectionSourceEnum.STATIC,
                        detecting_tool=self.name,
                    )
                )

            # Get node text slice safely
            start_line = node.start_point[0] + 1
            node_text = code[node.start_byte : node.end_byte]
            snippet = lines[start_line - 1] if 0 <= start_line - 1 < len(lines) else ""

            # Rule A: Explicit 'any' type annotation in TypeScript
            if node.type == "type_annotation" and "any" in node_text:
                issues.append(
                    Issue(
                        issue_id=f"ts-any-L{start_line}",
                        category=CategoryEnum.CODE_QUALITY,
                        severity=SeverityEnum.LOW,
                        confidence=0.95,
                        file=filename,
                        line_start=start_line,
                        line_end=start_line,
                        code_snippet=snippet,
                        description="Avoid using explicit 'any' type in TypeScript AST",
                        why_it_matters="'any' disables type checking for that variable, defeating TypeScript guarantees.",
                        root_cause="Tree-Sitter node type_annotation with 'any'",
                        detection_source=DetectionSourceEnum.STATIC,
                        detecting_tool=self.name,
                    )
                )

            # Rule B: Legacy 'var' variable declaration
            elif node.type == "lexical_declaration" and node_text.startswith("var "):
                issues.append(
                    Issue(
                        issue_id=f"ts-var-L{start_line}",
                        category=CategoryEnum.BEST_PRACTICE,
                        severity=SeverityEnum.LOW,
                        confidence=0.95,
                        file=filename,
                        line_start=start_line,
                        line_end=start_line,
                        code_snippet=snippet,
                        description="Use 'const' or 'let' instead of legacy 'var' declaration",
                        why_it_matters="'var' has function scope rather than block scope.",
                        root_cause="Tree-Sitter lexical_declaration starting with 'var'",
                        detection_source=DetectionSourceEnum.STATIC,
                        detecting_tool=self.name,
                    )
                )

            # Rule C: Loose equality operator (== or !=)
            elif node.type == "binary_expression":
                op_child = next((c for c in node.children if c.type in ("==", "!=")), None)
                if op_child:
                    op = op_child.type
                    issues.append(
                        Issue(
                            issue_id=f"ts-loose-eq-L{start_line}",
                            category=CategoryEnum.BEST_PRACTICE,
                            severity=SeverityEnum.LOW,
                            confidence=0.90,
                            file=filename,
                            line_start=start_line,
                            line_end=start_line,
                            code_snippet=snippet,
                            description=f"Use strict equality ('{op}=' or '!==') instead of loose equality '{op}'",
                            why_it_matters="Loose equality performs automatic type coercion.",
                            root_cause=f"Tree-Sitter binary_expression with operator '{op}'",
                            detection_source=DetectionSourceEnum.STATIC,
                            detecting_tool=self.name,
                        )
                    )

            # Rule D: Dangerous eval() call
            elif node.type == "call_expression" and node_text.startswith("eval("):
                issues.append(
                    Issue(
                        issue_id=f"ts-eval-L{start_line}",
                        category=CategoryEnum.SECURITY,
                        severity=SeverityEnum.HIGH,
                        confidence=1.0,
                        file=filename,
                        line_start=start_line,
                        line_end=start_line,
                        code_snippet=snippet,
                        description="Dangerous eval() execution in TypeScript AST",
                        why_it_matters="eval() enables dynamic script execution and cross-site scripting vulnerabilities.",
                        root_cause="Tree-Sitter call_expression to eval",
                        detection_source=DetectionSourceEnum.STATIC,
                        detecting_tool=self.name,
                    )
                )

            # Rule E: console.log(...)
            elif node.type == "call_expression" and "console.log" in node_text:
                issues.append(
                    Issue(
                        issue_id=f"ts-console-L{start_line}",
                        category=CategoryEnum.READABILITY,
                        severity=SeverityEnum.INFORMATIONAL,
                        confidence=0.95,
                        file=filename,
                        line_start=start_line,
                        line_end=start_line,
                        code_snippet=snippet,
                        description="Console log statement present in TypeScript code",
                        why_it_matters="Console logs should be removed prior to production build.",
                        root_cause="Tree-Sitter call_expression console.log",
                        detection_source=DetectionSourceEnum.STATIC,
                        detecting_tool=self.name,
                    )
                )

            # Rule F: innerHTML XSS
            elif node.type == "assignment_expression" and "innerHTML" in node_text:
                issues.append(
                    Issue(
                        issue_id=f"ts-xss-L{start_line}",
                        category=CategoryEnum.SECURITY,
                        severity=SeverityEnum.HIGH,
                        confidence=0.95,
                        file=filename,
                        line_start=start_line,
                        line_end=start_line,
                        code_snippet=snippet,
                        description="Cross-Site Scripting (XSS) risk via innerHTML assignment",
                        why_it_matters="Directly assigning raw strings to innerHTML enables script injection.",
                        root_cause="Tree-Sitter assignment_expression with innerHTML",
                        detection_source=DetectionSourceEnum.STATIC,
                        detecting_tool=self.name,
                    )
                )

            # Visit children recursively
            for child in node.children:
                visit(child)

        visit(tree.root_node)
        return issues
