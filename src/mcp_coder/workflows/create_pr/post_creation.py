"""Post-creation steps (phase B) for the create-pr workflow.

After the PR is opened, mergeability is checked before CI, in the same order
as PR-health: a ``dirty`` PR gets one rebase-and-push, and if it is still
``dirty`` the CI wait is skipped because CI results on a conflicting branch
are moot. Otherwise the CI run for the pushed HEAD is awaited. This phase
only waits and applies a final label - it never fixes CI or conflicts.
"""

import logging
from pathlib import Path

from mcp_coder.mcp_workspace_git import get_latest_commit_sha
from mcp_coder.mcp_workspace_github import CIResultsManager
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.workflow_steps.ci import _poll_for_ci_completion
from mcp_coder.workflow_steps.merge import (
    finish_auto_merge,
    is_real_green,
    run_auto_merge,
)
from mcp_coder.workflow_steps.pr_description import refresh_pr_description
from mcp_coder.workflow_steps.rebase import (
    _attempt_rebase_and_push,
    _poll_mergeable_state,
    _reset_hard,
)
from mcp_coder.workflow_utils.label_transitions import apply_final_label

logger = logging.getLogger(__name__)


def run_post_creation(
    project_dir: Path,
    branch: str,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    *,
    issue_number: int | None,
    update_issue_labels: bool,
    post_issue_comments: bool = False,
    auto_merge: bool = False,
) -> int:
    """Check mergeability, wait for CI, then apply the final label. No fixing.

    If this phase pushed new commits (a rebase), the PR title/body is
    refreshed afterwards. The refresh is best-effort and never changes the
    final label. With ``auto_merge`` on and CI really green on HEAD, the PR
    is then squash-merged and the merge outcome decides the final label.

    Args:
        project_dir: Path to the project directory.
        branch: Head branch of the PR.
        provider: LLM provider used for the description refresh.
        mcp_config: Optional path to MCP configuration file.
        settings_file: Optional path to .claude/settings.local.json.
        issue_number: Issue linked to the branch, or None.
        update_issue_labels: If True, apply the final label to the issue.
        post_issue_comments: If True, post the auto-merge failure comment.
        auto_merge: If True, squash-merge the PR on a real green.

    Returns:
        Exit code: 1 on "pr_merge_conflict" / "merge_failed" or when the label
        write fails, else 0 ("failing_ci" / "pr_created" / "merged").
    """
    head_before = get_latest_commit_sha(project_dir)
    label, verified_sha = _check_mergeability_and_ci(project_dir, branch, head_before)
    if get_latest_commit_sha(project_dir) != head_before:
        logger.log(OUTPUT, "New commits were pushed; refreshing PR description")
        refresh_pr_description(project_dir, branch, provider, mcp_config, settings_file)
    if auto_merge and label == "pr_created":
        if verified_sha:
            outcome = run_auto_merge(project_dir, branch, verified_sha=verified_sha)
            return finish_auto_merge(
                project_dir,
                outcome,
                from_label_id="pr_creating",
                issue_number=issue_number,
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
            )
        logger.warning(
            "Auto-merge skipped: CI not verified green on HEAD; keeping pr-created"
        )
    return apply_post_creation_label(
        project_dir,
        label,
        issue_number=issue_number,
        update_issue_labels=update_issue_labels,
    )


def apply_post_creation_label(
    project_dir: Path,
    label: str,
    *,
    issue_number: int | None,
    update_issue_labels: bool,
) -> int:
    """Apply the final phase B label (pr_creating → label) and map the exit code.

    Args:
        project_dir: Path to the project directory.
        label: Final label ID: "pr_merge_conflict", "failing_ci" or "pr_created".
        issue_number: Issue linked to the branch, or None (label write skipped).
        update_issue_labels: If True, apply the label to the issue.

    Returns:
        Exit code: 1 when the label write fails or the label is
        "pr_merge_conflict" (status-74), else 0.
    """
    rc = 0
    if update_issue_labels and issue_number:
        logger.log(OUTPUT, "Updating GitHub issue label...")
        rc = apply_final_label(project_dir, "pr_creating", label, issue_number)
        if rc == 0:
            logger.log(OUTPUT, "✓ Issue label updated: pr_creating → %s", label)
    else:
        if update_issue_labels:
            logger.warning("Skipping label update: branch was not linked to an issue")
        logger.log(OUTPUT, "Post-creation outcome: %s (label not updated)", label)

    if rc != 0:
        logger.error("Create PR workflow failed: final issue label not applied")
    elif update_issue_labels and issue_number is None:
        logger.log(OUTPUT, "Create PR workflow completed with warnings")
    else:
        logger.log(OUTPUT, "Create PR workflow completed successfully!")
    return rc or (1 if label == "pr_merge_conflict" else 0)


def _check_mergeability_and_ci(
    project_dir: Path, branch: str, head_before: str | None
) -> tuple[str, str | None]:
    """Check mergeability (rebasing once on ``dirty``), then wait for CI.

    Args:
        project_dir: Path to the project directory.
        branch: Head branch of the PR.
        head_before: Local HEAD at the start of phase B; restored when the
            rebase succeeds locally but its push fails.

    Returns:
        Tuple of the label ID ("pr_merge_conflict", "failing_ci" or
        "pr_created") and the HEAD SHA CI really passed on, or None when CI
        was not verified green on HEAD.
    """
    state = _poll_mergeable_state(project_dir, branch)
    logger.log(OUTPUT, "PR mergeable_state: %s", state)
    if state == "dirty":
        outcome = _attempt_rebase_and_push(project_dir)
        logger.log(OUTPUT, "Rebase result: %s", outcome.reason)
        if outcome.reason == "push_failed" and head_before:
            # Undo the unpushed rebase: the CI wait and the description
            # refresh must see the HEAD the PR actually has.
            _reset_hard(project_dir, head_before)
        state = _poll_mergeable_state(project_dir, branch)
        if state == "dirty":
            logger.log(
                OUTPUT, "PR still has merge conflicts after rebase; skipping CI wait"
            )
            return "pr_merge_conflict", None

    try:
        ci_manager = CIResultsManager(project_dir)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.info("CI_API_ERROR: could not create CI manager (%s)", e)
        return "pr_created", None

    # Read after any rebase, so it is the HEAD that was actually pushed.
    expected_sha = get_latest_commit_sha(project_dir)
    ci_status, ci_ok = _poll_for_ci_completion(
        ci_manager, branch, expected_sha=expected_sha
    )
    if ci_status is not None and not ci_ok:
        return "failing_ci", None
    verified = is_real_green(ci_status, ci_ok, expected_sha)
    return "pr_created", (expected_sha if verified else None)
