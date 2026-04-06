"""Formatters package providing code formatting utilities."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..utils.pyproject_config import get_formatter_config
from .black_formatter import format_with_black
from .config_reader import check_line_length_conflicts, read_formatter_config
from .isort_formatter import format_with_isort
from .models import FormatterResult

logger = logging.getLogger(__name__)


def format_code(
    project_root: Path,
    formatters: Optional[List[str]] = None,
    target_dirs: Optional[List[str]] = None,
) -> Dict[str, FormatterResult]:
    """Run multiple formatters using analysis-proven patterns and return combined results.

    Args:
        project_root: Root directory of the project
        formatters: Optional list of formatters to run (["black", "isort"]).
                   Defaults to both if not specified.
        target_dirs: Optional list of directories to format, defaults to auto-detection

    Returns:
        Dictionary mapping formatter names to FormatterResult objects
    """
    # Check for line-length conflicts before formatting
    _check_line_length_conflict(project_root)

    # Default to both formatters if not specified
    if formatters is None:
        formatters = ["black", "isort"]

    results = {}

    # Run each requested formatter
    for formatter_name in formatters:
        if formatter_name == "black":
            results["black"] = format_with_black(project_root, target_dirs)
            if not results["black"].success:
                logger.info(
                    "%s formatting failed: %s",
                    results["black"].formatter_name,
                    results["black"].error_message,
                )
                break
        elif formatter_name == "isort":
            results["isort"] = format_with_isort(project_root, target_dirs)
            if not results["isort"].success:
                logger.info(
                    "%s formatting failed: %s",
                    results["isort"].formatter_name,
                    results["isort"].error_message,
                )
                break

    return results


def _check_line_length_conflict(project_root: Path) -> None:
    """Warn about most common config conflict identified in analysis (~10 lines).

    Args:
        project_root: Root directory to check for pyproject.toml
    """
    config = get_formatter_config(project_root)
    black_length = config.get("black", {}).get("line-length", 88)  # Black default
    isort_length = config.get("isort", {}).get(
        "line_length", 88
    )  # isort uses underscore

    if black_length != isort_length:
        logger.warning(
            "line-length mismatch: black=%s, isort=%s",
            black_length,
            isort_length,
        )


__all__ = [
    "FormatterResult",
    "format_code",
    "format_with_black",
    "format_with_isort",
    "read_formatter_config",
    "check_line_length_conflicts",
]
