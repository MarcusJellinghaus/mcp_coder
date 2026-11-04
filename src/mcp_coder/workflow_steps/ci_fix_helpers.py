"""Helpers for the CI fix loop in ``workflow_steps/ci.py``."""

import logging
from pathlib import Path

# Setup logger
logger = logging.getLogger(__name__)


def _read_problem_description(temp_file: Path, fallback_response: str) -> str:
    """Read problem description from temp file or use fallback.

    Args:
        temp_file: Path to the temp problem description file
        fallback_response: Fallback text if file doesn't exist or is empty

    Returns:
        Problem description text
    """
    if temp_file.exists():
        try:
            content = temp_file.read_text(encoding="utf-8").strip()
            temp_file.unlink()  # Delete after reading
            if content:  # Only use file content if not empty
                logger.debug(f"Problem description:\n{content}")
                return content
            logger.debug("Temp file was empty, using fallback")
        except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
            logger.warning(f"Failed to read problem description file: {e}")

    logger.debug("Using analysis response as problem description")
    return fallback_response
