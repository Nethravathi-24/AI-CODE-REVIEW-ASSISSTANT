"""Input validation module for AI Code Review Assistant."""

import logging
from typing import Optional, Tuple

from services.config_service import get_settings

logger = logging.getLogger(__name__)


def validate_input(
    code: str, file_bytes: Optional[bytes] = None
) -> Tuple[bool, Optional[str]]:
    """Validates raw input code against size, empty, and character boundaries.

    Args:
        code: Source code text to validate.
        file_bytes: Optional raw bytes if uploaded from a file.

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    settings = get_settings()

    if file_bytes is not None:
        size_kb = len(file_bytes) / 1024.0
        if size_kb > settings.MAX_FILE_SIZE_KB:
            msg = (
                f"File size ({size_kb:.1f} KB) exceeds maximum limit "
                f"of {settings.MAX_FILE_SIZE_KB} KB."
            )
            logger.warning(msg)
            return False, msg

    if not code or not code.strip():
        msg = "Input code is empty. Please provide valid source code."
        logger.info(msg)
        return False, msg

    if len(code) > settings.MAX_CODE_CHARS:
        msg = (
            f"Input code length ({len(code)} characters) exceeds maximum "
            f"limit of {settings.MAX_CODE_CHARS} characters."
        )
        logger.warning(msg)
        return False, msg

    return True, None
