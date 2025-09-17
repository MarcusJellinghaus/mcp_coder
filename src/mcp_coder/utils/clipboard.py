"""Clipboard utilities for commit message handling.

This module provides utilities for accessing clipboard content and validating
commit message formats using tkinter (no external dependencies required).
"""

import logging
import tkinter as tk
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def get_clipboard_text() -> Tuple[bool, str, Optional[str]]:
    """Get text from clipboard using tkinter.

    Returns:
        Tuple containing:
        - bool: True if successful, False otherwise
        - str: The clipboard text (empty string on failure)
        - Optional[str]: Error message if failed, None if successful
    """
    try:
        # Create a temporary tkinter root window
        root = tk.Tk()
        root.withdraw()  # Hide the window

        try:
            # Get clipboard content
            clipboard_text = root.clipboard_get()
            root.destroy()

            if not clipboard_text.strip():
                return False, "", "Clipboard is empty"

            logger.debug("Successfully retrieved clipboard text")
            return True, clipboard_text, None

        except tk.TclError as e:
            root.destroy()
            error_msg = str(e)

            if "CLIPBOARD selection doesn't exist" in error_msg:
                error_msg = "Clipboard is empty"
            elif "couldn't connect to display" in error_msg:
                error_msg = "No display available for clipboard access"
            else:
                error_msg = f"Clipboard access failed: {error_msg}"

            logger.error(f"Clipboard error: {error_msg}")
            return False, "", error_msg

    except Exception as e:
        logger.error(f"Unexpected clipboard error: {e}")
        return False, "", f"Clipboard access failed: {e}"


def validate_commit_message(message: str) -> Tuple[bool, Optional[str]]:
    """Validate commit message format following git conventions.

    Valid formats:
    1. Single line: "fix: resolve authentication bug"
    2. Multi-line with empty second line:
       "feat: add user registration

       Implements user signup with email validation."

    Args:
        message: The commit message to validate

    Returns:
        Tuple containing:
        - bool: True if valid, False otherwise
        - Optional[str]: Error message if invalid, None if valid
    """
    if not message or not message.strip():
        return False, "Commit message cannot be empty"

    lines = message.split("\n")

    # Check first line (summary)
    summary = lines[0].strip()
    if not summary:
        return False, "Commit message cannot be empty"

    # Recommend summary line length (not enforced strictly)
    if len(summary) > 72:
        logger.warning(f"Summary line is {len(summary)} characters (recommend < 72)")

    # Single line commit is always valid
    if len(lines) == 1:
        return True, None

    # Multi-line commit: second line must be empty
    if len(lines) > 1:
        if lines[1].strip():  # Second line is not empty
            return False, "Multi-line commit message must have empty second line"

    logger.debug("Commit message format is valid")
    return True, None


def parse_commit_message(message: str) -> Tuple[str, Optional[str]]:
    """Parse commit message into summary and body components.

    Args:
        message: The commit message to parse

    Returns:
        Tuple containing:
        - str: The summary (first line)
        - Optional[str]: The body (remaining lines after empty line), None if single line
    """
    if not message:
        return "", None

    lines = message.split("\n")
    summary = lines[0].strip()

    # Single line commit
    if len(lines) <= 1:
        return summary, None

    # Multi-line commit: find body after empty line
    if len(lines) > 2 and not lines[1].strip():
        body_lines = [line.rstrip() for line in lines[2:]]
        # Remove trailing empty lines
        while body_lines and not body_lines[-1]:
            body_lines.pop()

        if body_lines:
            body = "\n".join(body_lines)
            return summary, body

    # No valid body found
    return summary, None
