"""Jenkins-side execution of the CI auto-fix loop.

Reuses the existing CI auto-fix loop (``check_and_fix_ci``) to try to fix a
PR's failing CI, dispatched from ``status-82:fixing-ci`` via the ``fix-ci``
CLI verb.
"""

import logging
from pathlib import Path

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.mcp_workspace_git import get_current_branch_name
from mcp_coder.mcp_workspace_github import IssueManager
from mcp_coder.workflow_steps.ci import check_and_fix_ci
from mcp_coder.workflow_steps.commit import check_formatter_config
from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure,
    handle_workflow_failure,
    llm_failure_reason,
    run_guarded,
)
from mcp_coder.workflow_utils.label_transitions import update_workflow_label

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
) -> int:
    """Deliberate fix_ci failure: comment (Category/Stage/Error) + status-84 label.

    Returns:
        1, indicating failure.
    """
    comment = (
        "## ❌ CI Fix Failed\n"
        f"**Category:** {category_display}\n"
        f"**Stage:** {stage}\n"
        f"**Error:** {message}"
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
) -> int:
    """Run the CI auto-fix loop for status-82:fixing-ci.

    Returns:
        0 on CI passing, 1 on any handled or netted failure.
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

        try:
            ci_ok = check_and_fix_ci(
                project_dir, branch, provider, mcp_config, settings_file
            )
        except (LLMTimeoutError, McpServersUnavailableError) as exc:
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

        if ci_ok:
            if update_issue_labels:
                update_workflow_label(
                    IssueManager(project_dir), "fixing_ci", "pr_created"
                )
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
        comment_header="## ❌ CI Fix Crashed",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )
