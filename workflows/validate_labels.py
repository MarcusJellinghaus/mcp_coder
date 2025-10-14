#!/usr/bin/env python3
"""
Validate labels workflow script for GitHub issue label maintenance.

This module validates GitHub issue labels, detects anomalies, and initializes
missing status labels to ensure consistent workflow state.
"""

import argparse
import logging
import sys
from datetime import datetime, timezone
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


def build_label_lookups(labels_config: Dict[str, Any]) -> LabelLookups:
    """Build lookup dictionaries from label configuration.
    
    Args:
        labels_config: Loaded label configuration from JSON
        
    Returns:
        LabelLookups TypedDict with all lookup structures
    """
    # Initialize empty data structures
    id_to_name: dict[str, str] = {}
    all_names: set[str] = set()
    name_to_category: dict[str, str] = {}
    name_to_id: dict[str, str] = {}
    
    # Loop through workflow labels and populate all lookups
    for label in labels_config["workflow_labels"]:
        internal_id = label["internal_id"]
        label_name = label["name"]
        category = label["category"]
        
        # Populate all lookup structures
        id_to_name[internal_id] = label_name
        all_names.add(label_name)
        name_to_category[label_name] = category
        name_to_id[label_name] = internal_id
    
    # Return LabelLookups TypedDict
    return LabelLookups(
        id_to_name=id_to_name,
        all_names=all_names,
        name_to_category=name_to_category,
        name_to_id=name_to_id
    )


def calculate_elapsed_minutes(timestamp_str: str) -> int:
    """Calculate minutes elapsed since given ISO timestamp.
    
    Args:
        timestamp_str: ISO format timestamp string (may have 'Z' suffix)
        
    Returns:
        Integer minutes elapsed since the timestamp
        
    Example:
        >>> elapsed = calculate_elapsed_minutes("2025-10-14T10:30:00Z")
        >>> print(f"Elapsed: {elapsed} minutes")
    """
    # Handle 'Z' suffix by replacing with UTC offset
    cleaned_timestamp = timestamp_str.replace('Z', '+00:00')
    
    # Parse ISO format timestamp
    timestamp = datetime.fromisoformat(cleaned_timestamp)
    
    # Calculate elapsed time
    elapsed_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()
    
    # Convert to minutes and return as integer
    return int(elapsed_seconds / 60)


def check_status_labels(
    issue: IssueData,
    workflow_label_names: set[str]
) -> tuple[int, list[str]]:
    """Check how many workflow status labels an issue has.
    
    Args:
        issue: Issue data from IssueManager
        workflow_label_names: Set of all valid workflow label names
        
    Returns:
        Tuple of (count, list_of_status_labels)
        
    Example:
        >>> count, labels = check_status_labels(issue, workflow_names)
        >>> if count == 0:
        ...     print("Issue needs initialization")
        >>> elif count > 1:
        ...     print(f"ERROR: Multiple labels: {labels}")
    """
    # Get issue labels list
    issue_labels = issue["labels"]
    
    # Filter to only workflow status labels
    status_labels = [label for label in issue_labels if label in workflow_label_names]
    
    # Return count and list of status labels
    return (len(status_labels), status_labels)


def check_stale_bot_process(
    issue: IssueData,
    label_name: str,
    internal_id: str,
    issue_manager: IssueManager
) -> tuple[bool, Optional[int]]:
    """Check if a bot_busy label has exceeded its timeout threshold.
    
    Args:
        issue: Issue data
        label_name: The bot_busy label name to check
        internal_id: The internal_id of the label (for timeout lookup)
        issue_manager: IssueManager instance for API calls
        
    Returns:
        Tuple of (is_stale, elapsed_minutes)
        - is_stale: True if label exceeded timeout
        - elapsed_minutes: Minutes since label was applied, or None if not found
        
    Raises:
        GithubException: If API call fails (per Decision #1 - let exceptions propagate)
        
    Note:
        Unlike other issue_manager methods, this intentionally does NOT catch exceptions,
        allowing the script to fail fast on API errors rather than silently skipping issues.
        This ensures we don't miss API problems and maintains data integrity.
        
    Algorithm:
        1. Get events for issue via issue_manager.get_issue_events()
           Note: This will raise exceptions on API errors (Decision #1)
        2. Filter to "labeled" events with matching label_name
        3. Find most recent such event
        4. Calculate elapsed time using calculate_elapsed_minutes() helper
        5. Compare against STALE_TIMEOUTS[internal_id]
        6. Return (is_stale, elapsed_minutes)
    """
    # Check if internal_id has a timeout threshold, return (False, None) if not
    if internal_id not in STALE_TIMEOUTS:
        return (False, None)
    
    # Get events for issue (will raise GithubException on API errors)
    events = issue_manager.get_issue_events(issue["number"])
    
    # Filter to "labeled" events with matching label_name
    labeled_events = [
        event for event in events
        if event["event"] == "labeled" and event["label"] == label_name
    ]
    
    # If no matching events found, return (False, None)
    if not labeled_events:
        return (False, None)
    
    # Find most recent labeled event
    most_recent_event = max(labeled_events, key=lambda e: e["created_at"])
    
    # Calculate elapsed time using helper
    elapsed = calculate_elapsed_minutes(most_recent_event["created_at"])
    
    # Check if stale by comparing against timeout threshold
    is_stale = elapsed > STALE_TIMEOUTS[internal_id]
    
    # Return (is_stale, elapsed_minutes)
    return (is_stale, elapsed)


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
