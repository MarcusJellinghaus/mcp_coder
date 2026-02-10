"""Define labels CLI command implementation.

This module provides the CLI command interface for defining and applying
workflow status labels to a GitHub repository.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from ...utils.github_operations.issue_manager import IssueData, IssueManager
from ...utils.github_operations.label_config import (
    get_labels_config_path,
    load_labels_config,
)
from ...utils.github_operations.labels_manager import LabelsManager
from ...workflows.utils import resolve_project_dir

logger = logging.getLogger(__name__)


def _log_dry_run_changes(changes: dict[str, list[str]]) -> None:
    """Log preview of label changes in dry-run mode."""
    logger.info("DRY RUN MODE - Preview of changes:")
    if changes["created"]:
        logger.info(
            f"  Would create {len(changes['created'])} labels: "
            f"{', '.join(changes['created'])}"
        )
    if changes["updated"]:
        logger.info(
            f"  Would update {len(changes['updated'])} labels: "
            f"{', '.join(changes['updated'])}"
        )
    if changes["deleted"]:
        logger.info(
            f"  Would delete {len(changes['deleted'])} labels: "
            f"{', '.join(changes['deleted'])}"
        )
    if changes["unchanged"]:
        logger.info(f"  {len(changes['unchanged'])} labels unchanged")


def check_status_labels(
    issue: IssueData,
    workflow_label_names: set[str],
) -> tuple[int, list[str]]:
    """Check how many workflow status labels an issue has.

    Args:
        issue: Issue data containing labels list
        workflow_label_names: Set of all valid workflow status label names

    Returns:
        Tuple of (count, list_of_status_labels) where:
        - count: Number of workflow status labels on the issue
        - list_of_status_labels: List of workflow label names found on the issue
    """
    # Get issue's labels and filter to only workflow labels
    issue_labels = issue["labels"]
    found_labels = [label for label in issue_labels if label in workflow_label_names]
    return (len(found_labels), found_labels)


def initialize_issues(
    issues: list[IssueData],
    workflow_label_names: set[str],
    created_label_name: str,
    issue_manager: IssueManager,
    dry_run: bool = False,
) -> list[int]:
    """Initialize issues without status labels.

    Issues without any workflow status label will be assigned the
    'created' label (typically 'status-01:created').

    Args:
        issues: List of IssueData from repository
        workflow_label_names: Set of all valid workflow status label names
        created_label_name: Name of the 'created' label to apply
        issue_manager: IssueManager instance for API calls
        dry_run: If True, preview changes without applying

    Returns:
        List of issue numbers that were (or would be in dry-run) initialized
    """
    initialized: list[int] = []

    for issue in issues:
        count, _ = check_status_labels(issue, workflow_label_names)
        if count == 0:
            issue_number = issue["number"]
            if not dry_run:
                issue_manager.add_labels(issue_number, created_label_name)
            initialized.append(issue_number)

    return initialized


def calculate_label_changes(
    existing_labels: list[tuple[str, str, str]],
    target_labels: list[tuple[str, str, str]],
) -> dict[str, list[str]]:
    """Pure function to calculate label changes without side effects.

    Compares existing GitHub labels against target labels to determine
    which labels need to be created, updated, deleted, or are unchanged.
    Only status-* labels are considered for deletion.

    Args:
        existing_labels: List of (name, color, description) tuples from GitHub
        target_labels: List of (name, color, description) tuples to apply

    Returns:
        Dict with keys: 'created', 'updated', 'deleted', 'unchanged'
        Each value is a list of label names

    Example:
        >>> existing = [("status-01:created", "10b981", "Fresh issue")]
        >>> target = [("status-01:created", "NEWCOL", "Updated desc")]
        >>> result = calculate_label_changes(existing, target)
        >>> result['updated']
        ['status-01:created']
    """
    # Initialize result dict with empty lists
    result: dict[str, list[str]] = {
        "created": [],
        "updated": [],
        "deleted": [],
        "unchanged": [],
    }

    # Build existing_map keyed by label name for O(1) lookup
    # Map format: {label_name: (color, description)}
    existing_map: dict[str, tuple[str, str]] = {
        name: (color, description) for name, color, description in existing_labels
    }

    # Build target_names set for O(1) lookup during deletion check
    target_names = {name for name, _, _ in target_labels}

    # Process target labels: determine create, update, or unchanged
    for name, color, description in target_labels:
        if name not in existing_map:
            # Label doesn't exist - needs to be created
            result["created"].append(name)
        else:
            # Label exists - check if update needed
            existing_color, existing_description = existing_map[name]
            if existing_color == color and existing_description == description:
                # No changes needed - identical
                result["unchanged"].append(name)
            else:
                # Color or description differs - needs update
                result["updated"].append(name)

    # Process existing labels: find status-* labels to delete
    # Only delete labels starting with 'status-' that are not in target
    for name in existing_map:
        if name.startswith("status-") and name not in target_names:
            result["deleted"].append(name)

    return result


def apply_labels(
    project_dir: Path,
    workflow_labels: list[tuple[str, str, str]],
    dry_run: bool = False,
) -> dict[str, list[str]]:
    """Apply workflow labels to repository.

    Orchestrator function that:
    1. Fetches existing labels from GitHub
    2. Calculates required changes
    3. Applies changes via LabelsManager API calls (unless dry_run=True)
    4. Logs all actions at INFO level
    5. Raises exceptions on any API error

    Args:
        project_dir: Path to project directory (must be git repo)
        workflow_labels: List of (name, color, description) tuples for target labels
        dry_run: If True, only preview changes without applying

    Returns:
        Dict with keys: 'created', 'updated', 'deleted', 'unchanged'
        Each value is a list of label names

    Raises:
        RuntimeError: On API errors during label operations
        ValueError: On invalid project_dir or missing GitHub token
    """
    try:
        # Initialize LabelsManager (validates token and repo connection)
        labels_manager = LabelsManager(project_dir)
    except (ValueError, Exception) as e:
        raise RuntimeError(f"Failed to initialize LabelsManager: {e}") from e

    # Fetch existing labels from GitHub
    try:
        existing_labels_data = labels_manager.get_labels()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch existing labels: {e}") from e

    # Convert LabelData list to tuple format for calculate_label_changes
    existing_labels = [
        (label["name"], label["color"], label["description"])
        for label in existing_labels_data
    ]

    # Calculate required changes
    changes = calculate_label_changes(existing_labels, workflow_labels)

    # Preview mode - log and return without applying
    if dry_run:
        _log_dry_run_changes(changes)
        return changes

    # Build lookup map for target label details
    target_map = {
        name: (color, description) for name, color, description in workflow_labels
    }

    # Apply changes - CREATE new labels
    for label_name in changes["created"]:
        color, description = target_map[label_name]
        try:
            labels_manager.create_label(label_name, color, description)
            logger.info(f"Created: {label_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to create label '{label_name}': {e}") from e

    # Apply changes - UPDATE existing labels
    for label_name in changes["updated"]:
        color, description = target_map[label_name]
        try:
            labels_manager.update_label(
                label_name, color=color, description=description
            )
            logger.info(f"Updated: {label_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to update label '{label_name}': {e}") from e

    # Apply changes - DELETE obsolete status-* labels
    for label_name in changes["deleted"]:
        try:
            labels_manager.delete_label(label_name)
            logger.info(f"Deleted: {label_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to delete label '{label_name}': {e}") from e

    # Unchanged labels - skip API calls (idempotent)
    # No logging for unchanged labels to reduce noise

    return changes


def execute_define_labels(args: argparse.Namespace) -> int:
    """Execute the define-labels command.

    Args:
        args: Parsed command line arguments with:
            - project_dir: Optional project directory path
            - dry_run: Preview mode flag

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Starting define-labels command execution")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        logger.info(f"Project directory: {project_dir}")

        # Load labels from JSON config using shared module
        # Tries project's local config first, falls back to package bundled config
        try:
            config_path = get_labels_config_path(project_dir)
            labels_config = load_labels_config(config_path)
        except FileNotFoundError as exc:
            raise ValueError(f"Configuration file not found: {config_path}") from exc
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}") from e

        # Extract workflow labels and convert to tuple format for GitHub API
        workflow_labels = [
            (label["name"], label["color"], label["description"])
            for label in labels_config["workflow_labels"]
        ]

        # Log dry-run mode status
        dry_run = getattr(args, "dry_run", False)
        if dry_run:
            logger.info("DRY RUN MODE: Changes will be previewed only")

        # Apply labels to repository
        results = apply_labels(project_dir, workflow_labels, dry_run=dry_run)

        # Log summary of results
        logger.info("Label operation completed successfully")
        logger.info(
            f"Summary: Created={len(results['created'])}, "
            f"Updated={len(results['updated'])}, "
            f"Deleted={len(results['deleted'])}, "
            f"Unchanged={len(results['unchanged'])}"
        )

        return 0

    except ValueError as e:
        logger.error(str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except RuntimeError as e:
        logger.error(str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1
