#!/usr/bin/env python3
"""
Issue statistics workflow script for GitHub repository issue tracking.

This module provides functionality to analyze and display statistics for issues
in a GitHub repository, grouped by workflow status labels and categories.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mcp_coder.utils import get_github_repository_url
from mcp_coder.utils.github_operations.issue_manager import IssueData, IssueManager
from mcp_coder.utils.github_operations.label_config import (
    get_labels_config_path,
    load_labels_config,
)
from mcp_coder.utils.log_utils import setup_logging

# Setup logger
logger = logging.getLogger(__name__)


def validate_issue_labels(
    issue: IssueData,
    valid_status_labels: set[str]
) -> Tuple[bool, str]:
    """Validate that issue has exactly one valid status label.
    
    Args:
        issue: IssueData dictionary
        valid_status_labels: Set of valid status label names
        
    Returns:
        Tuple of (is_valid, error_type)
        - is_valid: True if exactly one valid status label
        - error_type: "" if valid, "no_status" or "multiple_status" if invalid
    """
    # Filter issue labels to only those that are valid status labels
    status_labels = [label for label in issue['labels'] if label in valid_status_labels]
    
    if len(status_labels) == 0:
        return (False, "no_status")
    elif len(status_labels) > 1:
        return (False, "multiple_status")
    else:
        return (True, "")


def filter_ignored_issues(
    issues: List[IssueData],
    ignore_labels: List[str]
) -> List[IssueData]:
    """Filter out issues that have any of the ignored labels.
    
    Args:
        issues: List of IssueData dictionaries
        ignore_labels: List of label names to ignore
        
    Returns:
        Filtered list of issues without any ignored labels
    """
    if not ignore_labels:
        return issues
    
    filtered = []
    for issue in issues:
        has_ignored_label = False
        for label in issue['labels']:
            if label in ignore_labels:
                has_ignored_label = True
                break
        
        if not has_ignored_label:
            filtered.append(issue)
    
    return filtered


def group_issues_by_category(
    issues: List[IssueData],
    labels_config: Dict[str, Any]
) -> Dict[str, Dict[str, List[IssueData]]]:
    """Group issues by category and status label.
    
    Args:
        issues: List of IssueData dictionaries
        labels_config: Label configuration from JSON
        
    Returns:
        Dict structure:
        {
            'human_action': {
                'status-01:created': [issue1, issue2],
                'status-04:plan-review': []
            },
            'bot_pickup': {...},
            'bot_busy': {...},
            'errors': {
                'no_status': [issue_without_label],
                'multiple_status': [issue_with_multiple]
            }
        }
    """
    # Build lookup maps
    label_to_category: Dict[str, str] = {}
    valid_status_labels: set[str] = set()
    
    for label in labels_config['workflow_labels']:
        label_name = label['name']
        label_category = label['category']
        label_to_category[label_name] = label_category
        valid_status_labels.add(label_name)
    
    # Initialize result structure
    result: Dict[str, Dict[str, List[IssueData]]] = {
        'human_action': {},
        'bot_pickup': {},
        'bot_busy': {},
        'errors': {'no_status': [], 'multiple_status': []}
    }
    
    # Initialize empty lists for each label
    for label in labels_config['workflow_labels']:
        category = label['category']
        label_name = label['name']
        result[category][label_name] = []
    
    # Process each issue
    for issue in issues:
        is_valid, error_type = validate_issue_labels(issue, valid_status_labels)
        
        if not is_valid:
            result['errors'][error_type].append(issue)
        else:
            # Find the single valid status label
            status_label = None
            for label in issue['labels']:
                if label in valid_status_labels:
                    status_label = label
                    break
            
            if status_label:
                category = label_to_category[status_label]
                result[category][status_label].append(issue)
    
    return result


def truncate_title(title: str, max_length: int = 80) -> str:
    """Truncate title to max length with ellipsis.
    
    Args:
        title: Original title
        max_length: Maximum length (default: 80)
        
    Returns:
        Truncated title with "..." if needed
    """
    if len(title) <= max_length:
        return title
    return title[:max_length-3] + "..."


def format_issue_line(issue: IssueData, repo_url: str, max_title_length: int = 80) -> str:
    """Format a single-line display for an issue.
    
    Args:
        issue: IssueData dictionary
        repo_url: Repository URL
        max_title_length: Maximum title length before truncation
        
    Returns:
        Formatted string: "    - #{number}: {title} ({url})"
    """
    title = truncate_title(issue['title'], max_title_length)
    url = f"{repo_url}/issues/{issue['number']}"
    return f"    - #{issue['number']}: {title} ({url})"


def display_statistics(
    grouped_issues: Dict[str, Dict[str, List[IssueData]]],
    labels_config: Dict[str, Any],
    repo_url: str,
    filter_category: str = "all",
    show_details: bool = False
) -> None:
    """Display formatted statistics to console.
    
    Args:
        grouped_issues: Output from group_issues_by_category()
        labels_config: Label configuration for display order
        repo_url: Repository URL for issue links
        filter_category: 'all', 'human', or 'bot'
        show_details: If True, show individual issues with links
    """
    # Determine which categories to display
    categories_to_display = []
    if filter_category == "all":
        categories_to_display = [
            ('human_action', '=== Human Action Required ==='),
            ('bot_pickup', '=== Bot Should Pickup ==='),
            ('bot_busy', '=== Bot Busy ===')
        ]
    elif filter_category == "human":
        categories_to_display = [
            ('human_action', '=== Human Action Required ===')
        ]
    elif filter_category == "bot":
        categories_to_display = [
            ('bot_pickup', '=== Bot Should Pickup ==='),
            ('bot_busy', '=== Bot Busy ===')
        ]
    
    # Display each category
    for category_key, category_title in categories_to_display:
        print(category_title)
        
        # Get labels for this category in order
        category_labels = [
            label for label in labels_config['workflow_labels']
            if label['category'] == category_key
        ]
        
        for label_config in category_labels:
            label_name = label_config['name']
            issues_list = grouped_issues[category_key].get(label_name, [])
            count = len(issues_list)
            
            # Display count
            issue_word = "issue" if count == 1 else "issues"
            print(f"  {label_name:30s} {count} {issue_word}")
            
            # Display details if requested
            if show_details and count > 0:
                for issue in issues_list:
                    print(format_issue_line(issue, repo_url))
            
            # Add blank line after non-empty details
            if show_details and count > 0:
                print()
        
        # Add blank line after each category
        print()
    
    # Display validation errors (always shown)
    print("=== Validation Errors ===")
    
    no_status_count = len(grouped_issues['errors']['no_status'])
    multiple_status_count = len(grouped_issues['errors']['multiple_status'])
    
    issue_word = "issue" if no_status_count == 1 else "issues"
    print(f"  No status label: {no_status_count} {issue_word}")
    if show_details and no_status_count > 0:
        for issue in grouped_issues['errors']['no_status']:
            print(format_issue_line(issue, repo_url))
        print()
    
    issue_word = "issue" if multiple_status_count == 1 else "issues"
    print(f"  Multiple status labels: {multiple_status_count} {issue_word}")
    if show_details and multiple_status_count > 0:
        for issue in grouped_issues['errors']['multiple_status']:
            print(format_issue_line(issue, repo_url))
        print()
    
    # Calculate and display totals
    total_issues = 0
    valid_issues = 0
    error_issues = no_status_count + multiple_status_count
    
    for category_key, _ in categories_to_display:
        for label_name, issues_list in grouped_issues[category_key].items():
            count = len(issues_list)
            total_issues += count
            valid_issues += count
    
    total_issues += error_issues
    
    print(f"\nTotal: {total_issues} open issues ({valid_issues} valid, {error_issues} errors)")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Namespace with: project_dir, log_level, filter, details, ignore_labels
    """
    parser = argparse.ArgumentParser(
        description="Display issue statistics for GitHub repository."
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
        "--filter",
        type=str.lower,
        choices=["all", "human", "bot"],
        default="all",
        help="Filter issues by category (default: all)"
    )
    parser.add_argument(
        "--details",
        action="store_true",
        default=False,
        help="Show individual issue details with links"
    )
    parser.add_argument(
        "--ignore-labels",
        action="append",
        dest="ignore_labels",
        help="Additional labels to ignore beyond JSON config defaults (can be used multiple times)"
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
    """Main entry point for issue statistics workflow."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging BEFORE any other operations that might use logger
    setup_logging(args.log_level)
    
    # Now resolve project directory (which may use logger)
    project_dir = resolve_project_dir(args.project_dir)
    
    logger.info("Starting issue statistics workflow...")
    logger.info(f"Project directory: {project_dir}")
    
    # Get repository URL for context logging and issue links
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
    
    # Load configuration
    # Tries project's local config first, falls back to package bundled config
    logger.info("Loading label configuration...")
    try:
        config_path = get_labels_config_path(project_dir)
        labels_config = load_labels_config(config_path)
        logger.debug(f"Loaded {len(labels_config['workflow_labels'])} workflow labels")
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Fetch issues (open only)
    logger.info(f"Fetching open issues from GitHub...")
    try:
        issue_manager = IssueManager(project_dir)
        issues = issue_manager.list_issues(state="open", include_pull_requests=False)
        logger.info(f"Found {len(issues)} open issues")
    except Exception as e:
        logger.error(f"Failed to fetch issues from GitHub: {e}")
        sys.exit(1)
    
    # Build ignore list (JSON defaults + CLI additions)
    ignore_labels = labels_config.get('ignore_labels', []) + (args.ignore_labels or [])
    if ignore_labels:
        logger.debug(f"Ignore list: {ignore_labels}")
    
    # Filter out ignored issues
    filtered_issues = filter_ignored_issues(issues, ignore_labels)
    ignored_count = len(issues) - len(filtered_issues)
    if ignored_count > 0:
        logger.info(f"Ignored {ignored_count} issues with labels: {', '.join(ignore_labels)}")
    
    # Group by category and validate
    logger.debug("Grouping issues by category and validating labels...")
    grouped = group_issues_by_category(filtered_issues, labels_config)
    
    # Log validation warnings
    error_count = len(grouped['errors']['no_status']) + len(grouped['errors']['multiple_status'])
    if grouped['errors']['no_status']:
        logger.warning(f"Found {len(grouped['errors']['no_status'])} issues without status labels")
    if grouped['errors']['multiple_status']:
        logger.warning(f"Found {len(grouped['errors']['multiple_status'])} issues with multiple status labels")
    
    # Display statistics
    logger.debug(f"Displaying statistics (filter={args.filter}, details={args.details})")
    display_statistics(grouped, labels_config, repo_url, args.filter, args.details)
    
    logger.info("Issue statistics workflow completed successfully")


if __name__ == "__main__":
    main()
