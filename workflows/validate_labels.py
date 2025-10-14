#!/usr/bin/env python3
"""
Validate labels workflow script for GitHub issue label maintenance.

This module validates GitHub issue labels, detects anomalies, and initializes
missing status labels to ensure consistent workflow state.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from github import GithubException

from mcp_coder.utils import get_github_repository_url
from mcp_coder.utils.github_operations.issue_manager import IssueData, IssueManager
from mcp_coder.utils.github_operations.labels_manager import LabelsManager
from mcp_coder.utils.log_utils import setup_logging
from workflows.label_config import load_labels_config

# Setup logger
logger = logging.getLogger(__name__)


class LabelLookups(TypedDict):
    """TypedDict for label lookup data structures."""
    id_to_name: dict[str, str]        # internal_id -> label_name
    all_names: set[str]               # All workflow label names
    name_to_category: dict[str, str]  # label_name -> category
    name_to_id: dict[str, str]        # label_name -> internal_id


# Timeout thresholds in minutes for bot_busy labels
STALE_TIMEOUTS = {
    "implementing": 60,
    "planning": 15,
    "pr_creating": 15
}


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments including project directory and log level.
    
    Returns:
        Namespace with: project_dir, log_level, dry_run
    """
    parser = argparse.ArgumentParser(
        description="Validate workflow status labels for GitHub repository."
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
        help="Preview validation results without making changes"
    )
    
    return parser.parse_args()


def resolve_project_dir(project_dir_arg: Optional[str]) -> Path:
    """Convert project directory argument to absolute Path, with validation.
    
    Args:
        project_dir_arg: Project directory path string or None
        
    Returns:
        Absolute Path to validated project directory
        
    Raises:
        SystemExit: On validation errors
    """
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
    """Main entry point for label validation workflow."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging BEFORE any other operations that might use logger
    setup_logging(args.log_level)
    
    # Now resolve project directory (which may use logger)
    project_dir = resolve_project_dir(args.project_dir)
    
    logger.info("Starting validate labels workflow...")
    logger.info(f"Project directory: {project_dir}")
    
    # Get repository URL for context logging
    try:
        repo_url = get_github_repository_url(project_dir)
        if repo_url:
            # Extract owner/repo format for logging
            parts = repo_url.rstrip('/').split('/')
            repo_name = f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else repo_url
            logger.info(f"Repository: {repo_name}")
        else:
            logger.error("Failed to get repository URL")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to get repository URL: {e}")
        sys.exit(1)
    
    # Log dry-run mode status
    if args.dry_run:
        logger.info("DRY RUN MODE: Changes will be previewed only")
    
    # Load configuration
    logger.info("Loading label configuration...")
    config_path = project_dir / "workflows" / "config" / "labels.json"
    try:
        labels_config = load_labels_config(config_path)
        logger.debug(f"Loaded {len(labels_config['workflow_labels'])} workflow labels")
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Fetch issues (open only)
    logger.info("Fetching open issues from GitHub...")
    try:
        issue_manager = IssueManager(project_dir)
        issues = issue_manager.list_issues(state="open", include_pull_requests=False)
        logger.info(f"Found {len(issues)} open issues")
    except GithubException as e:
        logger.error(f"GitHub API error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to fetch issues from GitHub: {e}")
        sys.exit(1)
    
    # TODO: Process issues (Step 3)
    # TODO: Display results (Step 4)
    
    logger.info("Label validation workflow completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
