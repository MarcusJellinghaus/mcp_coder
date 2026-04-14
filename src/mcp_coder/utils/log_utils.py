"""Logging utilities shim — re-exports from mcp_coder_utils.

This module delegates to mcp_coder_utils.log_utils and mcp_coder_utils.redaction,
adding app-specific third-party log suppression in setup_logging().
"""

import logging
from typing import Optional

from mcp_coder_utils.log_utils import (
    OUTPUT,
    STANDARD_LOG_FIELDS,
    CleanFormatter,
    ExtraFieldsFormatter,
    log_function_call,
)
from mcp_coder_utils.log_utils import setup_logging as _upstream_setup_logging
from mcp_coder_utils.redaction import REDACTED_VALUE, RedactableDict

__all__ = [
    "OUTPUT",
    "STANDARD_LOG_FIELDS",
    "CleanFormatter",
    "ExtraFieldsFormatter",
    "log_function_call",
    "setup_logging",
    "REDACTED_VALUE",
    "RedactableDict",
]


def setup_logging(log_level: str, log_file: Optional[str] = None) -> None:
    """Configure logging with app-specific third-party log suppression."""
    _upstream_setup_logging(log_level, log_file)
    # App-specific: suppress noisy third-party loggers
    logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
    logging.getLogger("github.Requester").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
