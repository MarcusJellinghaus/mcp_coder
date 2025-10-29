#!/usr/bin/env python3
"""
Define labels workflow script for GitHub repository label management.

This module provides functionality to define and apply workflow status labels
to a GitHub repository, ensuring consistent label definitions across projects.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from mcp_coder.utils import get_github_repository_url
from mcp_coder.utils.github_operations.label_config import (
    get_labels_config_path,
    load_labels_config,
)
from mcp_coder.utils.github_operations.labels_manager import LabelsManager
from mcp_coder.utils.log_utils import setup_logging

# Setup logger
logger = logging.getLogger(__name__)


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


def apply_labels(
    project_dir: Path,
    workflow_labels: list[tuple[str, str, str]],
    dry_run: bool = False
) -> dict[str, list[str]]:
    """Apply workflow labels to repository.
    
    Orchestrator function that:
    1. Fetches existing labels from GitHub
    2. Calculates required changes
    3. Applies changes via LabelsManager API calls (unless dry_run=True)
    4. Logs all actions at INFO level
    5. Fails fast on any API error
    
    Args:
        project_dir: Path to project directory (must be git repo)
        workflow_labels: List of (name, color, description) tuples for target labels
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
    changes = calculate_label_changes(existing_labels, workflow_labels)
    
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
        for name, color, description in workflow_labels
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


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments including project directory and log level."""
    parser = argparse.ArgumentParser(
        description="Define workflow status labels for GitHub repository."
    )
    parser.add_argument(
        "--project-dir",
        metavar="PATH",
        help="Project directory path (default: current directory)"
    )
    parser.add_argument(
        "--log-level",
        type=str.upper,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without applying them"
    )

    return parser.parse_args()


def resolve_project_dir(project_dir_arg: Optional[str]) -> Path:
    """Convert project directory argument to absolute Path, with validation."""
    # Use current directory if no argument provided
    if project_dir_arg is None:
        project_path = Path.cwd()
    else:
        project_path = Path(project_dir_arg)
    
    # Resolve to absolute path
    try:
        project_path = project_path.resolve()
    except (OSError, ValueError) as e:
        logger.error(f"Invalid project directory path: {e}")
        sys.exit(1)
    
    # Validate directory exists
    if not project_path.exists():
        logger.error(f"Project directory does not exist: {project_path}")
        sys.exit(1)
    
    # Validate it's a directory
    if not project_path.is_dir():
        logger.error(f"Project path is not a directory: {project_path}")
        sys.exit(1)
    
    # Validate directory is accessible
    try:
        # Test read access by listing directory
        list(project_path.iterdir())
    except PermissionError:
        logger.error(f"No read access to project directory: {project_path}")
        sys.exit(1)
    
    # Validate directory contains .git subdirectory
    git_dir = project_path / ".git"
    if not git_dir.exists():
        logger.error(f"Project directory is not a git repository: {project_path}")
        sys.exit(1)
    
    return project_path


def main() -> None:
    """Main entry point for label definition workflow."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging BEFORE any other operations that might use logger
    setup_logging(args.log_level)
    
    # Now resolve project directory (which may use logger)
    project_dir = resolve_project_dir(args.project_dir)
    
    logger.info("Starting define labels workflow...")
    logger.info(f"Project directory: {project_dir}")
    
    # Get repository name for context logging
    try:
        repo_url = get_github_repository_url(project_dir)
        repo_name = repo_url.split('/')[-1] if repo_url else str(project_dir.name)
        logger.info(f"Repository: {repo_name}")
    except Exception:
        # If we can't get repo name, just skip it
        pass
    
    # Load labels from JSON config using shared module
    # Tries project's local config first, falls back to package bundled config
    try:
        config_path = get_labels_config_path(project_dir)
        labels_config = load_labels_config(config_path)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Extract workflow labels and convert to tuple format for GitHub API
    workflow_labels = [
        (label['name'], label['color'], label['description'])
        for label in labels_config['workflow_labels']
    ]
    
    # Log dry-run mode status
    if args.dry_run:
        logger.info("DRY RUN MODE: Changes will be previewed only")
    
    # Apply labels to repository
    try:
        results = apply_labels(project_dir, workflow_labels, dry_run=args.dry_run)
        
        # Log summary of results
        logger.info("Label operation completed successfully")
        logger.info(f"Summary: Created={len(results['created'])}, "
                   f"Updated={len(results['updated'])}, "
                   f"Deleted={len(results['deleted'])}, "
                   f"Unchanged={len(results['unchanged'])}")
        
        sys.exit(0)
        
    except SystemExit:
        # Re-raise SystemExit from apply_labels (fail fast on errors)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in main workflow: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
