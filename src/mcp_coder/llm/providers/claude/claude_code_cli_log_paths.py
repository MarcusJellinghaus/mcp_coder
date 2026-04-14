"""Log path utilities for Claude Code CLI stream logging.

Extracted from claude_code_cli.py to keep file sizes manageable.
"""

import re
from datetime import datetime
from pathlib import Path

# Default logs directory for stream output
DEFAULT_LOGS_DIR = "logs"

CLAUDE_SESSIONS_SUBDIR = "claude-sessions"


def sanitize_branch_identifier(branch_name: str | None) -> str:
    """Sanitize a branch name into a short identifier for filenames.

    Extracts a meaningful short identifier from the branch name:
    - For branches like '123-feature-name', returns '123'
    - For branches like 'fix/improve-logging', returns 'fix'
    - Sanitizes special characters
    - Returns max 10 characters

    Args:
        branch_name: Full branch name (e.g., 'fix/improve-logging')

    Returns:
        Sanitized identifier (max 10 chars), or empty string if None/empty

    Example:
        >>> sanitize_branch_identifier('123-feature-name')
        '123'
        >>> sanitize_branch_identifier('fix/improve-logging')
        'fix'
        >>> sanitize_branch_identifier(None)
        ''
    """
    if not branch_name:
        return ""

    branch = branch_name.strip()
    if not branch or branch == "HEAD":
        return ""

    # Extract first meaningful part:
    # - Split on / (e.g., 'fix/improve-logging' -> 'fix')
    # - Split on - (e.g., '123-feature-name' -> '123')
    parts_slash = branch.split("/")
    parts_dash = branch.split("-")

    # Prefer numeric issue IDs if present at the start
    first_dash = parts_dash[0] if parts_dash else ""
    first_slash = parts_slash[0] if parts_slash else ""

    # If first dash part is numeric (issue ID), use it
    if first_dash and first_dash.isdigit():
        identifier = first_dash
    # Otherwise use the first slash part (e.g., 'fix', 'feat', 'feature')
    elif first_slash:
        identifier = first_slash
    else:
        identifier = branch

    # Sanitize: keep only alphanumeric and underscore
    identifier = re.sub(r"[^a-zA-Z0-9_]", "", identifier)

    # Limit to 10 characters
    return identifier[:10]


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
