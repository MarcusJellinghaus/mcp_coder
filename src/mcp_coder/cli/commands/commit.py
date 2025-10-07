"""Commit commands for the MCP Coder CLI."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

from ...utils.clipboard import (
    get_clipboard_text,
    parse_commit_message,
    validate_commit_message,
)
from ...utils.commit_operations import generate_commit_message_with_llm
from ...utils.git_operations import (
    commit_staged_files,
    get_git_diff_for_commit,
    is_git_repository,
    stage_all_changes,
)
from ..utils import parse_llm_method_from_args

logger = logging.getLogger(__name__)


def execute_commit_auto(args: argparse.Namespace) -> int:
    """Execute commit auto command with optional preview. Returns exit code."""
    logger.info("Starting commit auto with preview=%s", args.preview)

    project_dir = Path(args.project_dir) if args.project_dir else Path.cwd()

    # 1. Validate git repository
    success, error = validate_git_repository(project_dir)
    if not success:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    # 2. Parse LLM method and generate commit message
    provider, method = parse_llm_method_from_args(args.llm_method)
    success, commit_message, error = generate_commit_message_with_llm(
        project_dir, provider, method
    )
    if not success:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    # 3. Preview mode - simple inline confirmation
    if args.preview:
        print("\nGenerated commit message:")
        print("=" * 50)
        print(commit_message)
        print("=" * 50)

        response = input("\nProceed with commit? (Y/n): ").strip().lower()
        # Handle case-insensitive input, check first letter, only check for non-default (n/no)
        if response.startswith("n"):  # 'n', 'no', 'nope', etc.
            print("Commit cancelled.")
            return 0
        # Everything else (empty, 'y', 'yes', 'yeah', etc.) proceeds as default

    # 4. Create commit
    commit_result = commit_staged_files(commit_message, project_dir)
    if not commit_result["success"]:
        print(f"Error: {commit_result['error']}", file=sys.stderr)
        return 2

    # Show commit message summary in output
    commit_lines = commit_message.strip().split("\n")
    first_line = commit_lines[0].strip()
    total_lines = len([line for line in commit_lines if line.strip()])

    print(f"SUCCESS: Commit created: {commit_result['commit_hash']}")
    if total_lines == 1:
        print(f"Message: {first_line}")
    else:
        print(f"Message: {first_line} ({total_lines} lines)")
    return 0


def validate_git_repository(project_dir: Path) -> Tuple[bool, Optional[str]]:
    """Validate current directory is git repo with changes."""
    if not is_git_repository(project_dir):
        return False, "Not a git repository"

    # Check if there are any changes to stage or already staged
    try:
        git_diff = get_git_diff_for_commit(project_dir)
        if git_diff is None:
            return False, "Unable to determine git status"

        # If we get an empty diff but there might be unstaged changes,
        # try staging first to see if that produces a diff
        if not git_diff.strip():
            # Try staging all changes
            if stage_all_changes(project_dir):
                git_diff = get_git_diff_for_commit(project_dir)
                if git_diff and git_diff.strip():
                    return True, None

            return False, "No changes to commit"

        return True, None

    except Exception as e:
        logger.error("Error validating git repository: %s", e)
        return False, f"Git validation error: {str(e)}"


def execute_commit_clipboard(args: argparse.Namespace) -> int:
    """Execute commit clipboard command. Returns exit code."""
    logger.info("Starting commit clipboard")

    project_dir = Path(args.project_dir) if args.project_dir else Path.cwd()

    # 1. Validate git repository
    success, error = validate_git_repository(project_dir)
    if not success:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    # 2. Get and validate commit message from clipboard
    success, commit_message, error = get_commit_message_from_clipboard()
    if not success:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    # 3. Stage all changes
    if not stage_all_changes(project_dir):
        print("Error: Failed to stage changes", file=sys.stderr)
        return 2

    # 4. Create commit
    commit_result = commit_staged_files(commit_message, project_dir)
    if not commit_result["success"]:
        print(f"Error: {commit_result['error']}", file=sys.stderr)
        return 2

    # Parse commit message to get summary for user feedback
    summary, _ = parse_commit_message(commit_message)
    print(f"SUCCESS: Successfully committed with message: {summary}")
    if commit_result["commit_hash"]:
        print(f"COMMIT: {commit_result['commit_hash']}")

    return 0


def get_commit_message_from_clipboard() -> Tuple[bool, str, Optional[str]]:
    """Get and validate commit message from clipboard.

    Returns:
        Tuple containing:
        - bool: True if successful, False otherwise
        - str: The formatted commit message (empty string on failure)
        - Optional[str]: Error message if failed, None if successful
    """
    # Get text from clipboard
    success, clipboard_text, error = get_clipboard_text()
    if not success:
        return False, "", error

    # Validate commit message format
    is_valid, validation_error = validate_commit_message(clipboard_text)
    if not is_valid:
        return False, "", f"Invalid commit message format - {validation_error}"

    # Parse message into components (this also formats it properly)
    summary, body = parse_commit_message(clipboard_text)

    # Format the final commit message
    if body:
        formatted_message = f"{summary}\n\n{body}"
    else:
        formatted_message = summary

    logger.debug("Successfully validated clipboard commit message: %s", summary)
    return True, formatted_message, None
