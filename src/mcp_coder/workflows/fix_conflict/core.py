"""Jenkins-side execution of the mechanical merge-conflict fix.

Rebases the current branch onto its base, polls the resulting PR's
``mergeable_state`` until it settles, and transitions the workflow label
accordingly. Runs inside the Jenkins job's own checkout, dispatched from
``status-71:merge-conflict`` via the ``fix-conflict`` CLI verb.
"""

import logging
import time
from pathlib import Path
from typing import Optional

from mcp_coder.mcp_workspace_git import get_current_branch_name
from mcp_coder.mcp_workspace_github import IssueManager, PullRequestManager
from mcp_coder.workflow_steps.rebase import _attempt_rebase_and_push
from mcp_coder.workflow_utils.failure_handling import run_guarded
from mcp_coder.workflow_utils.label_transitions import update_workflow_label

logger = logging.getLogger(__name__)

_POLL_ATTEMPTS = 6
_POLL_INTERVAL_SECONDS = 5


def _poll_mergeable_state(project_dir: Path, branch_name: str) -> Optional[str]:
    """Poll ``find_pull_request_by_head`` for a settled mergeable_state.

    Returns:
        The last observed mergeable_state (may be "unknown" or None if the
        PR disappeared) after the loop ends.
    """
    state: Optional[str] = None
    for attempt in range(_POLL_ATTEMPTS):
        prs = PullRequestManager(project_dir).find_pull_request_by_head(branch_name)
        state = prs[0]["mergeable_state"] if prs else None
        # "unknown" is GitHub's not-yet-computed placeholder - keep polling.
        if state not in (None, "unknown"):
            return state
        if attempt < _POLL_ATTEMPTS - 1:
            time.sleep(_POLL_INTERVAL_SECONDS)
    return state


def run_fix_conflict_workflow(project_dir: Path) -> int:
    """Rebase the current branch and resolve the merge-conflict escalation.

    Returns:
        0 on any handled outcome (resolved clean, resolved still conflicting,
        or still unknown after the poll cap). 1 on a netted crash - the
        Jenkins shell template's watchdog line is a further safety net for
        a silent crash, this is just the reported exit code.
    """

    def body() -> int:
        branch = get_current_branch_name(project_dir)
        if branch is None:
            logger.error("Could not determine current branch")
            return 1

        rebased = _attempt_rebase_and_push(project_dir)
        logger.info("Rebase attempt result: %s", rebased)

        state = _poll_mergeable_state(project_dir, branch)
        # "dirty" is GitHub's only verdict for a real unresolved merge conflict.
        if state == "dirty":
            update_workflow_label(
                IssueManager(project_dir),
                "fixing_merge_conflict",
                "pr_merge_conflict",
            )
        elif state not in (None, "unknown"):
            update_workflow_label(
                IssueManager(project_dir), "fixing_merge_conflict", "pr_created"
            )
        else:
            logger.info(
                "mergeable_state still unknown after poll cap - leaving at "
                "status-72 for next coordinator poll"
            )
        return 0

    return run_guarded(
        body,
        project_dir=project_dir,
        from_label_id="fixing_merge_conflict",
        general_category="merge_conflict_failed",
        comment_header="## ❌ Fix Conflict Crashed",
        update_issue_labels=True,
        post_issue_comments=True,
    )
