"""Commit operations for the MCP Coder utilities.

This module provides functions for generating commit messages using LLM services.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

from ..constants import PROMPTS_FILE_PATH
from ..llm.interface import ask_llm
from ..llm.providers.claude.claude_code_api import ClaudeAPIError

from ..prompt_manager import get_prompt
from .git_operations import get_git_diff_for_commit, stage_all_changes

# Constants
LLM_COMMIT_TIMEOUT_SECONDS = 120  # 2 minutes for commit message generation

logger = logging.getLogger(__name__)


def generate_commit_message_with_llm(
    project_dir: Path, provider: str = "claude", method: str = "api"
) -> Tuple[bool, str, Optional[str]]:
    """Generate commit message using LLM. Returns (success, message, error).
    
    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
        
    Returns:
        Tuple of (success, commit_message, error_message)
    """
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
            str(PROMPTS_FILE_PATH), "Git Commit Message Generation"
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
        logger.debug("Calling LLM for auto generated commit message...")
        response = ask_llm(
            full_prompt,
            provider=provider,
            method=method,
            timeout=LLM_COMMIT_TIMEOUT_SECONDS,
        )

        if not response or not response.strip():
            error_msg = "LLM returned empty or null response. The AI service may be unavailable or overloaded. Try again in a moment."
            logger.error(error_msg)
            return False, "", error_msg

        logger.debug("LLM response received successfully, %d characters", len(response))

    except ClaudeAPIError as e:
        # Clean error message from ClaudeAPIError - no stack trace needed
        error_msg = str(e)
        logger.error("Claude API error: %s", error_msg)
        return False, "", error_msg
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

        logger.debug("Successfully generated commit message: %s", first_line)
        return True, commit_message, None

    except Exception as e:
        error_msg = f"Error parsing LLM response: {str(e)}. The AI response may be in an unexpected format."
        logger.error("Response parsing failed: %s", e, exc_info=True)
        return False, "", error_msg


def parse_llm_commit_response(response: Optional[str]) -> Tuple[str, Optional[str]]:
    """Parse LLM response into commit summary and body."""
    if not response or not response.strip():
        return "", None

    # Split response into lines and strip surrounding whitespace from the entire response
    lines = response.strip().split("\n")

    # Find the first non-empty line as the summary
    summary_line = ""
    body_start_index = -1

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line:
            summary_line = stripped_line
            body_start_index = i + 1
            break

    if not summary_line:
        return "", None

    # Collect body lines starting from after the summary
    body_lines = []
    if body_start_index < len(lines):
        # Skip any immediate empty lines after summary
        body_start = body_start_index
        while body_start < len(lines) and not lines[body_start].strip():
            body_start += 1

        # Collect all remaining lines, preserving single empty lines between content
        for i in range(body_start, len(lines)):
            line = lines[i].strip()
            if line:  # Non-empty line
                body_lines.append(line)
            elif body_lines:  # Empty line, but only if we already have content
                # Check if there's more non-empty content after this empty line
                has_more_content = any(
                    lines[j].strip() for j in range(i + 1, len(lines))
                )
                if has_more_content:
                    # Only add one empty line, even if there are multiple consecutive empty lines
                    if not body_lines or body_lines[-1] != "":
                        body_lines.append(
                            ""
                        )  # Preserve single empty line between content

    # Create body string if we have content
    body = "\n".join(body_lines) if body_lines else None

    # If we have a body, combine summary and body with blank line
    if body:
        return f"{summary_line}\n\n{body}", body
    else:
        return summary_line, None
