"""Task processing functions for implement workflow.

This module contains functions for processing individual implementation tasks,
including LLM integration, mypy fixes, formatting, and git operations.
"""

import json
import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.formatters import format_code
from mcp_coder.llm.interface import ask_llm
from mcp_coder.llm.providers.claude.claude_code_api import (
    ask_claude_code_api_detailed_sync,
)

# Import removed - using structured parameters instead
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.commit_operations import generate_commit_message_with_llm
from mcp_coder.utils.git_operations import (
    commit_all_changes,
    get_full_status,
    git_push,
)
from mcp_coder.workflow_utils.task_tracker import get_incomplete_tasks

# Constants
PR_INFO_DIR = "pr_info"
CONVERSATIONS_DIR = f"{PR_INFO_DIR}/.conversations"
LLM_IMPLEMENTATION_TIMEOUT_SECONDS = 1800  # 30 minutes

# Setup logger
logger = logging.getLogger(__name__)


def get_next_task(project_dir: Path) -> Optional[str]:
    """Get next incomplete task from task tracker (excluding meta-tasks)."""
    logger.info("Checking for incomplete tasks...")

    try:
        pr_info_dir = str(project_dir / PR_INFO_DIR)

        # Get incomplete tasks, excluding meta-tasks
        incomplete_tasks = get_incomplete_tasks(pr_info_dir, exclude_meta_tasks=True)

        if not incomplete_tasks:
            logger.info(
                "No incomplete implementation tasks found (meta-tasks excluded)"
            )
            return None

        next_task = incomplete_tasks[0]
        logger.info(f"Found next task: {next_task}")
        return next_task

    except Exception as e:
        logger.error(f"Error getting incomplete tasks: {e}")
        return None


def save_conversation(
    project_dir: Path, content: str, step_num: int, conversation_type: str = ""
) -> None:
    """Save conversation content to pr_info/.conversations/step_N[_type][_counter].md."""
    logger.debug(
        f"Saving conversation for step {step_num} (type: {conversation_type or 'main'})..."
    )

    # Create conversations directory if it doesn't exist
    conversations_dir = project_dir / PR_INFO_DIR / ".conversations"
    conversations_dir.mkdir(parents=True, exist_ok=True)

    # Build base filename with optional type
    if conversation_type:
        base_name = f"step_{step_num}_{conversation_type}"
    else:
        base_name = f"step_{step_num}"

    # Find next available filename for this step and type
    counter = 1
    filename = f"{base_name}.md"

    while (conversations_dir / filename).exists():
        counter += 1
        filename = f"{base_name}_{counter}.md"

    # Save the conversation
    conversation_path = conversations_dir / filename
    conversation_path.write_text(content, encoding="utf-8")

    logger.debug(f"Conversation saved to {conversation_path.absolute()}")


