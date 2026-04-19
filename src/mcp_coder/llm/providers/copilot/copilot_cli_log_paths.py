"""Log path utilities for Copilot CLI stream logging.

Generates unique log file paths in the copilot-sessions/ subdirectory,
following the same pattern as Claude's log paths.
"""

from datetime import datetime
from pathlib import Path

from ...log_utils import DEFAULT_LOGS_DIR, sanitize_branch_identifier

COPILOT_SESSIONS_SUBDIR: str = "copilot-sessions"


def get_stream_log_path(
    logs_dir: str | None = None,
    cwd: str | None = None,
    branch_name: str | None = None,
) -> Path:
    """Generate unique path for Copilot JSONL log file.

    Same pattern as Claude's log paths but in copilot-sessions/ subdirectory.
    Filename: session_YYYYMMDD_HHMMSS_NNNNNN[_BRANCH].ndjson

    Args:
        logs_dir: Base logs directory (default: 'logs' in cwd or project root)
        cwd: Working directory context
        branch_name: Optional git branch name to include in filename

    Returns:
        Path to the stream log file
    """
    # Determine base directory
    if logs_dir:
        base_dir = Path(logs_dir)
    elif cwd:
        base_dir = Path(cwd) / DEFAULT_LOGS_DIR
    else:
        base_dir = Path.cwd() / DEFAULT_LOGS_DIR

    # Create copilot-sessions subdirectory
    session_dir = base_dir / COPILOT_SESSIONS_SUBDIR
    session_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename with timestamp and optional branch identifier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    branch_id = sanitize_branch_identifier(branch_name)

    if branch_id:
        filename = f"session_{timestamp}_{branch_id}.ndjson"
    else:
        filename = f"session_{timestamp}.ndjson"

    return session_dir / filename
