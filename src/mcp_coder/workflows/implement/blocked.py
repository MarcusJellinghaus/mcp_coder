"""Blocked-marker handling for the implement workflow.

The agent writes pr_info/.blocked.txt when something stops it from completing
a task. This module reads that marker and removes it.
"""

import logging
from pathlib import Path

from .constants import BLOCKED_FILE

logger = logging.getLogger(__name__)

BLOCKED_REASON_MAX_CHARS = 500
BLOCKED_REASON_FALLBACK = "Agent reported being blocked but gave no reason"


def read_and_clear_blocked(project_dir: Path) -> str | None:
    """Read the blocked marker and delete it.

    Args:
        project_dir: Path to the project directory

    Returns:
        None if no marker exists. Otherwise the marker text collapsed to a
        single line (truncated to BLOCKED_REASON_MAX_CHARS), or
        BLOCKED_REASON_FALLBACK when the marker is empty or whitespace only -
        an empty marker still means blocked. Collapsing keeps the reason from
        breaking the markdown failure comment it is rendered into.
        The file is deleted in every case where it exists, and the reason is
        logged before the delete so the cleanup call sites - which discard the
        return value - still leave a trace. Never raises: callers invoke this
        from their own `finally`, where an exception would replace the original
        LLM failure.
    """
    blocked_path = project_dir / BLOCKED_FILE
    if not blocked_path.exists():
        return None

    reason = BLOCKED_REASON_FALLBACK
    try:
        raw = blocked_path.read_text(encoding="utf-8", errors="replace")
        # Collapse before truncating: the reason becomes one markdown line in the
        # failure comment, and the char budget should be spent on content.
        text = " ".join(raw.split())
        if len(text) > BLOCKED_REASON_MAX_CHARS:
            reason = text[:BLOCKED_REASON_MAX_CHARS] + "..."
        elif text:
            reason = text
        logger.warning("Blocked marker found: %s", reason)
    # errors="replace" is what handles bad bytes; ValueError here is belt-and-
    # braces in case a future edit drops it - this function must never raise.
    except (OSError, ValueError) as e:
        logger.warning(f"Could not read blocked marker: {e}")
    finally:
        # Delete even if the read failed - a stale marker breaks the next run.
        try:
            blocked_path.unlink(missing_ok=True)
        except OSError as e:
            logger.warning(f"Could not delete blocked marker: {e}")

    return reason
