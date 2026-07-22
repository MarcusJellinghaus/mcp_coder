"""Shared constants for workflow_steps.

Generic commit/CI tuning constants live here (the workflow-agnostic middle
tier), so steps can import them downward without reaching up into a specific
workflow package. `implement/constants.py` re-exports the ones its own
staying-in-`implement` code still uses.
"""

from __future__ import annotations

# Directory paths
PR_INFO_DIR = "pr_info"
COMMIT_MESSAGE_FILE = f"{PR_INFO_DIR}/.commit_message.txt"
