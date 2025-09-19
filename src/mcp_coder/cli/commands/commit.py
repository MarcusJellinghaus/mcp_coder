"""Commit commands for the MCP Coder CLI."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

from ...llm_interface import ask_llm
from ...prompt_manager import get_prompt
from ...utils.clipboard import (
    get_clipboard_text,
    parse_commit_message,
    validate_commit_message,
)
from ...utils.git_operations import (
    commit_staged_files,
    get_git_diff_for_commit,
    is_git_repository,
    stage_all_changes,
)

logger = logging.getLogger(__name__)


def execute_commit_auto(args: argparse.Namespace) -> int:
    """Execute commit auto command with optional preview. Returns exit code."""
    logger.info("Starting commit auto with preview=%s", args.preview)

    project_dir = Path.cwd()

    # 1. Validate git repository
    success, error = validate_git_repository(project_dir)
    if not success:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    # 2. Stage changes and generate commit message
    success, commit_message, error = generate_commit_message_with_llm(project_dir)
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


def generate_commit_message_with_llm(
    project_dir: Path,
) -> Tuple[bool, str, Optional[str]]:
    """Generate commit message using LLM. Returns (success, message, error)."""
    logger.debug("Generating commit message with LLM for %s", project_dir)

    # Step 1: Stage all changes
    logger.debug("Staging all changes in repository")
    try:
        if not stage_all_changes(project_dir):
            error_msg = f"Failed to stage changes in repository at {project_dir}. Check if you have write permissions and the repository is in a valid state."
            logger.error(error_msg)
            return False, "", error_msg
    except Exception as e:
        error_msg = f"Error staging changes: {str(e)}. Ensure the git repository is accessible and not corrupted."
        logger.error("Git staging operation failed: %s", e, exc_info=True)
        return False, "", error_msg

    # Step 2: Get git diff
    logger.debug("Retrieving git diff for staged changes")
    try:
        git_diff = get_git_diff_for_commit(project_dir)
        if git_diff is None:
            error_msg = f"Failed to retrieve git diff from repository at {project_dir}. The repository may be in an invalid state."
            logger.error(error_msg)
            return False, "", error_msg

        if not git_diff.strip():
            error_msg = "No changes to commit. Ensure you have modified, added, or deleted files before running commit auto."
            logger.warning(error_msg)
            return False, "", error_msg

        logger.debug("Git diff retrieved successfully, %d characters", len(git_diff))
    except Exception as e:
        error_msg = f"Error retrieving git diff: {str(e)}. Check if git is properly installed and the repository is accessible."
        logger.error("Git diff operation failed: %s", e, exc_info=True)
        return False, "", error_msg

    # Step 3: Load commit prompt template
    logger.debug("Loading commit message generation prompt")
    try:
        base_prompt = get_prompt(
            "mcp_coder/prompts/prompts.md", "Git Commit Message Generation"
        )
        logger.debug(
            "Commit prompt loaded successfully, %d characters", len(base_prompt)
        )
    except FileNotFoundError as e:
        error_msg = f"Commit prompt template not found: {str(e)}. The prompts.md file may be missing or corrupted."
        logger.error("Prompt file not found: %s", e, exc_info=True)
        return False, "", error_msg
    except Exception as e:
        error_msg = f"Failed to load commit prompt template: {str(e)}. Check if the prompts.md file is readable and properly formatted."
        logger.error("Prompt loading failed: %s", e, exc_info=True)
        return False, "", error_msg

    # Step 4: Prepare and send LLM request
    logger.debug("Preparing LLM request with git diff")
    try:
        # Combine prompt with git diff
        full_prompt = f"{base_prompt}\n\n=== GIT DIFF ===\n{git_diff}"

        # Validate prompt size (avoid extremely large prompts)
        if len(full_prompt) > 100000:  # 100KB limit
            logger.warning(
                "Git diff is very large (%d chars), may cause LLM issues", len(git_diff)
            )

        logger.debug("Sending request to LLM (prompt size: %d chars)", len(full_prompt))
        print("Calling LLM for auto generated commit message...")
        response = ask_llm(full_prompt, provider="claude", method="api", timeout=30)

        if not response or not response.strip():
            error_msg = "LLM returned empty or null response. The AI service may be unavailable or overloaded. Try again in a moment."
            logger.error(error_msg)
            return False, "", error_msg

        logger.debug("LLM response received successfully, %d characters", len(response))

    except Exception as e:
        error_msg = f"LLM communication failed: {str(e)}. Check your internet connection and API credentials. If the error persists, the AI service may be temporarily unavailable."
        logger.error("LLM request failed: %s", e, exc_info=True)
        return False, "", error_msg

    # Step 5: Parse and validate LLM response
    logger.debug("Parsing LLM response into commit message")
    try:
        commit_message, _ = parse_llm_commit_response(response)

        if not commit_message or not commit_message.strip():
            error_msg = "LLM generated an empty commit message. The AI may not have understood the changes. Try modifying your changes or running the command again."
            logger.error(error_msg)
            return False, "", error_msg

        # Basic validation of commit message format
        lines = commit_message.split("\n")  # Don't strip the whole message first
        first_line = lines[0].strip() if lines else ""

        if len(first_line) > 100:
            logger.warning(
                "Generated commit summary is very long (%d chars): %s",
                len(first_line),
                first_line[:50] + "...",
            )

        if not first_line:
            error_msg = "LLM generated a commit message with empty first line. This is invalid for git commits."
            logger.error(error_msg)
            return False, "", error_msg

        logger.info("Successfully generated commit message: %s", first_line)
        return True, commit_message, None

    except Exception as e:
        error_msg = f"Error parsing LLM response: {str(e)}. The AI response may be in an unexpected format."
        logger.error("Response parsing failed: %s", e, exc_info=True)
        return False, "", error_msg


def parse_llm_commit_response(response: str) -> Tuple[str, Optional[str]]:
    """Parse LLM response into commit summary and body."""
    if not response or not response.strip():
        return "", None

    # Split response into lines
    lines = response.strip().split("\n")

    # Find the first non-empty line as the commit summary
    summary = ""
    body_lines = []
    found_summary = False

    for line in lines:
        stripped_line = line.strip()

        if not found_summary and stripped_line:
            summary = stripped_line
            found_summary = True
        elif found_summary and stripped_line:
            body_lines.append(stripped_line)

    # Join body lines if any exist
    body = "\n".join(body_lines) if body_lines else None

    # If we have a body, combine summary and body with blank line
    if body:
        return f"{summary}\n\n{body}", body
    else:
        return summary, None


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

    project_dir = Path.cwd()

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

    logger.info("Successfully validated clipboard commit message: %s", summary)
    return True, formatted_message, None
