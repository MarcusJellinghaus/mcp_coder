"""Crash logging utility using faulthandler.

Provides enable_crash_logging() which enables Python's faulthandler with a
persistent per-process crash log file. This captures native-level tracebacks
on crash (SIGSEGV, SIGABRT, etc.) for post-mortem diagnostics.
"""

import faulthandler
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_state: dict[str, Any] = {"path": None, "handle": None}


def enable_crash_logging(project_dir: Path, command_name: str) -> Path | None:
    """Enable faulthandler with a persistent per-process crash log.

    Creates a log file under ``{project_dir}/logs/faulthandler/`` and enables
    faulthandler to write tracebacks there on fatal signals. The call is
    idempotent — a second call returns the existing path without re-enabling.

    Args:
        project_dir: Project root directory for log storage.
        command_name: CLI command name included in the filename.

    Returns:
        Path to the crash log file, or None if setup failed.
    """
    if _state["path"] is not None:
        path: Path = _state["path"]
        return path

    try:
        log_dir = project_dir / "logs" / "faulthandler"
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().isoformat().replace(":", "-").split(".")[0]
        pid = os.getpid()
        filename = f"crash_{command_name}_{timestamp}_{pid}.log"
        crash_path = log_dir / filename

        handle = open(crash_path, "w", encoding="utf-8", buffering=1)  # noqa: SIM115
        _state["handle"] = handle
        _state["path"] = crash_path

        faulthandler.enable(file=handle, all_threads=True)
        logger.debug("Crash logging enabled: %s", crash_path)
        return crash_path
    except Exception:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to enable crash logging", exc_info=True)
        return None


def _reset_for_testing() -> None:
    """Close the active handle and clear module state. Test-only helper."""
    if _state["handle"] is not None:
        _state["handle"].close()
    _state["path"] = None
    _state["handle"] = None
