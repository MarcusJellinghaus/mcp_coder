"""Log path utilities for Claude Code CLI stream logging.

Extracted from claude_code_cli.py to keep file sizes manageable.
Shared utilities (sanitize_branch_identifier, DEFAULT_LOGS_DIR) live in
mcp_coder.llm.log_utils and are re-exported here for backwards compatibility.
"""

from datetime import datetime
from pathlib import Path

from ...log_utils import DEFAULT_LOGS_DIR, sanitize_branch_identifier

__all__ = [
    "DEFAULT_LOGS_DIR",
    "sanitize_branch_identifier",
    "CLAUDE_SESSIONS_SUBDIR",
    "get_stream_log_path",
]

CLAUDE_SESSIONS_SUBDIR = "claude-sessions"


def get_stream_log_path(
    logs_dir: str | None = None,
    cwd: str | None = None,
    branch_name: str | None = None,
) -> Path:
    """Generate a unique path for stream log file.

    The filename includes:
    - Timestamp for uniqueness
    - Git branch identifier (max 10 chars) for context (if provided)

    Example filenames:
    - session_20260201_123456_789012_fix.ndjson (branch: fix/improve-logging)
    - session_20260201_123456_789012_123.ndjson (branch: 123-feature-name)
    - session_20260201_123456_789012.ndjson (no branch provided)

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

    # Create claude-sessions subdirectory
    session_dir = base_dir / CLAUDE_SESSIONS_SUBDIR
    session_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename with timestamp and optional branch identifier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    branch_id = sanitize_branch_identifier(branch_name)

    if branch_id:
        filename = f"session_{timestamp}_{branch_id}.ndjson"
    else:
        filename = f"session_{timestamp}.ndjson"

    return session_dir / filename
