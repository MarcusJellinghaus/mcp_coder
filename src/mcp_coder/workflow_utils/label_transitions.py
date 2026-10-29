"""Standalone workflow label transition function.

Extracted from IssueManager.update_workflow_label() to decouple workflow
state-machine logic from the GitHub manager class.
"""

import logging
import time
from pathlib import Path

from mcp_coder.config.label_config import (
    build_label_lookups,
    get_labels_config_path,
    load_labels_config,
)
from mcp_coder.mcp_workspace_git import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from mcp_coder.mcp_workspace_github import (
    IssueBranchManager,
    IssueManager,
)
from mcp_coder.workflow_utils.branch_linkage import is_branch_linked_to_issue
from mcp_coder.workflow_utils.rate_limit import raise_if_rate_limited

logger = logging.getLogger(__name__)

__all__ = [
    "FINAL_LABEL_RETRY_DELAY_SECONDS",
    "apply_final_label",
    "update_workflow_label",
]

FINAL_LABEL_RETRY_DELAY_SECONDS = 30


def update_workflow_label(
    issue_manager: IssueManager,
    from_label_id: str,
    to_label_id: str,
    branch_name: str | None = None,
    validated_issue_number: int | None = None,
) -> bool:
    """Workflow state machine transition.

    Reads labels.json via label_config, resolves internal_ids to label names,
    then delegates to issue_manager.transition_issue_label().

    Non-blocking except for rate limits, which raise ``GitHubRateLimitError``.
    All other errors are caught, logged, and return False.

    Args:
        issue_manager: IssueManager instance to delegate label operations to.
        from_label_id: Internal ID of source label (e.g., "implementing").
        to_label_id: Internal ID of target label (e.g., "code_review").
        branch_name: Optional branch name. If None, detects current branch.
        validated_issue_number: Optional pre-validated issue number. If provided,
            skips branch detection and linkage validation.

    Returns:
        True if label updated successfully, False otherwise.

    Raises:
        GitHubRateLimitError: If a GitHub rate limit is hit.
    """
    try:
        # Check for pre-validated issue number
        if validated_issue_number is not None:
            issue_number = validated_issue_number
        else:
            # Step 1: Get branch name (provided or auto-detect)
            actual_branch_name: str
            if branch_name is None:
                if issue_manager.project_dir is None:
                    logger.error(
                        "Cannot auto-detect branch name without project_dir. "
                        "Please provide branch_name parameter."
                    )
                    return False
                detected_branch = get_current_branch_name(issue_manager.project_dir)
                if detected_branch is None:
                    logger.error(
                        "Failed to detect current branch name. "
                        "Please provide branch_name parameter."
                    )
                    return False
                actual_branch_name = detected_branch
            else:
                actual_branch_name = branch_name

            # Step 2: Extract issue number from branch name
            extracted_issue_number = extract_issue_number_from_branch(
                actual_branch_name
            )
            if extracted_issue_number is None:
                logger.warning(
                    f"Branch '{actual_branch_name}' does not follow "
                    "{issue_number}-title pattern"
                )
                return False
            issue_number = extracted_issue_number

            # Step 3: Verify branch is linked to the issue
            if issue_manager.project_dir is not None:
                branch_manager = IssueBranchManager(
                    project_dir=issue_manager.project_dir,
                    github_token=issue_manager.github_token,
                )
            else:
                branch_manager = IssueBranchManager(
                    repo_url=issue_manager.repo_identifier.https_url,
                    github_token=issue_manager.github_token,
                )
            if not is_branch_linked_to_issue(
                branch_manager, issue_number, actual_branch_name
            ):
                return False

        # Step 4: Load label config and build lookups
        config_path = get_labels_config_path(issue_manager.project_dir)
        label_config = load_labels_config(config_path)
        label_lookups = build_label_lookups(label_config)

        # Step 5: Lookup actual label names from internal IDs
        from_label_name = label_lookups["id_to_name"].get(from_label_id)
        to_label_name = label_lookups["id_to_name"].get(to_label_id)

        if not from_label_name:
            logger.error(
                f"Label ID '{from_label_id}' not found in configuration. "
                f"Available IDs: {list(label_lookups['id_to_name'].keys())}"
            )
            return False

        if not to_label_name:
            logger.error(
                f"Label ID '{to_label_id}' not found in configuration. "
                f"Available IDs: {list(label_lookups['id_to_name'].keys())}"
            )
            return False

        # Step 6: Delegate label mutation to the config-free primitive.
        labels_to_clear = label_lookups["all_names"] - {to_label_name}
        success = issue_manager.transition_issue_label(
            issue_number, to_label_name, labels_to_clear
        )
        if success:
            logger.info(
                f"Successfully updated issue #{issue_number} label: "
                f"{from_label_name} → {to_label_name}"
            )
        return success

    except Exception as e:  # pylint: disable=broad-exception-caught  # non-blocking by design
        raise_if_rate_limited(e)
        logger.error(f"Unexpected error updating workflow label: {e}")
        return False


def apply_final_label(
    project_dir: Path,
    from_label_id: str,
    to_label_id: str,
    issue_number: int | None = None,
) -> int:
    """Apply the workflow's final label; retry once after ~30 s.

    Returns 0 on success, 1 after the retry failed. Never raises or exits,
    so run_guarded's safety net is not triggered.

    Args:
        project_dir: Project directory (used for the manager and branch lookup).
        from_label_id: Internal ID of the workflow's busy label.
        to_label_id: Internal ID of the intended final label.
        issue_number: Optional pre-validated issue number.

    Returns:
        0 if the label was applied, 1 if both attempts failed.
    """
    for attempt in (1, 2):
        if attempt == 2:
            time.sleep(FINAL_LABEL_RETRY_DELAY_SECONDS)
        try:
            if update_workflow_label(
                IssueManager(project_dir=project_dir),
                from_label_id,
                to_label_id,
                validated_issue_number=issue_number,
            ):
                return 0
        except Exception as exc:  # pylint: disable=broad-exception-caught  # retried, then reported via exit code
            logger.warning("Final label update failed (attempt %d): %s", attempt, exc)

    number = issue_number
    if number is None:
        try:
            number = extract_issue_number_from_branch(
                get_current_branch_name(project_dir) or ""
            )
        except Exception:  # pylint: disable=broad-exception-caught  # only for the error message
            number = None
    logger.error(
        "Final label update failed for issue #%s: intended label '%s'",
        number or "?",
        to_label_id,
    )
    return 1