def _call_llm_with_comprehensive_capture(
    prompt: str, provider: str, method: str, timeout: int = 300
) -> tuple[str, dict[Any, Any]]:
    """Call LLM and capture both text response and comprehensive data.

    Args:
        prompt: The prompt to send to the LLM
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
        timeout: Request timeout in seconds

    Returns:
        Tuple of (response_text, comprehensive_data_dict)
        For CLI method, comprehensive_data will be empty dict
    """
    # Use provided structured parameters

    if method == "api":
        # Use detailed API call to get comprehensive data
        try:
            logger.info(f"Calling Claude API with {timeout}s timeout...")
            logger.debug(
                f"Prompt preview: {prompt[:200]}{'...' if len(prompt) > 200 else ''}"
            )
            start_time = datetime.now()
            detailed_response = ask_claude_code_api_detailed_sync(
                prompt, timeout=timeout
            )
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Claude API call completed in {duration:.1f}s")

            # Extract text response from detailed response structure
            response_text = detailed_response.get("text", "")

            if not response_text:
                logger.warning("Detailed API response had no text content")
                logger.debug(f"Response structure: {list(detailed_response.keys())}")

            return response_text, detailed_response

        except subprocess.TimeoutExpired as e:
            duration = (
                (datetime.now() - start_time).total_seconds()
                if "start_time" in locals()
                else timeout
            )
            logger.error(
                f"Claude API call timed out after {timeout}s (actual: {duration:.1f}s): {e}"
            )
            logger.error(
                f"Prompt length: {len(prompt)} characters ({len(prompt.split())} words)"
            )
            logger.error(f"LLM method: {provider}/{method}")
            logger.error(
                f"This may indicate: network issues, complex prompt, long-running MCP tools, or insufficient timeout"
            )
            logger.error(
                f"Consider: checking network, simplifying prompt, waiting for MCP tools to complete, or increasing timeout"
            )
            raise Exception(f"LLM request timed out after {timeout} seconds") from e
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise Exception(f"LLM request failed: {e}") from e
    else:
        # CLI method - no comprehensive data available
        try:
            logger.info(f"Calling Claude CLI with {timeout}s timeout...")
            response_text = ask_llm(
                prompt, provider=provider, method=method, timeout=timeout
            )
            return response_text, {}
        except subprocess.TimeoutExpired as e:
            logger.error(f"Claude CLI call timed out after {timeout}s: {e}")
            logger.error(f"Prompt length: {len(prompt)} characters")
            logger.error(f"LLM method: {provider}/{method}")
            logger.error(
                f"This may indicate: network issues, complex prompt, long-running MCP tools, or insufficient timeout"
            )
            logger.error(
                f"Consider: checking network, simplifying prompt, waiting for MCP tools to complete, or increasing timeout"
            )
            raise Exception(f"LLM request timed out after {timeout} seconds") from e
        except Exception as e:
            logger.error(f"Claude CLI call failed: {e}")
            logger.error(f"Prompt length: {len(prompt)} characters")
            logger.error(f"LLM method: {provider}/{method}")
            raise Exception(f"LLM request failed: {e}") from e


def save_conversation_comprehensive(
    project_dir: Path,
    content: str,
    step_num: int,
    conversation_type: str = "",
    comprehensive_data: dict[Any, Any] | None = None,
) -> None:
    """Save both markdown conversation and comprehensive JSON data.

    Args:
        project_dir: Project directory path
        content: Conversation content (markdown)
        step_num: Step number
        conversation_type: Type of conversation (e.g., 'mypy', 'main')
        comprehensive_data: Full API response data including session info, cost, usage, etc.
    """
    # Save the regular markdown conversation
    save_conversation(project_dir, content, step_num, conversation_type)

    # Save comprehensive JSON data if provided
    if comprehensive_data:
        logger.debug(
            f"Saving comprehensive data for step {step_num} (type: {conversation_type or 'main'})..."
        )

        conversations_dir = project_dir / PR_INFO_DIR / ".conversations"
        conversations_dir.mkdir(parents=True, exist_ok=True)

        # Build filename for comprehensive data
        if conversation_type:
            base_name = f"step_{step_num}_{conversation_type}_comprehensive"
        else:
            base_name = f"step_{step_num}_comprehensive"

        # Find next available filename
        counter = 1
        filename = f"{base_name}.json"

        while (conversations_dir / filename).exists():
            counter += 1
            filename = f"{base_name}_{counter}.json"

        # Prepare comprehensive data structure
        comprehensive_json = {
            "step": step_num,
            "type": conversation_type or "main",
            "timestamp": datetime.now().isoformat(),
            "conversation_markdown": content,
            "llm_response_data": comprehensive_data,
            "metadata": {
                "workflow": "implement",
                "version": "1.0",
                "comprehensive_export": True,
            },
        }

        # Save comprehensive JSON
        json_path = conversations_dir / filename
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(comprehensive_json, f, indent=2, default=str, ensure_ascii=False)

        logger.debug(f"Comprehensive data saved to {json_path.absolute()}")


def run_formatters(project_dir: Path) -> bool:
    """Run code formatters (black, isort) and return success status."""
    logger.info("Running code formatters...")

    try:
        results = format_code(project_dir, formatters=["black", "isort"])

        # Check if any formatter failed
        for formatter_name, result in results.items():
            if not result.success:
                logger.error(
                    f"{formatter_name} formatting failed: {result.error_message}"
                )
                return False
            logger.info(f"{formatter_name} formatting completed successfully")

        logger.info("All formatters completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error running formatters: {e}")
        return False


