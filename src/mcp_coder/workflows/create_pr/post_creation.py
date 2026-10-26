"""Post-creation steps (phase B) for the create-pr workflow.

After the PR is opened, mergeability is checked before CI, in the same order
as PR-health: a ``dirty`` PR gets one rebase-and-push, and if it is still
``dirty`` the CI wait is skipped because CI results on a conflicting branch
are moot. Otherwise the CI run for the pushed HEAD is awaited. This phase
only waits and reports a final label - it never fixes CI or conflicts.
"""

import logging
from pathlib import Path

from mcp_coder.mcp_workspace_git import get_latest_commit_sha
from mcp_coder.mcp_workspace_github import CIResultsManager
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.workflow_steps.ci import _poll_for_ci_completion
from mcp_coder.workflow_steps.pr_description import refresh_pr_description
from mcp_coder.workflow_steps.rebase import (
    _attempt_rebase_and_push,
    _poll_mergeable_state,
)

logger = logging.getLogger(__name__)


def run_post_creation(
    project_dir: Path,
    branch: str,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
) -> str:
    """Check mergeability, then wait for CI. No fixing.

    If this phase pushed new commits (a rebase), the PR title/body is
    refreshed afterwards. The refresh is best-effort and never changes the
    returned label.

    Args:
        project_dir: Path to the project directory.
        branch: Head branch of the PR.
        provider: LLM provider used for the description refresh.
        mcp_config: Optional path to MCP configuration file.
        settings_file: Optional path to .claude/settings.local.json.

    Returns:
        Label ID for the final transition from pr_creating:
        "pr_merge_conflict", "failing_ci" or "pr_created".
    """
    head_before = get_latest_commit_sha(project_dir)
    label = _check_mergeability_and_ci(project_dir, branch)
    if get_latest_commit_sha(project_dir) != head_before:
        logger.log(OUTPUT, "New commits were pushed; refreshing PR description")
        refresh_pr_description(project_dir, branch, provider, mcp_config, settings_file)
    return label


def _check_mergeability_and_ci(project_dir: Path, branch: str) -> str:
    """Check mergeability (rebasing once on ``dirty``), then wait for CI.

    Returns:
        Label ID: "pr_merge_conflict", "failing_ci" or "pr_created".
    """
    state = _poll_mergeable_state(project_dir, branch)
    logger.log(OUTPUT, "PR mergeable_state: %s", state)
    if state == "dirty":
        outcome = _attempt_rebase_and_push(project_dir)
        logger.log(OUTPUT, "Rebase result: %s", outcome.reason)
        state = _poll_mergeable_state(project_dir, branch)
        if state == "dirty":
            logger.log(
                OUTPUT, "PR still has merge conflicts after rebase; skipping CI wait"
            )
            return "pr_merge_conflict"

    try:
        ci_manager = CIResultsManager(project_dir)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.info("CI_API_ERROR: could not create CI manager (%s)", e)
        return "pr_created"

    # Read after any rebase, so it is the HEAD that was actually pushed.
    expected_sha = get_latest_commit_sha(project_dir)
    ci_status, ci_ok = _poll_for_ci_completion(
        ci_manager, branch, expected_sha=expected_sha
    )
    if ci_status is not None and not ci_ok:
        return "failing_ci"
    return "pr_created"
