"""Pre-creation steps for the create-pr workflow.

Runs before the PR summary is generated. Kept out of ``core.py`` so that
module stays under the CI file-size gate. Must not import ``create_pr.core``.
"""

import logging
from pathlib import Path

from mcp_coder.mcp_workspace_git import get_current_branch_name, needs_rebase
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.workflow_steps.rebase import _attempt_rebase_and_push
from mcp_coder.workflow_utils.base_branch import detect_base_branch

logger = logging.getLogger(__name__)


def _rebase_if_needed(project_dir: Path) -> None:
    """Rebase onto the base branch and push, only when the branch is behind.

    Never fails the workflow: a missing base, a ``needs_rebase`` error, a
    failed rebase or any exception is logged and skipped. A resulting
    ``dirty`` PR is handled after creation.

    Args:
        project_dir: Path to the project directory.
    """
    try:
        branch = get_current_branch_name(project_dir)
        base = detect_base_branch(project_dir, current_branch=branch)
        if base is None:
            logger.warning("Could not detect base branch; skipping rebase before PR")
            return

        needed, reason = needs_rebase(project_dir, base)
        if not needed:
            if reason.startswith("error:"):
                logger.warning(
                    "Rebase check failed for origin/%s (non-blocking): %s",
                    base,
                    reason,
                )
            else:
                logger.info("Branch is up to date with origin/%s", base)
            return

        logger.log(OUTPUT, "Branch is behind origin/%s; rebasing...", base)
        outcome = _attempt_rebase_and_push(project_dir)
        logger.log(OUTPUT, "Rebase result: %s", outcome.reason)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Rebase before PR failed (non-blocking): %s", e)
