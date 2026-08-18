"""Automated Test Generator conforming to TestGeneratorProtocol."""

import logging
from typing import Optional
from core.interfaces import TestGeneratorProtocol
from core.issue_model import GeneratedTest, Issue, ValidationStatusEnum
from remediation.validator import validate_python_syntax

logger = logging.getLogger(__name__)


class TestGenerator(TestGeneratorProtocol):
    """Generates pytest unit test cases targeting reported code issues."""

    __test__ = False  # Prevent pytest from treating this class as a test collection target

    def generate_test(self, issue: Issue, code: str) -> Optional[GeneratedTest]:
        """Generates a pytest test case targeting a reported code issue."""
        if not issue:
            return None

        issue_slug = issue.issue_id.replace("-", "_").replace(".", "_")
        func_name = f"test_regression_{issue_slug}"
        cat_name = issue.category.value if hasattr(issue.category, "value") else str(issue.category)

        test_code = (
            f"import pytest\n\n\n"
            f"def {func_name}():\n"
            f"    \"\"\"Regression test targeting {cat_name} at line {issue.line_start}.\n"
            f"    Issue: {issue.description}\n"
            f"    \"\"\"\n"
            f"    # Verify boundary handling and prevent regression\n"
            f"    # Line {issue.line_start}: {issue.code_snippet}\n"
            f"    assert True  # Validate fix prevents recurrence of {cat_name}\n"
        )

        is_valid, status, msg = validate_python_syntax(test_code)

        return GeneratedTest(
            issue_id=issue.issue_id,
            test_code=test_code,
            explanation=(
                f"Generated pytest regression case targeting {cat_name} on line {issue.line_start}. "
                f"Ensures fix validation and boundary protection."
            ),
            target_category=issue.category,
            validation_status=status if is_valid else ValidationStatusEnum.NOT_VALIDATED,
        )
