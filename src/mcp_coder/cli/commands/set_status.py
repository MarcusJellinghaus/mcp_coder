"""Set status CLI command implementation.

This module provides the CLI command interface for updating the status
label on GitHub issues through the workflow system.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

from ...constants import DEFAULT_IGNORED_BUILD_ARTIFACTS
from ...utils.git_operations.readers import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from ...utils.git_operations.repository import is_working_directory_clean
from ...utils.github_operations.issue_manager import IssueManager
from ...utils.github_operations.label_config import (
    get_labels_config_path,
    load_labels_config,
)
from ...workflows.utils import resolve_project_dir

logger = logging.getLogger(__name__)


def build_set_status_epilog() -> str:
    """Build epilog text with available labels from config.

    Returns:
        Formatted string with available status labels and examples,
        or fallback message if config cannot be loaded.
    """
    try:
        # Use package bundled config (always available)
        config_path = get_labels_config_path(None)
        labels_config = load_labels_config(config_path)

        lines = ["Available status labels:"]
        for label in labels_config["workflow_labels"]:
            lines.append(f"  {label['name']:30} {label['description']}")
        lines.append("")
        lines.append("Examples:")
        lines.append("  mcp-coder set-status status-05:plan-ready")
        lines.append("  mcp-coder set-status status-08:ready-pr --issue 123")
        return "\n".join(lines)
    except Exception as e:
        # Log at debug level to aid troubleshooting (Decision #9)
        logger.debug(f"Failed to build set-status epilog: {e}")
        return "Run in a project directory to see available status labels."


def get_status_labels_from_config(config_path: Path) -> set[str]:
    """Load status labels from config and return set of label names.

    Args:
        config_path: Path to labels config file

    Returns:
        Set of label names (e.g., {"status-01:created", "status-02:awaiting-planning", ...})
    """
    labels_config = load_labels_config(config_path)

    # Extract workflow label names
    return {label["name"] for label in labels_config["workflow_labels"]}


def validate_status_label(
    label: str, valid_labels: set[str]
) -> Tuple[bool, Optional[str]]:
    """Check if label is a valid status label.

    Args:
        label: Label name to validate
        valid_labels: Set of valid label names from config

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, error_message) if invalid
    """
    if label in valid_labels:
        return True, None

    # Build error message with available labels
    sorted_labels = sorted(valid_labels)
    formatted_labels = "\n".join(f"  - {lbl}" for lbl in sorted_labels)
    error_msg = (
        f"'{label}' is not a valid status label.\nAvailable labels:\n{formatted_labels}"
    )
    return False, error_msg


def compute_new_labels(
    current_labels: set[str],
    new_status: str,
    all_status_names: set[str],
) -> set[str]:
    """Compute new label set: remove all status-*, add new_status.

    Args:
        current_labels: Current labels on the issue
        new_status: New status label to set
        all_status_names: All valid status label names

    Returns:
        New set of labels to apply
    """
    # Remove all existing status labels and add the new one
    non_status_labels = current_labels - all_status_names
    return non_status_labels | {new_status}


def _resolve_issue_number(
    args: argparse.Namespace, project_dir: Path
) -> Tuple[Optional[int], Optional[str]]:
    """Resolve issue number from args or branch name.

    Args:
        args: Parsed CLI arguments
        project_dir: Project directory path

    Returns:
        Tuple of (issue_number, error_message)
        - (issue_number, None) if resolved successfully
        - (None, error_message) if resolution failed
    """
    if args.issue:
        return args.issue, None

    branch = get_current_branch_name(project_dir)
    if branch is None:
        return None, (
            "Cannot detect current branch.\n"
            "Use --issue flag to specify issue number explicitly."
        )

    extracted_issue = extract_issue_number_from_branch(branch)
    if extracted_issue is None:
        return None, (
            f"Cannot detect issue number from branch '{branch}'.\n"
            f"Branch must follow pattern: {{issue_number}}-title "
            f"(e.g., '123-feature-name')\n"
            f"Use --issue flag to specify issue number explicitly."
        )

    return extracted_issue, None


def _update_issue_labels(
    manager: IssueManager,
    issue_number: int,
    status_label: str,
    status_labels: set[str],
) -> Tuple[bool, Optional[str]]:
    """Get issue, compute new labels, and apply them.

    Args:
        manager: IssueManager instance
        issue_number: Issue number to update
        status_label: New status label to set
        status_labels: All valid status label names

    Returns:
        Tuple of (success, error_message)
        - (True, None) if successful
        - (False, error_message) if failed
    """
    issue_data = manager.get_issue(issue_number)

    # Check for error (number=0 indicates error)
    if issue_data["number"] == 0:
        return False, (
            f"Failed to get issue #{issue_number}. "
            "Issue may not exist or there may be a GitHub API error."
        )

    current_labels = set(issue_data["labels"])
    new_labels = compute_new_labels(current_labels, status_label, status_labels)

    # Apply new labels
    result = manager.set_labels(issue_number, *new_labels)

    # Check for error (number=0 indicates error)
    if result["number"] == 0:
        return False, (
            f"Failed to update labels for issue #{issue_number}.\n"
            f"Label '{status_label}' may not exist on GitHub.\n"
            "Run `mcp-coder define-labels` to create workflow labels."
        )

    return True, None


def execute_set_status(args: argparse.Namespace) -> int:
    """Execute the set-status command.

    Args:
        args: Parsed CLI arguments with:
            - status_label: The status label to set
            - issue: Optional explicit issue number
            - project_dir: Optional project directory

    Returns:
        Exit code (0=success, 1=error)
    """
    try:
        # Step 1: Resolve project directory
        project_dir = resolve_project_dir(args.project_dir)

        # Step 1.5: Check working directory is clean (unless --force)
        if not args.force:
            try:
                if not is_working_directory_clean(
                    project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
                ):
                    print(
                        "Error: Working directory has uncommitted changes. "
                        "Commit/stash first or use --force.",
                        file=sys.stderr,
                    )
                    return 1
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1

        # Step 2: Load and validate label
        config_path = get_labels_config_path(project_dir)
        status_labels = get_status_labels_from_config(config_path)
        is_valid, error_msg = validate_status_label(args.status_label, status_labels)
        if not is_valid:
            print(f"Error: {error_msg}", file=sys.stderr)
            return 1

        # Step 3: Get issue number
        issue_number, resolve_error = _resolve_issue_number(args, project_dir)
        if issue_number is None:
            print(f"Error: {resolve_error}", file=sys.stderr)
            return 1

        # Step 4: Get current issue, compute new labels, and apply
        manager = IssueManager(project_dir)
        success, update_error = _update_issue_labels(
            manager, issue_number, args.status_label, status_labels
        )
        if not success:
            print(f"Error: {update_error}", file=sys.stderr)
            return 1

        logger.info(f"Updated issue #{issue_number} to {args.status_label}")
        return 0

    except ValueError as e:
        logger.error(str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1
