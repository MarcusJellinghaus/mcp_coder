"""Validation helpers for issue operations.

This module provides standalone validation functions extracted from IssueManager
for use by the mixin classes and manager.
"""

import logging

logger = logging.getLogger(__name__)

__all__ = [
    "validate_issue_number",
    "validate_comment_id",
]


def validate_issue_number(issue_number: int) -> bool:
    """Validate issue number.

    Args:
        issue_number: Issue number to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(issue_number, int) or issue_number <= 0:
        logger.error(
            f"Invalid issue number: {issue_number}. Must be a positive integer."
        )
        return False
    return True


def validate_comment_id(comment_id: int) -> bool:
    """Validate comment ID.

    Args:
        comment_id: Comment ID to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(comment_id, int) or comment_id <= 0:
        logger.error(f"Invalid comment ID: {comment_id}. Must be a positive integer.")
        return False
    return True
