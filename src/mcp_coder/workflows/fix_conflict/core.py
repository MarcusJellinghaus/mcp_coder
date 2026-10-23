"""Jenkins-side execution of the mechanical merge-conflict fix.

Rebases the current branch onto its base, polls the resulting PR's
``mergeable_state`` until it settles, and transitions the workflow label
accordingly. Runs inside the Jenkins job's own checkout, dispatched from
``status-71:merge-conflict`` via the ``fix-conflict`` CLI verb.
"""

import logging
import time
from pathlib import Path

from mcp_coder.mcp_workspace_git import get_current_branch_name
from mcp_coder.mcp_workspace_github import IssueManager, PullRequestManager
from mcp_coder.workflow_steps.rebase import RebaseOutcome, _attempt_rebase_and_push
from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure,
    build_failure_comment,
    handle_workflow_failure,
    run_guarded,
)
from mcp_coder.workflow_utils.label_transitions import update_workflow_label

logger = logging.getLogger(__name__)

_POLL_ATTEMPTS = 6
_POLL_INTERVAL_SECONDS = 5


def _poll_mergeable_state(project_dir: Path, branch_name: str) -> str | None:
    """Poll ``find_pull_request_by_head`` for a settled mergeable_state.

    Returns:
        The last observed mergeable_state (may be "unknown" or None if the
        PR disappeared) after the loop ends.
    """
    state: str | None = None
    for attempt in range(_POLL_ATTEMPTS):
        prs = PullRequestManager(project_dir).find_pull_request_by_head(branch_name)
        state = prs[0]["mergeable_state"] if prs else None
        # "unknown" is GitHub's not-yet-computed placeholder - keep polling.
        if state not in (None, "unknown"):
            return state
        if attempt < _POLL_ATTEMPTS - 1:
            time.sleep(_POLL_INTERVAL_SECONDS)
    return state


def _fail(project_dir: Path, verdict: str, outcome: RebaseOutcome) -> None:
    """status-74 verdict: "Fix Conflict Failed" comment + pr_merge_conflict label."""
    files_label = (
        "Likely conflicting files"
        if outcome.reason == "conflict"
        else "Uncommitted files"
    )
    fields = [
        ("Verdict", verdict),
        ("Reason", None if outcome.ok else outcome.reason),
        ("Base", outcome.base_branch),
        (files_label, ", ".join(outcome.files) if outcome.files else None),
    ]
    comment = build_failure_comment(
        project_dir, title="Fix Conflict", kind="Failed", fields=fields
    )
    handle_workflow_failure(
        WorkflowFailure(
            category="pr_merge_conflict",
            stage="Merge-conflict verdict",
            message=verdict,
        ),
        comment,
        project_dir,
        from_label_id="fixing_merge_conflict",
        update_issue_labels=True,
        post_issue_comments=True,
    )


def run_fix_conflict_workflow(project_dir: Path) -> int:
    """Rebase the current branch and resolve the merge-conflict escalation.

    Returns:
        0 on every handled outcome: a settled non-dirty state, or "unknown"
        after a successful rebase, goes to status-10; "dirty", no open PR,
        or "unknown" after a failed rebase goes to status-74 with a comment.
        1 when the current branch cannot be determined or on a netted
        crash - the Jenkins shell template's watchdog line is a further
        safety net for a silent crash, this is just the reported exit code.
    """

    def body() -> int:
        branch = get_current_branch_name(project_dir)
        if branch is None:
            logger.error("Could not determine current branch")
            return 1

        outcome = _attempt_rebase_and_push(project_dir)
        logger.info("Rebase attempt result: %s", outcome.reason)

        state = _poll_mergeable_state(project_dir, branch)
        # "dirty" is GitHub's only verdict for a real unresolved merge conflict.
        verdict: str | None
        if state == "dirty":
            verdict = "still conflicting"
        elif state is None:
            verdict = "no open PR found for branch"
        elif state == "unknown" and not outcome.ok:
            verdict = "mergeable state unknown, rebase did not complete"
        else:
            verdict = None

        if verdict:
            _fail(project_dir, verdict, outcome)
        else:
            if state == "unknown":
                # Safe: status-10 detection re-checks "dirty" on every poll.
                logger.info(
                    "mergeable_state still unknown after poll cap but rebase "
                    "succeeded - returning to status-10"
                )
            update_workflow_label(
                IssueManager(project_dir), "fixing_merge_conflict", "pr_created"
            )
        return 0

    return run_guarded(
        body,
        project_dir=project_dir,
        from_label_id="fixing_merge_conflict",
        general_category="merge_conflict_failed",
        workflow_title="Fix Conflict",
        update_issue_labels=True,
        post_issue_comments=True,
    )
