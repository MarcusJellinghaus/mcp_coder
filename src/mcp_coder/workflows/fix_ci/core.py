"""Jenkins-side execution of the CI auto-fix loop.

Reuses the existing CI auto-fix loop (``check_and_fix_ci``) to try to fix a
PR's failing CI, dispatched from ``status-82:fixing-ci`` via the ``fix-ci``
CLI verb.
"""

import logging
from pathlib import Path

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.mcp_workspace_git import get_current_branch_name, get_latest_commit_sha
from mcp_coder.workflow_steps.ci import check_and_fix_ci
from mcp_coder.workflow_steps.commit import (
    BRANCH_MOVED_NEXT_STEP,
    PushRejectedError,
    check_formatter_config,
)
from mcp_coder.workflow_steps.merge import (
    finish_auto_merge,
    resolve_merge_issue_number,
    run_auto_merge,
)
from mcp_coder.workflow_steps.pr_description import refresh_pr_description
from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure,
    build_failure_comment,
    handle_workflow_failure,
    llm_failure_reason,
    run_guarded,
)
from mcp_coder.workflow_utils.label_transitions import apply_final_label

logger = logging.getLogger(__name__)

_LLM_FAILURE_CATEGORY_DISPLAY = {
    "timeout": "Llm Timeout",
    "mcp_unavailable": "Mcp Unavailable",
}


def _fail(
    project_dir: Path,
    category_display: str,
    stage: str,
    message: str,
    *,
    update_issue_labels: bool,
    post_issue_comments: bool,
    next_step: str | None = None,
) -> int:
    """Deliberate fix_ci failure: comment (Category/Stage/Error) + status-84 label.

    Returns:
        1, indicating failure.
    """
    comment = build_failure_comment(
        project_dir,
        title="CI Fix",
        kind="Failed",
        fields=[
            ("Category", category_display),
            ("Stage", stage),
            ("Error", message),
            ("Next step", next_step),
        ],
    )
    handle_workflow_failure(
        WorkflowFailure(category="pr_ci_failed", stage=stage, message=message),
        comment,
        project_dir,
        from_label_id="fixing_ci",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )
    return 1


def run_fix_ci_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
    auto_merge: bool = False,
) -> int:
    """Run the CI auto-fix loop for status-82:fixing-ci.

    With ``auto_merge``, a passing CI hands over to the auto-merge helper.

    Returns:
        0 on CI passing, 1 on any handled or netted failure. With
        ``auto_merge``, a passing CI's exit code follows the merge outcome.
    """

    def body() -> int:
        # Formatter pre-flight: an unresolvable formatter would only surface
        # after an LLM fix attempt, at the formatting call in check_and_fix_ci.
        formatter_err = check_formatter_config(project_dir, warn_legacy_key=True)
        if formatter_err:
            return _fail(
                project_dir,
                "General",
                "Formatter configuration",
                formatter_err,
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
            )

        branch = get_current_branch_name(project_dir)
        if branch is None:
            logger.error("Could not determine current branch")
            return 1

        head_before = get_latest_commit_sha(project_dir)

        def _refresh_if_pushed() -> None:
            # Runs while the issue is still at fixing_ci; never raises.
            if get_latest_commit_sha(project_dir) != head_before:
                logger.info("New commits were pushed; refreshing PR description")
                refresh_pr_description(
                    project_dir, branch, provider, mcp_config, settings_file
                )

        try:
            ci_ok = check_and_fix_ci(
                project_dir, branch, provider, mcp_config, settings_file
            )
        except (LLMTimeoutError, McpServersUnavailableError) as exc:
            _refresh_if_pushed()
            reason = llm_failure_reason(exc) or "general"
            category = _LLM_FAILURE_CATEGORY_DISPLAY.get(reason, "General")
            return _fail(
                project_dir,
                category,
                "CI pipeline analysis",
                str(exc),
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
            )
        except PushRejectedError as exc:
            # No refresh: local HEAD holds a commit the remote does not have.
            return _fail(
                project_dir,
                "Branch Moved",
                "CI pipeline fix",
                str(exc),
                next_step=(
                    f"{BRANCH_MOVED_NEXT_STEP} "
                    "Then set `status-10:pr-created` so CI is re-detected."
                ),
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
            )

        _refresh_if_pushed()
        if ci_ok:
            if auto_merge:
                issue_number = resolve_merge_issue_number(project_dir, branch)
                outcome = run_auto_merge(project_dir, branch)
                return finish_auto_merge(
                    project_dir,
                    outcome,
                    from_label_id="fixing_ci",
                    issue_number=issue_number,
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                )
            if update_issue_labels:
                return apply_final_label(project_dir, "fixing_ci", "pr_created")
            return 0

        return _fail(
            project_dir,
            "Ci Fix Exhausted",
            "CI pipeline fix",
            "CI check failed after maximum fix attempts",
            update_issue_labels=update_issue_labels,
            post_issue_comments=post_issue_comments,
        )

    return run_guarded(
        body,
        project_dir=project_dir,
        from_label_id="fixing_ci",
        general_category="ci_fix_failed",
        workflow_title="CI Fix",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )
