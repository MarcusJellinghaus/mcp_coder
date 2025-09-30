#!/usr/bin/env python3
"""
Define labels workflow script for GitHub repository label management.

This module provides functionality to define and apply workflow status labels
to a GitHub repository, ensuring consistent label definitions across projects.
"""

import logging
import re
import sys
from pathlib import Path

from mcp_coder.utils.github_operations.labels_manager import LabelsManager

# Setup logger
logger = logging.getLogger(__name__)


# Workflow status labels definition
# Format: (name, color, description)
# Colors are 6-character hex codes WITHOUT '#' prefix (GitHub API format)
WORKFLOW_LABELS = [
    ("status-01:created", "10b981", "Fresh issue, may need refinement"),
    ("status-02:awaiting-planning", "6ee7b7", "Issue is refined and ready for implementation planning"),
    ("status-03:planning", "a7f3d0", "Implementation plan being drafted (auto/in-progress)"),
    ("status-04:plan-review", "3b82f6", "First implementation plan available for review/discussion"),
    ("status-05:plan-ready", "93c5fd", "Implementation plan approved, ready to code"),
    ("status-06:implementing", "bfdbfe", "Code being written (auto/in-progress)"),
    ("status-07:code-review", "f59e0b", "Implementation complete, needs code review"),
    ("status-08:ready-pr", "fbbf24", "Approved for pull request creation"),
    ("status-09:pr-creating", "fed7aa", "Bot is creating the pull request (auto/in-progress)"),
    ("status-10:pr-created", "8b5cf6", "Pull request created, awaiting approval/merge"),
]


def _validate_color_format(color: str) -> bool:
    """Validate that color is a 6-character hex code.
    
    Args:
        color: Color string to validate
        
    Returns:
        True if valid 6-character hex code, False otherwise
    """
    return isinstance(color, str) and bool(re.match(r'^[0-9A-Fa-f]{6}$', color))


# Validate all colors at module load time
def _validate_workflow_labels() -> None:
    """Validate WORKFLOW_LABELS structure and color formats at module load.
    
    Raises:
        ValueError: If any label has invalid structure or color format
    """
    for label in WORKFLOW_LABELS:
        if not isinstance(label, tuple) or len(label) != 3:
            raise ValueError(f"Invalid label structure: {label}. Expected (name, color, description) tuple.")
        
        name, color, description = label
        
        if not isinstance(name, str) or not name:
            raise ValueError(f"Invalid label name: {name}. Must be non-empty string.")
        
        if not _validate_color_format(color):
            raise ValueError(f"Invalid color format for label '{name}': {color}. Expected 6-character hex code.")
        
        if not isinstance(description, str):
            raise ValueError(f"Invalid description for label '{name}': {description}. Must be string.")


# Perform validation at module load
_validate_workflow_labels()


def calculate_label_changes(
    existing_labels: list[tuple[str, str, str]],
    target_labels: list[tuple[str, str, str]]
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
        'created': [],
        'updated': [],
        'deleted': [],
        'unchanged': []
    }
    
    # Build existing_map keyed by label name for O(1) lookup
    # Map format: {label_name: (color, description)}
    existing_map: dict[str, tuple[str, str]] = {
        name: (color, description)
        for name, color, description in existing_labels
    }
    
    # Build target_names set for O(1) lookup during deletion check
    target_names = {name for name, _, _ in target_labels}
    
    # Process target labels: determine create, update, or unchanged
    for name, color, description in target_labels:
        if name not in existing_map:
            # Label doesn't exist - needs to be created
            result['created'].append(name)
        else:
            # Label exists - check if update needed
            existing_color, existing_description = existing_map[name]
            if existing_color == color and existing_description == description:
                # No changes needed - identical
                result['unchanged'].append(name)
            else:
                # Color or description differs - needs update
                result['updated'].append(name)
    
    # Process existing labels: find status-* labels to delete
    # Only delete labels starting with 'status-' that are not in target
    for name in existing_map:
        if name.startswith('status-') and name not in target_names:
            result['deleted'].append(name)
    
    return result


def apply_labels(project_dir: Path, dry_run: bool = False) -> dict[str, list[str]]:
    """Apply workflow labels to repository.
    
    Orchestrator function that:
    1. Fetches existing labels from GitHub
    2. Calculates required changes
    3. Applies changes via LabelsManager API calls (unless dry_run=True)
    4. Logs all actions at INFO level
    5. Fails fast on any API error
    
    Args:
        project_dir: Path to project directory (must be git repo)
        dry_run: If True, only preview changes without applying
    
    Returns:
        Dict with keys: 'created', 'updated', 'deleted', 'unchanged'
        Each value is a list of label names
        
    Raises:
        SystemExit: On API errors (exit code 1)
        ValueError: On invalid project_dir or missing GitHub token
    """
    try:
        # Initialize LabelsManager (validates token and repo connection)
        labels_manager = LabelsManager(project_dir)
    except (ValueError, Exception) as e:
        logger.error(f"Failed to initialize LabelsManager: {e}")
        sys.exit(1)
    
    # Fetch existing labels from GitHub
    try:
        existing_labels_data = labels_manager.get_labels()
    except Exception as e:
        logger.error(f"Failed to fetch existing labels: {e}")
        sys.exit(1)
    
    # Convert LabelData list to tuple format for calculate_label_changes
    existing_labels = [
        (label['name'], label['color'], label['description'])
        for label in existing_labels_data
    ]
    
    # Calculate required changes
    changes = calculate_label_changes(existing_labels, WORKFLOW_LABELS)
    
    # Preview mode - log and return without applying
    if dry_run:
        logger.info("DRY RUN MODE - Preview of changes:")
        if changes['created']:
            logger.info(f"  Would create {len(changes['created'])} labels: {', '.join(changes['created'])}")
        if changes['updated']:
            logger.info(f"  Would update {len(changes['updated'])} labels: {', '.join(changes['updated'])}")
        if changes['deleted']:
            logger.info(f"  Would delete {len(changes['deleted'])} labels: {', '.join(changes['deleted'])}")
        if changes['unchanged']:
            logger.info(f"  {len(changes['unchanged'])} labels unchanged")
        return changes
    
    # Build lookup map for target label details
    target_map = {
        name: (color, description)
        for name, color, description in WORKFLOW_LABELS
    }
    
    # Apply changes - CREATE new labels
    for label_name in changes['created']:
        color, description = target_map[label_name]
        try:
            labels_manager.create_label(label_name, color, description)
            logger.info(f"Created: {label_name}")
        except Exception as e:
            logger.error(f"Failed to create label '{label_name}': {e}")
            sys.exit(1)
    
    # Apply changes - UPDATE existing labels
    for label_name in changes['updated']:
        color, description = target_map[label_name]
        try:
            labels_manager.update_label(label_name, color=color, description=description)
            logger.info(f"Updated: {label_name}")
        except Exception as e:
            logger.error(f"Failed to update label '{label_name}': {e}")
            sys.exit(1)
    
    # Apply changes - DELETE obsolete status-* labels
    for label_name in changes['deleted']:
        try:
            labels_manager.delete_label(label_name)
            logger.info(f"Deleted: {label_name}")
        except Exception as e:
            logger.error(f"Failed to delete label '{label_name}': {e}")
            sys.exit(1)
    
    # Unchanged labels - skip API calls (idempotent)
    # No logging for unchanged labels to reduce noise
    
    return changes
