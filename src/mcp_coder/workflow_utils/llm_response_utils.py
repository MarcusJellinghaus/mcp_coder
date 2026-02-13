<<<<<<< HEAD
"""LLM response processing utilities.

This module provides shared utilities for processing LLM responses,
including footer stripping used by both commit and PR workflows.
"""

import re
=======
"""LLM response processing utilities.

This module provides shared utilities for processing LLM responses,
including footer stripping used by both commit and PR workflows.
"""

import re


def strip_claude_footers(message: str) -> str:
    """Remove Claude Code footer lines from text (commit messages, PR bodies, etc.).

    Removes lines starting with 🤖 (robot emoji) and Co-Authored-By patterns
    with case-insensitive matching for 'Claude <model>? <noreply@anthropic.com>'
    from the end of the message. Also cleans up trailing blank lines.

    Supports model name variations: Claude Opus 4.5, Claude Sonnet 4.5, Claude (no model).
    Preserves non-Claude co-author footers (e.g., AutoRunner Bot).

    Args:
        message: The text to clean (commit message, PR body, etc.)

    Returns:
        Cleaned text with Claude footers removed
    """
    if not message:
        return ""

    # Split message into lines
    lines = message.split("\n")

    # Compile regex pattern for Co-Authored-By (case-insensitive)
    co_authored_pattern = re.compile(
        r"^Co-Authored-By:\s*Claude.*<noreply@anthropic\.com>$", re.IGNORECASE
    )

    # Work backwards from the end, removing footers and empty lines
    while lines:
        last_line = lines[-1].strip()

        # Check if line is a footer pattern or empty
        if (
            last_line.startswith("🤖")
            or co_authored_pattern.match(last_line)
            or last_line == ""
        ):
            lines.pop()
        else:
            break

    # Join lines back together
    return "\n".join(lines)
>>>>>>> 04d14b7 (refactor: move and enhance strip_claude_footers() to shared module)
