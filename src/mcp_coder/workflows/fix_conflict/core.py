"""Jenkins-side execution of the merge-conflict fix.

Rebases the current branch onto its base - git-only first, then the LLM
rebase on conflict / rebase_failed - polls the resulting PR's
``mergeable_state`` until it settles, and transitions the workflow label
accordingly. Runs inside the Jenkins job's own checkout, dispatched from
``status-71:merge-conflict`` via the ``fix-conflict`` CLI verb.
"""

import logging
from pathlib import Path

from mcp_coder.mcp_workspace_git import get_current_branch_name
from mcp_coder.workflow_steps.merge import (
    finish_auto_merge,
    resolve_merge_issue_number,
    run_auto_merge,
)
from mcp_coder.workflow_steps.rebase import RebaseOutcome, _poll_mergeable_state
from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure,
    build_failure_comment,
    handle_workflow_failure,
    run_guarded,
)
from mcp_coder.workflow_utils.label_transitions import apply_final_label
from mcp_coder.workflows.rebase_automated import rebase_with_llm_fallback

logger = logging.getLogger(__name__)


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
        ("LLM rebase", outcome.llm_detail),
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


def run_fix_conflict_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    settings_override: str | None = None,
    auto_merge: bool = False,
) -> int:
    """Rebase the current branch and resolve the merge-conflict escalation.

    With ``auto_merge``, a resolved conflict hands over to the auto-merge
    helper instead of returning to status-10; its CI poll waits for CI on
    the rebased HEAD before merging.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider for the fallback rebase session
        mcp_config: MCP config path for the fallback rebase session
        settings_override: Already-resolved settings path; None uses the
            least-privilege rebase settings.
        auto_merge: Hand a resolved conflict over to the auto-merge helper.

    Returns:
        0 on status-10: a settled non-dirty state, or "unknown" after a
        successful rebase. 1 on status-74 ("dirty", no open PR, or "unknown"
        after a failed rebase; posted with a comment), when the current
        branch cannot be determined, when the status-10
        label could not be applied after one retry, or on a netted
        crash - the Jenkins shell template's watchdog line is a further
        safety net for a silent crash, this is just the reported exit code.
        With ``auto_merge``, a resolved conflict's exit code follows the
        merge outcome: 0 on merged / pr_created / failing_ci, 1 on
        pr_merge_conflict / merge_failed or a failed label write.
    """

    def body() -> int:
        branch = get_current_branch_name(project_dir)
        if branch is None:
            logger.error("Could not determine current branch")
            return 1

        outcome = rebase_with_llm_fallback(
            project_dir, provider, mcp_config, settings_override
        )
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
            return 1
        if state == "unknown":
            # Safe: status-10 detection re-checks "dirty" on every poll.
            logger.info(
                "mergeable_state still unknown after poll cap but rebase "
                "succeeded - returning to status-10"
            )
        if auto_merge:
            issue_number = resolve_merge_issue_number(project_dir, branch)
            merge_outcome = run_auto_merge(project_dir, branch)
            return finish_auto_merge(
                project_dir,
                merge_outcome,
                from_label_id="fixing_merge_conflict",
                issue_number=issue_number,
                update_issue_labels=True,
                post_issue_comments=True,
            )
        return apply_final_label(project_dir, "fixing_merge_conflict", "pr_created")

    return run_guarded(
        body,
        project_dir=project_dir,
        from_label_id="fixing_merge_conflict",
        general_category="merge_conflict_failed",
        workflow_title="Fix Conflict",
        update_issue_labels=True,
        post_issue_comments=True,
    )