def commit_changes(project_dir: Path) -> bool:
    """Commit changes using existing git operations and return success status."""
    logger.info("Committing changes...")

    try:
        success, commit_message, error = generate_commit_message_with_llm(project_dir)

        if not success:
            logger.error(f"Error generating commit message: {error}")
            return False

        # Commit using the generated message
        commit_result = commit_all_changes(commit_message, project_dir)

        if not commit_result["success"]:
            logger.error(f"Error committing changes: {commit_result['error']}")
            return False

        # Show commit message first line along with hash
        commit_lines = commit_message.strip().split("\n")
        first_line = commit_lines[0].strip() if commit_lines else commit_message.strip()
        logger.info(
            f"Changes committed successfully: {commit_result['commit_hash']} - {first_line}"
        )
        return True

    except Exception as e:
        logger.error(f"Error committing changes: {e}")
        return False


def push_changes(project_dir: Path) -> bool:
    """Push changes to remote repository and return success status."""
    logger.info("Pushing changes to remote...")

    try:
        push_result = git_push(project_dir)

        if not push_result["success"]:
            logger.error(f"Error pushing changes: {push_result['error']}")
            return False

        logger.info("Changes pushed successfully to remote")
        return True

    except Exception as e:
        logger.error(f"Error pushing changes: {e}")
        return False


def _run_mypy_check(project_dir: Path) -> Optional[str]:
    """Run mypy check using our wrapper and return error output or None if clean."""
    from mcp_coder.mcp_code_checker import run_mypy_check

    try:
        result = run_mypy_check(project_dir)

        # Check if there are errors
        if (result.errors_found or 0) > 0:
            # Return raw output for error details
            return result.raw_output or "Mypy found type errors"
        else:
            return None  # No errors found

    except Exception as e:
        raise Exception(f"Failed to run mypy check: {e}")


def check_and_fix_mypy(
    project_dir: Path, step_num: int, provider: str, method: str
) -> bool:
    """Run mypy check and attempt fixes if issues found. Returns True if clean.

    Args:
        project_dir: Path to the project directory
        step_num: Step number for conversation naming
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
    """
    logger.info("Running mypy type checking...")

    max_identical_attempts = 3
    previous_outputs = []
    mypy_attempt_counter = 0

    try:
        # Initial mypy check using MCP tool
        mypy_result = _run_mypy_check(project_dir)

        if mypy_result is None:
            logger.info("Mypy check passed - no type errors found")
            return True

        logger.info("Type errors found, attempting fixes...")
        identical_count = 0

        # Retry loop with smart retry logic
        while identical_count < max_identical_attempts:
            # Check if current mypy output is identical to a previous one
            if mypy_result in previous_outputs:
                identical_count += 1
                logger.info(
                    f"Identical mypy feedback detected (attempt {identical_count}/{max_identical_attempts})"
                )

                if identical_count >= max_identical_attempts:
                    logger.info(
                        "Maximum identical attempts reached - stopping mypy fixes"
                    )
                    break
            else:
                # New output, reset counter
                identical_count = 0

            # Add current output to history
            previous_outputs.append(mypy_result)
            mypy_attempt_counter += 1

            # Get mypy fix prompt template
            try:
                mypy_prompt_template = get_prompt(
                    str(PROMPTS_FILE_PATH), "Mypy Fix Prompt"
                )
                # Replace placeholder with actual mypy output
                mypy_prompt = mypy_prompt_template.replace("[mypy_output]", mypy_result)
            except Exception as e:
                logger.error(f"Error loading mypy fix prompt: {e}")
                return False

            # Call LLM for fixes with comprehensive data capture
            try:
                fix_response, mypy_comprehensive_data = (
                    _call_llm_with_comprehensive_capture(
                        mypy_prompt,
                        provider,
                        method,
                        timeout=LLM_IMPLEMENTATION_TIMEOUT_SECONDS,
                    )
                )

                if not fix_response or not fix_response.strip():
                    logger.error("LLM returned empty response for mypy fixes")
                    return False

                # Save this mypy fix conversation immediately with comprehensive data
                mypy_conversation = f"""# Mypy Fix Attempt {mypy_attempt_counter}

## Mypy Errors:
{mypy_result}

## Prompt Sent to LLM:
{mypy_prompt}

## LLM Fix Response:
{fix_response}

---
Mypy fix generated on: {datetime.now().isoformat()}
"""
                save_conversation_comprehensive(
                    project_dir,
                    mypy_conversation,
                    step_num,
                    "mypy",
                    comprehensive_data=mypy_comprehensive_data,
                )

                logger.info(
                    f"Applied mypy fixes from LLM (attempt {mypy_attempt_counter})"
                )

            except Exception as e:
                logger.error(
                    f"Error getting mypy fixes from LLM on attempt {mypy_attempt_counter}: {e}"
                )
                return False

            # Re-run mypy check to see if issues were resolved
            try:
                mypy_result = _run_mypy_check(project_dir)

                if mypy_result is None:
                    logger.info("Mypy check passed after fixes")
                    return True

            except Exception as e:
                logger.error(
                    f"Error re-running mypy check on attempt {mypy_attempt_counter}: {e}"
                )
                return False

        # If we get here, we couldn't fix all issues
        logger.info("Could not resolve all mypy type errors")
        return False

    except Exception as e:
        logger.error(f"Error during mypy check and fix: {e}")
        return False


