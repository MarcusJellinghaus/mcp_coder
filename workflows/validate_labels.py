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
from typing import Any, Dict, List, Optional

from github import GithubException

from mcp_coder.utils import get_github_repository_url
from mcp_coder.utils.github_operations.issue_manager import IssueData, IssueManager
from mcp_coder.utils.github_operations.label_config import (
    LabelLookups,
    build_label_lookups,
    get_labels_config_path,
    load_labels_config,
)
from mcp_coder.utils.github_operations.labels_manager import LabelsManager
from mcp_coder.utils.log_utils import setup_logging
from mcp_coder.workflows.utils import resolve_project_dir

# Setup logger
logger = logging.getLogger(__name__)


# Timeout thresholds in minutes for bot_busy labels
STALE_TIMEOUTS = {
    "implementing": 60,
    "planning": 15,
    "pr_creating": 15
}


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


def process_issues(
    issues: List[IssueData],
    labels_config: Dict[str, Any],
    issue_manager: IssueManager,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Process all issues and collect validation results.
    
    Args:
        issues: List of issues to process
        labels_config: Label configuration
        issue_manager: IssueManager for API operations
        dry_run: If True, don't make any changes
        
    Returns:
        Results dictionary with structure:
        {
            "processed": 123,
            "skipped": 5,
            "initialized": [issue_numbers],
            "errors": [{"issue": 45, "labels": ["label1", "label2"]}],
            "warnings": [{"issue": 67, "label": "planning", "elapsed": 20}],
            "ok": [issue_numbers]
        }
        
    Note:
        - Logs API call count at DEBUG level (Decision #10)
        - Filters out issues with ANY ignore label (Decision #3)
    """
    # Build label lookups
    label_lookups = build_label_lookups(labels_config)
    workflow_label_names = label_lookups["all_names"]
    name_to_category = label_lookups["name_to_category"]
    name_to_id = label_lookups["name_to_id"]
    id_to_name = label_lookups["id_to_name"]
    
    # Get ignore labels from config
    ignore_labels = set(labels_config.get("ignore_labels", []))
    
    # Initialize API call counter
    api_call_count = 0
    
    # Initialize results dictionary
    results: Dict[str, Any] = {
        "processed": 0,
        "skipped": 0,
        "initialized": [],
        "errors": [],
        "warnings": [],
        "ok": []
    }
    
    # Process each issue
    for issue in issues:
        issue_number = issue["number"]
        issue_labels = set(issue["labels"])
        
        # Filter out issues with ANY ignore label (Decision #3)
        if ignore_labels & issue_labels:
            logger.debug(f"Issue #{issue_number}: Skipped (has ignore label)")
            results["skipped"] += 1
            continue
        
        # Check status label count
        count, status_labels = check_status_labels(issue, workflow_label_names)
        
        # Case 1: No status labels - initialize with "created"
        if count == 0:
            logger.info(f"Issue #{issue_number}: Initializing with 'created' label")
            if not dry_run:
                try:
                    # Get the "created" label name
                    created_label_name = id_to_name["created"]
                    issue_manager.add_labels(issue_number, created_label_name)
                    logger.debug(f"Issue #{issue_number}: Added label '{created_label_name}'")
                except GithubException as e:
                    logger.error(f"Issue #{issue_number}: Failed to add label - {e}")
                    # Let exception propagate per Decision #1
                    raise
            else:
                logger.debug(f"Issue #{issue_number}: DRY RUN - would add 'created' label")
            results["initialized"].append(issue_number)
            results["processed"] += 1
            
        # Case 2: Exactly one status label - check if bot_busy and check for staleness
        elif count == 1:
            label_name = status_labels[0]
            category = name_to_category.get(label_name, "")
            internal_id = name_to_id.get(label_name, "")
            
            # Check if this is a bot_busy label
            if category == "bot_busy" and not dry_run:
                # Check if stale (this makes an API call)
                # Skip in dry-run mode to avoid ALL API calls
                try:
                    is_stale, elapsed = check_stale_bot_process(
                        issue, label_name, internal_id, issue_manager
                    )
                    api_call_count += 1
                    
                    if is_stale and elapsed is not None:
                        logger.warning(
                            f"Issue #{issue_number}: Stale bot process - "
                            f"'{label_name}' for {elapsed} minutes"
                        )
                        results["warnings"].append({
                            "issue": issue_number,
                            "label": label_name,
                            "elapsed": elapsed
                        })
                    else:
                        logger.info(f"Issue #{issue_number}: OK - '{label_name}'")
                        results["ok"].append(issue_number)
                except GithubException as e:
                    logger.error(f"Issue #{issue_number}: API error checking staleness - {e}")
                    # Let exception propagate per Decision #1
                    raise
            else:
                # Not a bot_busy label OR dry-run mode, just mark as OK
                logger.info(f"Issue #{issue_number}: OK - '{label_name}'")
                results["ok"].append(issue_number)
            
            results["processed"] += 1
            
        # Case 3: Multiple status labels - ERROR condition
        else:
            logger.error(
                f"Issue #{issue_number}: Multiple status labels - {status_labels}"
            )
            results["errors"].append({
                "issue": issue_number,
                "labels": status_labels
            })
            results["processed"] += 1
    
    # Log API call count at DEBUG level (Decision #10)
    logger.debug(f"API calls made: {api_call_count}")
    
    return results


def display_summary(results: Dict[str, Any], repo_url: str) -> None:
    """Display validation results summary.
    
    Args:
        results: Results dictionary from process_issues()
        repo_url: Repository URL for generating issue links
        
    Output Format (plain text, Decision #5):
        Summary:
          Total issues processed: 47
          Skipped (ignore labels): 3
          Initialized with 'created': 5
            - Issue #12: Title (url)
            - Issue #45: Title (url)
          Errors (multiple status labels): 2
            - Issue #23: status-01:created, status-03:planning
            - Issue #56: status-04:plan-review, status-06:implementing
          Warnings (stale bot processes): 1
            - Issue #78: planning (20 minutes)
    
    Note: Uses plain text format (no emojis or colors, Decision #5)
    """
    # Print header
    print("Summary:")
    
    # Print counts
    print(f"  Total issues processed: {results['processed']}")
    print(f"  Skipped (ignore labels): {results['skipped']}")
    
    # Print initialized issues count
    initialized_count = len(results['initialized'])
    print(f"  Initialized with 'created': {initialized_count}")
    
    # If initialized issues exist, print each with issue number only
    # Note: We don't have titles or URLs in the results, so we just show issue numbers
    if initialized_count > 0:
        for issue_num in results['initialized']:
            issue_url = f"{repo_url}/issues/{issue_num}"
            print(f"    - Issue #{issue_num} ({issue_url})")
    
    # Print error count
    error_count = len(results['errors'])
    print(f"  Errors (multiple status labels): {error_count}")
    
    # If errors exist, print each with issue number and conflicting labels
    if error_count > 0:
        for error in results['errors']:
            labels_str = ", ".join(error['labels'])
            print(f"    - Issue #{error['issue']}: {labels_str}")
    
    # Print warning count
    warning_count = len(results['warnings'])
    print(f"  Warnings (stale bot processes): {warning_count}")
    
    # If warnings exist, print each with issue number, label, and elapsed time
    if warning_count > 0:
        for warning in results['warnings']:
            print(f"    - Issue #{warning['issue']}: {warning['label']} ({warning['elapsed']} minutes)")


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


def main() -> None:
    """Main entry point for label validation workflow."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging BEFORE any other operations that might use logger
    setup_logging(args.log_level)
    
    # Now resolve project directory (which may use logger)
    try:
        project_dir = resolve_project_dir(args.project_dir)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
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
    
    # Process issues with exception handling (Decision #22)
    try:
        logger.info("Processing issues for validation...")
        results = process_issues(
            issues=issues,
            labels_config=labels_config,
            issue_manager=issue_manager,
            dry_run=args.dry_run
        )
    except GithubException as e:
        logger.error(f"GitHub API error during validation: {e}")
        logger.error("Validation incomplete - some issues were not checked")
        logger.debug("Traceback:", exc_info=True)  # Log full traceback at DEBUG level
        sys.exit(1)
    
    # Display results
    display_summary(results, repo_url)
    
    # Calculate exit code and exit
    # Note: Errors take precedence over warnings (Decision #6)
    has_errors = len(results["errors"]) > 0
    has_warnings = len(results["warnings"]) > 0
    
    if has_errors:
        logger.error(f"Validation completed with {len(results['errors'])} errors")
        sys.exit(1)  # Exit 1 even if warnings also exist
    elif has_warnings:
        logger.warning(f"Validation completed with {len(results['warnings'])} warnings")
        sys.exit(2)
    else:
        logger.info("Validation completed successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
