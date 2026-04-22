"""Standalone workflow label transition function.

Extracted from IssueManager.update_workflow_label() to decouple workflow
state-machine logic from the GitHub manager class.
"""

import logging
from typing import Optional

from mcp_coder.config.label_config import (
    build_label_lookups,
    get_labels_config_path,
    load_labels_config,
)
from mcp_coder.mcp_workspace_git import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from mcp_coder.mcp_workspace_github import IssueBranchManager, IssueManager

logger = logging.getLogger(__name__)

__all__ = ["update_workflow_label"]


def update_workflow_label(
    issue_manager: IssueManager,
    from_label_id: str,
    to_label_id: str,
    branch_name: Optional[str] = None,
    validated_issue_number: Optional[int] = None,
) -> bool:
    """Workflow state machine transition.

    Reads labels.json via label_config, resolves internal_ids to label names,
    then delegates to issue_manager.transition_issue_label().

    Non-blocking: All errors are caught, logged, and return False.
    Workflow success is never affected by label update failures.

    Args:
        issue_manager: IssueManager instance to delegate label operations to.
        from_label_id: Internal ID of source label (e.g., "implementing").
        to_label_id: Internal ID of target label (e.g., "code_review").
        branch_name: Optional branch name. If None, detects current branch.
        validated_issue_number: Optional pre-validated issue number. If provided,
            skips branch detection and linkage validation.

    Returns:
        True if label updated successfully, False otherwise.
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
            repo_url = None
            if issue_manager._repo_full_name is not None:
                repo_url = f"https://github.com/{issue_manager._repo_full_name}.git"

            branch_manager = IssueBranchManager(
                project_dir=issue_manager.project_dir, repo_url=repo_url
            )
            linked_branches = branch_manager.get_linked_branches(issue_number)

            if actual_branch_name not in linked_branches:
                logger.warning(
                    f"Branch '{actual_branch_name}' is not linked to "
                    f"issue #{issue_number}. "
                    f"Linked branches: {linked_branches}"
                )
                return False

        # Step 4: Load label config and build lookups
        if issue_manager.project_dir is None:
            logger.error(
                "Cannot load label config without project_dir. "
                "Label update is not supported for repo_url mode."
            )
            return False

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

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # non-blocking by design
        logger.error(f"Unexpected error updating workflow label: {e}")
        return False
