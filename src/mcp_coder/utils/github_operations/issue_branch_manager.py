"""Branch management operations for GitHub issues."""

import re


def generate_branch_name_from_issue(
    issue_number: int, issue_title: str, max_length: int = 200
) -> str:
    """Generate sanitized branch name matching GitHub's native rules.

    Args:
        issue_number: Issue number (e.g., 123)
        issue_title: Raw issue title (e.g., "Add New Feature - Part 1")
        max_length: Max branch name length in characters (default 200)

    Returns:
        Sanitized branch name (e.g., "123-add-new-feature---part-1")
    """
    # Step 1: Replace " - " with "---" (GitHub-specific rule)
    sanitized = issue_title.replace(" - ", "---")

    # Step 2: Convert to lowercase
    sanitized = sanitized.lower()

    # Step 3: Replace non-alphanumeric (except dash) with dash
    sanitized = re.sub(r"[^a-z0-9-]+", "-", sanitized)

    # Step 4: Replace multiple consecutive dashes with single dash
    # (but preserve "---" from step 1)
    # First, protect "---" by temporarily replacing it
    sanitized = sanitized.replace("---", "\x00")
    sanitized = re.sub(r"-+", "-", sanitized)
    sanitized = sanitized.replace("\x00", "---")

    # Step 5: Strip leading/trailing dashes
    sanitized = sanitized.strip("-")

    # Step 6: Truncate to max_length if needed
    branch_prefix = f"{issue_number}-"
    if sanitized:
        full_branch_name = f"{branch_prefix}{sanitized}"
    else:
        # Handle empty title case
        full_branch_name = str(issue_number)

    if len(full_branch_name) > max_length:
        # Keep issue number prefix and truncate title
        available_for_title = max_length - len(branch_prefix)
        if available_for_title > 0:
            truncated_title = sanitized[:available_for_title].rstrip("-")
            full_branch_name = f"{branch_prefix}{truncated_title}"
        else:
            # If even the prefix is too long, just return the issue number
            full_branch_name = str(issue_number)

    return full_branch_name
