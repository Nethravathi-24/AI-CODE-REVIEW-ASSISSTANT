"""Real JavaScript AST static analyzer using esprima AST parser."""

import logging
from typing import Any, List, Optional
from analyzers.base import BaseAnalyzer
from core.issue_model import CategoryEnum, DetectionSourceEnum, Issue, SeverityEnum

logger = logging.getLogger(__name__)

try:
    import esprima
    ESPRIMA_AVAILABLE = True
except ImportError:
    ESPRIMA_AVAILABLE = False


class JSAnalyzer(BaseAnalyzer):
    """Real JavaScript AST static analyzer inspecting ECMAScript syntax tree nodes."""

    @property
    def name(self) -> str:
        return "js_analyzer"

    @property
    def language(self) -> str:
        return "javascript"

    @property
    def analyzer_type(self) -> str:
        return "ast_walker"

    @property
    def tool_name(self) -> str:
        return "esprima"

    def is_available(self) -> bool:
        return ESPRIMA_AVAILABLE

    def get_availability_reason(self) -> str:
        return "Esprima ECMAScript AST parser operational" if ESPRIMA_AVAILABLE else "esprima library not installed"

    def analyze(self, code: str, filename: str = "submitted_snippet") -> List[Issue]:
        """Parses JavaScript code into an AST and traverses nodes for static findings."""
        if not code or not code.strip():
            return []

        if not ESPRIMA_AVAILABLE:
            logger.warning("JSAnalyzer: esprima parser unavailable.")
            return []

        issues: List[Issue] = []

        # 1. Parse AST with esprima
        tree = None
        try:
            tree = esprima.parseScript(code, loc=True, tolerant=True)
        except Exception as err:
            try:
                tree = esprima.parseModule(code, loc=True, tolerant=True)
            except Exception as mod_err:
                line_no = getattr(mod_err, "lineNumber", 1)
                col = getattr(mod_err, "column", 0)
                msg = getattr(mod_err, "description", str(mod_err))
                lines = code.splitlines()
                snippet = lines[line_no - 1] if 0 <= line_no - 1 < len(lines) else ""

                return [
                    Issue(
                        issue_id=f"js-syntax-err-L{line_no}",
                        category=CategoryEnum.SYNTAX_ERROR,
                        severity=SeverityEnum.CRITICAL,
                        confidence=1.0,
                        file=filename,
                        line_start=line_no,
                        line_end=line_no,
                        column=col,
                        code_snippet=snippet,
                        description=f"JavaScript SyntaxError: {msg}",
                        why_it_matters="JavaScript code containing syntax errors cannot be executed or analyzed.",
                        root_cause=f"Esprima AST parser raised SyntaxError: {msg}",
                        detection_source=DetectionSourceEnum.STATIC,
                        detecting_tool=self.name,
                    )
                ]

        if not tree:
            return []

        # 2. Traverse AST nodes recursively
        lines = code.splitlines()

        def visit_node(node: Any) -> None:
            if not isinstance(node, esprima.nodes.Node):
                return

            loc = getattr(node, "loc", None)
            line_no = loc.start.line if loc and hasattr(loc, "start") else 1
            snippet = lines[line_no - 1] if 0 <= line_no - 1 < len(lines) else ""

            node_type = getattr(node, "type", "")

            # Rule A: Legacy 'var' variable declaration
            if node_type == "VariableDeclaration":
                kind = getattr(node, "kind", "")
                if kind == "var":
                    issues.append(
                        Issue(
                            issue_id=f"js-var-L{line_no}",
                            category=CategoryEnum.BEST_PRACTICE,
                            severity=SeverityEnum.LOW,
                            confidence=0.95,
                            file=filename,
                            line_start=line_no,
                            line_end=line_no,
                            code_snippet=snippet,
                            description="Use 'const' or 'let' instead of legacy 'var' declaration",
                            why_it_matters="'var' has function scope and variable hoisting, causing scope confusion.",
                            root_cause="AST VariableDeclaration with kind='var'",
                            detection_source=DetectionSourceEnum.STATIC,
                            detecting_tool=self.name,
                        )
                    )

            # Rule B: Loose equality operator (== or !=)
            elif node_type == "BinaryExpression":
                op = getattr(node, "operator", "")
                if op in ("==", "!="):
                    issues.append(
                        Issue(
                            issue_id=f"js-loose-eq-L{line_no}",
                            category=CategoryEnum.BEST_PRACTICE,
                            severity=SeverityEnum.LOW,
                            confidence=0.90,
                            file=filename,
                            line_start=line_no,
                            line_end=line_no,
                            code_snippet=snippet,
                            description=f"Use strict equality ('{op}=' or '!==') instead of loose equality '{op}'",
                            why_it_matters="Loose equality performs automatic type coercion, leading to comparison bugs.",
                            root_cause=f"AST BinaryExpression with operator='{op}'",
                            detection_source=DetectionSourceEnum.STATIC,
                            detecting_tool=self.name,
                        )
                    )

            # Rule C: Function calls (eval, console.log, document.write)
            elif node_type == "CallExpression":
                callee = getattr(node, "callee", None)
                if callee:
                    callee_type = getattr(callee, "type", "")

                    # eval(...)
                    if callee_type == "Identifier" and getattr(callee, "name", "") == "eval":
                        issues.append(
                            Issue(
                                issue_id=f"js-eval-L{line_no}",
                                category=CategoryEnum.SECURITY,
                                severity=SeverityEnum.HIGH,
                                confidence=1.0,
                                file=filename,
                                line_start=line_no,
                                line_end=line_no,
                                code_snippet=snippet,
                                description="Dangerous eval() execution in JavaScript AST",
                                why_it_matters="Evaluating dynamic strings as code enables remote code execution vulnerabilities.",
                                root_cause="AST CallExpression with callee='eval'",
                                detection_source=DetectionSourceEnum.STATIC,
                                detecting_tool=self.name,
                            )
                        )

                    # console.log(...)
                    elif (
                        callee_type == "MemberExpression"
                        and getattr(getattr(callee, "object", None), "name", "") == "console"
                        and getattr(getattr(callee, "property", None), "name", "") == "log"
                    ):
                        issues.append(
                            Issue(
                                issue_id=f"js-console-L{line_no}",
                                category=CategoryEnum.READABILITY,
                                severity=SeverityEnum.INFORMATIONAL,
                                confidence=0.95,
                                file=filename,
                                line_start=line_no,
                                line_end=line_no,
                                code_snippet=snippet,
                                description="Console log debug statement present",
                                why_it_matters="Debug console logs should be removed prior to production deployment.",
                                root_cause="AST CallExpression to console.log",
                                detection_source=DetectionSourceEnum.STATIC,
                                detecting_tool=self.name,
                            )
                        )

            # Rule D: innerHTML DOM assignment XSS
            elif node_type == "AssignmentExpression":
                left = getattr(node, "left", None)
                if left and getattr(left, "type", "") == "MemberExpression":
                    prop = getattr(left, "property", None)
                    prop_name = getattr(prop, "name", "") if prop else ""
                    if prop_name == "innerHTML":
                        issues.append(
                            Issue(
                                issue_id=f"js-xss-L{line_no}",
                                category=CategoryEnum.SECURITY,
                                severity=SeverityEnum.HIGH,
                                confidence=0.95,
                                file=filename,
                                line_start=line_no,
                                line_end=line_no,
                                code_snippet=snippet,
                                description="Cross-Site Scripting (XSS) risk via innerHTML assignment",
                                why_it_matters="Directly assigning HTML strings can execute malicious script payloads.",
                                root_cause="AST AssignmentExpression to innerHTML property",
                                detection_source=DetectionSourceEnum.STATIC,
                                detecting_tool=self.name,
                            )
                        )

            # Recursively traverse children
            for key, val in node.__dict__.items():
                if isinstance(val, esprima.nodes.Node):
                    visit_node(val)
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, esprima.nodes.Node):
                            visit_node(item)

        visit_node(tree)
        return issues
