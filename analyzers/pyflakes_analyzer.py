"""Pyflakes static analyzer wrapper for defects and unused symbols."""

import ast
import logging
from typing import Dict, List

from analyzers.base import BaseAnalyzer
from core.issue_model import CategoryEnum, Issue

logger = logging.getLogger(__name__)

try:
    import pyflakes.checker
    import pyflakes.messages
    PYFLAKES_AVAILABLE = True
except ImportError:
    PYFLAKES_AVAILABLE = False
    logger.warning("pyflakes library is not available.")


# Mapping of Pyflakes message class names to Issue CategoryEnum
MESSAGE_CATEGORY_MAP: Dict[str, CategoryEnum] = {
    "UndefinedName": CategoryEnum.RUNTIME_PROBLEM,
    "UndefinedExport": CategoryEnum.RUNTIME_PROBLEM,
    "UndefinedLocal": CategoryEnum.RUNTIME_PROBLEM,
    "ReturnOutsideFunction": CategoryEnum.RUNTIME_PROBLEM,
    "YieldOutsideFunction": CategoryEnum.RUNTIME_PROBLEM,
    "BreakOutsideLoop": CategoryEnum.RUNTIME_PROBLEM,
    "ContinueOutsideLoop": CategoryEnum.RUNTIME_PROBLEM,
    "DefaultExceptNotLast": CategoryEnum.RUNTIME_PROBLEM,
    "AssertTuple": CategoryEnum.LOGICAL_BUG,
    "IfTuple": CategoryEnum.LOGICAL_BUG,
    "DuplicateArgument": CategoryEnum.LOGICAL_BUG,
    "MultiValueRepeatedKeyLiteral": CategoryEnum.LOGICAL_BUG,
    "MultiValueRepeatedKeyVariable": CategoryEnum.LOGICAL_BUG,
    "UnusedImport": CategoryEnum.CODE_QUALITY,
    "UnusedVariable": CategoryEnum.CODE_QUALITY,
    "UnusedAnnotation": CategoryEnum.CODE_QUALITY,
    "ImportShadowedByLoopVar": CategoryEnum.CODE_QUALITY,
    "RedefinedWhileUnused": CategoryEnum.CODE_QUALITY,
    "ImportStarNotPermitted": CategoryEnum.BEST_PRACTICE,
    "ImportStarUsage": CategoryEnum.BEST_PRACTICE,
    "ImportStarUsed": CategoryEnum.BEST_PRACTICE,
    "DoctestSyntaxError": CategoryEnum.SYNTAX_ERROR,
    "ForwardAnnotationSyntaxError": CategoryEnum.SYNTAX_ERROR,
    "FutureFeatureNotDefined": CategoryEnum.RUNTIME_PROBLEM,
    "LateFutureImport": CategoryEnum.BEST_PRACTICE,
    "PercentFormatInvalidFormat": CategoryEnum.RUNTIME_PROBLEM,
    "PercentFormatMixedPositionalAndNamed": CategoryEnum.LOGICAL_BUG,
    "PercentFormatMissingArgument": CategoryEnum.RUNTIME_PROBLEM,
    "PercentFormatPositionalCountMismatch": CategoryEnum.LOGICAL_BUG,
    "PercentFormatUnsupportedFormatCharacter": CategoryEnum.RUNTIME_PROBLEM,
    "StringDotFormatInvalidFormat": CategoryEnum.RUNTIME_PROBLEM,
    "StringDotFormatMissingArgument": CategoryEnum.RUNTIME_PROBLEM,
    "StringDotFormatExtraNamedArguments": CategoryEnum.LOGICAL_BUG,
    "StringDotFormatExtraPositionalArguments": CategoryEnum.LOGICAL_BUG,
}

MESSAGE_WHY_MAP: Dict[str, str] = {
    "UndefinedName": (
        "Referencing undefined variables causes an immediate NameError "
        "when executed at runtime."
    ),
    "UndefinedLocal": (
        "Referencing a local variable before assignment causes an "
        "UnboundLocalError at runtime."
    ),
    "UndefinedExport": (
        "Exporting undefined symbols in __all__ leads to AttributeError "
        "or ImportError for importers."
    ),
    "UnusedImport": (
        "Unused imports clutter module namespace, introduce unnecessary "
        "loading overhead, and obscure dependencies."
    ),
    "UnusedVariable": (
        "Assigning to variables that are never read wastes resources and "
        "often indicates incomplete logic or forgotten values."
    ),
    "UnusedAnnotation": (
        "Unused type annotations have no effect and may indicate obsolete "
        "or dead code."
    ),
    "ImportShadowedByLoopVar": (
        "Loop variables shadowing imported modules or functions can cause "
        "unexpected runtime name collisions."
    ),
    "RedefinedWhileUnused": (
        "Redefining a variable or function before its previous value was used "
        "indicates dead code or conflicting assignments."
    ),
    "AssertTuple": (
        "assert (condition, message) is always truthy in Python, causing "
        "the assertion to never fail."
    ),
    "IfTuple": (
        "if (condition,) evaluates to a non-empty tuple which is always "
        "truthy, leading to unintended control flow."
    ),
    "DuplicateArgument": (
        "Defining duplicate parameter names in a function signature causes "
        "ambiguity and syntax/runtime errors."
    ),
    "ReturnOutsideFunction": (
        "'return' statements outside functions cause a SyntaxError during "
        "execution."
    ),
    "YieldOutsideFunction": (
        "'yield' statements outside functions cause a SyntaxError during "
        "execution."
    ),
    "BreakOutsideLoop": (
        "'break' statements outside loop constructs cause a SyntaxError "
        "at runtime."
    ),
    "ContinueOutsideLoop": (
        "'continue' statements outside loop constructs cause a SyntaxError "
        "at runtime."
    ),
    "ImportStarUsed": (
        "Wildcard imports pollute the local namespace and obscure where "
        "names originated."
    ),
}


class PyflakesAnalyzer(BaseAnalyzer):
    """Static analyzer wrapping Pyflakes."""

    @property
    def name(self) -> str:
        return "pyflakes"

    def analyze(
        self, code: str, filename: str = "submitted_snippet"
    ) -> List[Issue]:
        """Runs Pyflakes analysis in-memory without executing user code."""
        if not PYFLAKES_AVAILABLE or not code or not code.strip():
            return []

        try:
            tree = ast.parse(code, filename=filename)
        except SyntaxError:
            # Syntax errors are handled and reported primarily by ASTAnalyzer
            return []
        except Exception as e:
            logger.error(f"Pyflakes AST parse error: {e}", exc_info=True)
            return []

        issues: List[Issue] = []
        try:
            checker = pyflakes.checker.Checker(tree, filename=filename)
            for msg in checker.messages:
                msg_type = type(msg).__name__
                category = MESSAGE_CATEGORY_MAP.get(
                    msg_type, CategoryEnum.CODE_QUALITY
                )
                why_it_matters = MESSAGE_WHY_MAP.get(
                    msg_type,
                    "This static defect impacts code reliability and quality.",
                )

                description = msg.message % msg.message_args

                line_num = max(1, getattr(msg, "lineno", 1))
                col_offset = getattr(msg, "col", None)

                issues.append(
                    self.build_issue(
                        category=category,
                        description=description,
                        why_it_matters=why_it_matters,
                        code=code,
                        line_start=line_num,
                        line_end=line_num,
                        column=col_offset,
                        confidence=1.0,
                        file=filename,
                        references=["pyflakes", msg_type],
                    )
                )
        except Exception as e:
            logger.error(
                f"Pyflakes error on {filename}: {e}", exc_info=True
            )

        return issues