def process_single_task(
    project_dir: Path, provider: str, method: str
) -> tuple[bool, str]:
    """Process a single implementation task.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')

    Returns:
        Tuple of (success, reason) where:
        - success: True if task completed successfully
        - reason: 'completed' | 'no_tasks' | 'error'
    """
    # Get next incomplete task
    next_task = get_next_task(project_dir)
    if not next_task:
        logger.info("No incomplete tasks found")
        return False, "no_tasks"

    # Step 3: Get implementation prompt template
    logger.debug("Loading implementation prompt template...")
    try:
        prompt_template = get_prompt(
            str(PROMPTS_FILE_PATH), "Implementation Prompt Template using task tracker"
        )
    except Exception as e:
        logger.error(f"Error loading prompt template: {e}")
        return False, "error"

    # Step 4: Call LLM with prompt and capture comprehensive data
    logger.info("Calling LLM for implementation...")
    try:
        # Create the full prompt by combining template with task context
        full_prompt = f"""{prompt_template}

Current task from TASK_TRACKER.md: {next_task}

Please implement this task step by step."""

        response, comprehensive_data = _call_llm_with_comprehensive_capture(
            full_prompt, provider, method, timeout=LLM_IMPLEMENTATION_TIMEOUT_SECONDS
        )

        if not response or not response.strip():
            logger.error("LLM returned empty response")
            logger.debug(f"Response was: {repr(response)}")
            if comprehensive_data:
                logger.debug(
                    f"Comprehensive data keys: {list(comprehensive_data.keys())}"
                )
            return False, "error"

        logger.info("LLM response received successfully")

    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        return False, "error"

    # Step 5: Extract step number and save initial implementation conversation
    try:
        # Extract step number from task for conversation naming
        step_match = re.search(r"Step (\d+)", next_task)
        step_num = int(step_match.group(1)) if step_match else 1

        # Save initial implementation conversation with comprehensive data
        initial_conversation = f"""# Implementation Task: {next_task}

## Prompt Sent to LLM:
{full_prompt}

## LLM Response:
{response}

---
Generated on: {datetime.now().isoformat()}"""

        save_conversation_comprehensive(
            project_dir,
            initial_conversation,
            step_num,
            comprehensive_data=comprehensive_data,
        )

    except Exception as e:
        logger.error(f"Error saving initial conversation: {e}")
        return False, "error"

    # Step 6: Check if any files were actually changed
    try:
        status = get_full_status(project_dir)
        all_changes = status["staged"] + status["modified"] + status["untracked"]

        if not all_changes:
            logger.warning(f"No files were changed for task: {next_task}")
            logger.warning(
                "This might indicate the task is already complete or the LLM didn't make changes"
            )
            logger.warning("Skipping commit/push for this task")
            return True, "completed"  # Consider it successful but skip commit
    except Exception as e:
        logger.error(f"Error checking file changes: {e}")
        return False, "error"

    # Step 7: Run mypy check and fixes (each fix will be saved separately)
    if not check_and_fix_mypy(project_dir, step_num, provider, method):
        logger.warning(
            "Mypy check failed or found unresolved issues - continuing anyway"
        )

    # Step 8: Run formatters
    if not run_formatters(project_dir):
        return False, "error"

    # Step 9: Commit changes
    if not commit_changes(project_dir):
        return False, "error"

    # Step 10: Push changes to remote
    if not push_changes(project_dir):
        return False, "error"

    logger.info(f"Task completed successfully: {next_task}")
    return True, "completed"
