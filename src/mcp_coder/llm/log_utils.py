"""Shared log utilities for LLM providers.

Provider-agnostic utilities for log path generation, extracted from
claude_code_cli_log_paths.py so they can be reused by multiple providers.
"""

import re

# Default logs directory for stream output
DEFAULT_LOGS_DIR: str = "logs"


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
