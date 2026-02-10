"""Issue statistics functions for coordinator issue-stats command.

This module provides core functionality to analyze and display statistics for issues
in a GitHub repository, grouped by workflow status labels and categories.

Functions are moved from workflows/issue_stats.py as part of consolidating
CLI functionality into the cli/commands structure.
"""

from typing import Any

from ....utils.github_operations.issue_manager import IssueData


def validate_issue_labels(
    issue: IssueData, valid_status_labels: set[str]
) -> tuple[bool, str]:
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
    status_labels = [label for label in issue["labels"] if label in valid_status_labels]

    if len(status_labels) == 0:
        return (False, "no_status")
    elif len(status_labels) > 1:
        return (False, "multiple_status")
    else:
        return (True, "")


def filter_ignored_issues(
    issues: list[IssueData], ignore_labels: list[str]
) -> list[IssueData]:
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
        for label in issue["labels"]:
            if label in ignore_labels:
                has_ignored_label = True
                break

        if not has_ignored_label:
            filtered.append(issue)

    return filtered


def group_issues_by_category(
    issues: list[IssueData], labels_config: dict[str, Any]
) -> dict[str, dict[str, list[IssueData]]]:
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
    label_to_category: dict[str, str] = {}
    valid_status_labels: set[str] = set()

    for label in labels_config["workflow_labels"]:
        label_name = label["name"]
        label_category = label["category"]
        label_to_category[label_name] = label_category
        valid_status_labels.add(label_name)

    # Initialize result structure
    result: dict[str, dict[str, list[IssueData]]] = {
        "human_action": {},
        "bot_pickup": {},
        "bot_busy": {},
        "errors": {"no_status": [], "multiple_status": []},
    }

    # Initialize empty lists for each label
    for label in labels_config["workflow_labels"]:
        category = label["category"]
        label_name = label["name"]
        result[category][label_name] = []

    # Process each issue
    for issue in issues:
        is_valid, error_type = validate_issue_labels(issue, valid_status_labels)

        if not is_valid:
            result["errors"][error_type].append(issue)
        else:
            # Find the single valid status label
            status_label = None
            for label in issue["labels"]:
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
    return title[: max_length - 3] + "..."


def format_issue_line(
    issue: IssueData, repo_url: str, max_title_length: int = 80
) -> str:
    """Format a single-line display for an issue.

    Args:
        issue: IssueData dictionary
        repo_url: Repository URL
        max_title_length: Maximum title length before truncation

    Returns:
        Formatted string: "    - #{number}: {title} ({url})"
    """
    title = truncate_title(issue["title"], max_title_length)
    url = f"{repo_url}/issues/{issue['number']}"
    return f"    - #{issue['number']}: {title} ({url})"


def display_statistics(
    grouped_issues: dict[str, dict[str, list[IssueData]]],
    labels_config: dict[str, Any],
    repo_url: str,
    filter_category: str = "all",
    show_details: bool = False,
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
            ("human_action", "=== Human Action Required ==="),
            ("bot_pickup", "=== Bot Should Pickup ==="),
            ("bot_busy", "=== Bot Busy ==="),
        ]
    elif filter_category == "human":
        categories_to_display = [("human_action", "=== Human Action Required ===")]
    elif filter_category == "bot":
        categories_to_display = [
            ("bot_pickup", "=== Bot Should Pickup ==="),
            ("bot_busy", "=== Bot Busy ==="),
        ]

    # Display each category
    for category_key, category_title in categories_to_display:
        print(category_title)

        # Get labels for this category in order
        category_labels = [
            label
            for label in labels_config["workflow_labels"]
            if label["category"] == category_key
        ]

        for label_config in category_labels:
            label_name = label_config["name"]
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

    no_status_count = len(grouped_issues["errors"]["no_status"])
    multiple_status_count = len(grouped_issues["errors"]["multiple_status"])

    issue_word = "issue" if no_status_count == 1 else "issues"
    print(f"  No status label: {no_status_count} {issue_word}")
    if show_details and no_status_count > 0:
        for issue in grouped_issues["errors"]["no_status"]:
            print(format_issue_line(issue, repo_url))
        print()

    issue_word = "issue" if multiple_status_count == 1 else "issues"
    print(f"  Multiple status labels: {multiple_status_count} {issue_word}")
    if show_details and multiple_status_count > 0:
        for issue in grouped_issues["errors"]["multiple_status"]:
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

    print(
        f"\nTotal: {total_issues} open issues ({valid_issues} valid, {error_issues} errors)"
    )
