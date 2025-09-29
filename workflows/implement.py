#!/usr/bin/env python3
"""
Continuous implement workflow script that orchestrates existing mcp-coder functionality.

This script automates the implementation process by processing ALL incomplete implementation
tasks in sequence until the entire feature is complete.

For each incomplete task, it:
1. Gets implementation prompt template using get_prompt()
2. Calls LLM with task-specific prompt using ask_llm()
3. Saves conversation to pr_info/.conversations/step_N.md
4. Runs formatters (black, isort) using existing format_code()
5. Commits changes using generate_commit_message_with_llm() and commit_all_changes()
6. Pushes changes to remote repository using git_push()
7. Continues to next incomplete task

Workflow Algorithm:
1. Check prerequisites once (git status, task tracker exists)
2. Loop through all incomplete implementation tasks:
   a. Get next incomplete task from task_tracker
   b. Process single task (prompt → LLM → save → format → commit → push)
   c. Continue until no more incomplete tasks
3. Exit with summary of completed tasks
4. Graceful error handling - continues processing remaining tasks if possible
"""

import argparse
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from mcp_coder.cli.commands.commit import generate_commit_message_with_llm
from mcp_coder.cli.llm_helpers import parse_llm_method
from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.formatters import format_code
from mcp_coder.llm_interface import ask_llm
from mcp_coder.llm_providers.claude.claude_code_api import (
    ask_claude_code_api_detailed_sync,
)
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.git_operations import (
    commit_all_changes,
    get_current_branch_name,
    get_default_branch_name,
    get_full_status,
    git_push,
    is_working_directory_clean,
)
from mcp_coder.utils.log_utils import setup_logging
from mcp_coder.workflow_utils.task_tracker import get_incomplete_tasks

# Constants
PR_INFO_DIR = "pr_info"
CONVERSATIONS_DIR = f"{PR_INFO_DIR}/.conversations"
# Note: PROMPTS_FILE_PATH imported from constants

# Setup logger
logger = logging.getLogger(__name__)


def log_step(message: str) -> None:
    """Log step with structured logging instead of print."""
    logger.info(message)


def check_git_clean(project_dir: Path) -> bool:
    """Check if git working directory is clean."""
    log_step("Checking git working directory status...")
    
    try:
        is_clean = is_working_directory_clean(project_dir)
        
        if not is_clean:
            logger.error("Git working directory is not clean. Please commit or stash changes before running the workflow.")
            # Get detailed status for error reporting
            status = get_full_status(project_dir)
            for category, files in status.items():
                if files:
                    logger.error(f"{category.capitalize()} files: {files}")
            return False
        
        log_step("Git working directory is clean")
        return True
    
    except ValueError as e:
        logger.error(str(e))
        return False


def check_main_branch(project_dir: Path) -> bool:
    """Check if current branch is not the main branch."""
    log_step("Checking current branch...")
    
    try:
        current_branch = get_current_branch_name(project_dir)
        main_branch = get_default_branch_name(project_dir)
        
        if current_branch is None:
            logger.error("Could not determine current branch (possibly detached HEAD state)")
            return False
        
        if main_branch is None:
            logger.error("Could not determine main branch (neither 'main' nor 'master' branch found)")
            return False
        
        if current_branch == main_branch:
            logger.error(f"Current branch '{current_branch}' is the main branch. Please create and switch to a feature branch before running the workflow.")
            return False
        
        log_step(f"Current branch '{current_branch}' is not the main branch '{main_branch}' - check passed")
        return True
    
    except Exception as e:
        logger.error(f"Error checking current branch: {e}")
        return False


def check_prerequisites(project_dir: Path) -> bool:
    """Verify dependencies and prerequisites are met."""
    log_step("Checking prerequisites...")
    
    # Check if we're in a git repository
    git_dir = project_dir / ".git"
    if not git_dir.exists():
        logger.error(f"Not a git repository: {project_dir}")
        return False
    
    # Check if task tracker exists
    task_tracker_path = project_dir / PR_INFO_DIR / "TASK_TRACKER.md"
    if not task_tracker_path.exists():
        logger.error(f"{task_tracker_path} not found")
        return False
    
    log_step("Prerequisites check passed")
    return True


def has_implementation_tasks(project_dir: Path) -> bool:
    """Check if TASK_TRACKER.md has any implementation tasks (complete or incomplete)."""
    try:
        from mcp_coder.workflow_utils.task_tracker import (
            _find_implementation_section,
            _parse_task_lines,
            _read_task_tracker,
        )

        # Use internal functions to check for ANY tasks (complete or incomplete)
        pr_info_dir = str(project_dir / PR_INFO_DIR)
        content = _read_task_tracker(pr_info_dir)
        section_content = _find_implementation_section(content)
        all_tasks = _parse_task_lines(section_content)
        
        # Return True if there are any tasks at all (complete or incomplete)
        return len(all_tasks) > 0
    except Exception:
        # If any exception occurs (file not found, section not found, etc.), 
        # it means there are no proper implementation tasks
        return False


def prepare_task_tracker(project_dir: Path, llm_method: str) -> bool:
    """Prepare task tracker by populating it if it has no implementation steps."""
    log_step("Checking if task tracker needs preparation...")
    
    # Check if pr_info/steps/ directory exists
    steps_dir = project_dir / PR_INFO_DIR / "steps"
    if not steps_dir.exists():
        logger.error(f"Directory {steps_dir} does not exist. Please create implementation steps first.")
        return False
    
    # Check if task tracker already has implementation tasks
    if has_implementation_tasks(project_dir):
        log_step("Task tracker already has implementation tasks. Skipping preparation.")
        return True
    
    log_step("Task tracker has no implementation tasks. Generating tasks from implementation steps...")
    
    try:
        # Get the Task Tracker Update Prompt
        prompt_template = get_prompt(str(PROMPTS_FILE_PATH), "Task Tracker Update Prompt")
        
        # Call LLM with the prompt
        provider, method = parse_llm_method(llm_method)
        response = ask_llm(prompt_template, provider=provider, method=method, timeout=300)
        
        if not response or not response.strip():
            logger.error("LLM returned empty response for task tracker update")
            return False
        
        log_step("LLM response received for task tracker update")
        
        # Check what files changed using existing git_operations
        status = get_full_status(project_dir)
        
        # Only staged and modified files should contain TASK_TRACKER.md
        all_changed = status["staged"] + status["modified"] + status["untracked"]
        task_tracker_file = f"{PR_INFO_DIR}/TASK_TRACKER.md"
        
        # Check if only TASK_TRACKER.md was modified (case-insensitive comparison)
        if len(all_changed) != 1 or all_changed[0].casefold() != task_tracker_file.casefold():
            logger.error("Unexpected files were modified during task tracker update:")
            logger.error(f"  Expected: [{task_tracker_file}]")
            logger.error(f"  Found: {all_changed}")
            return False
        
        # Verify that task tracker now has implementation steps
        if not has_implementation_tasks(project_dir):
            logger.error("Task tracker still has no implementation steps after LLM update")
            return False
        
        # Commit the changes
        commit_message = "TASK_TRACKER.md with implementation steps and PR tasks updated"
        commit_result = commit_all_changes(commit_message, project_dir)
        
        if not commit_result["success"]:
            logger.error(f"Error committing task tracker changes: {commit_result['error']}")
            return False
        
        log_step("Task tracker updated and committed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error preparing task tracker: {e}")
        return False


def get_next_task(project_dir: Path) -> Optional[str]:
    """Get next incomplete task from task tracker."""
    log_step("Checking for incomplete tasks...")
    
    try:
        pr_info_dir = str(project_dir / PR_INFO_DIR)
        incomplete_tasks = get_incomplete_tasks(pr_info_dir)
        if not incomplete_tasks:
            log_step("No incomplete tasks found")
            return None
        
        next_task = incomplete_tasks[0]
        log_step(f"Found next task: {next_task}")
        return next_task
    
    except Exception as e:
        logger.error(f"Error getting incomplete tasks: {e}")
        return None


def save_conversation(project_dir: Path, content: str, step_num: int, conversation_type: str = "") -> None:
    """Save conversation content to pr_info/.conversations/step_N[_type][_counter].md."""
    logger.debug(f"Saving conversation for step {step_num} (type: {conversation_type or 'main'})...")
    
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


def _call_llm_with_comprehensive_capture(prompt: str, llm_method: str, timeout: int = 300) -> tuple[str, dict]:
    """Call LLM and capture both text response and comprehensive data.
    
    Args:
        prompt: The prompt to send to the LLM
        llm_method: LLM method ('claude_code_cli' or 'claude_code_api')
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (response_text, comprehensive_data_dict)
        For CLI method, comprehensive_data will be empty dict
    """
    provider, method = parse_llm_method(llm_method)
    
    if method == "api":
        # Use detailed API call to get comprehensive data
        try:
            detailed_response = ask_claude_code_api_detailed_sync(prompt, timeout=timeout)
            
            # Extract text response from detailed response
            response_text = ""
            if "response" in detailed_response and "content" in detailed_response["response"]:
                for content_block in detailed_response["response"]["content"]:
                    if content_block.get("type") == "text":
                        response_text += content_block.get("text", "")
            
            return response_text, detailed_response
            
        except Exception as e:
            logger.warning(f"Failed to get detailed API response, falling back to simple call: {e}")
            # Fall back to simple call
            response_text = ask_llm(prompt, provider=provider, method=method, timeout=timeout)
            return response_text, {}
    else:
        # CLI method - no comprehensive data available
        response_text = ask_llm(prompt, provider=provider, method=method, timeout=timeout)
        return response_text, {}


def save_conversation_comprehensive(project_dir: Path, content: str, step_num: int, 
                                  conversation_type: str = "", comprehensive_data: dict = None) -> None:
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
        logger.debug(f"Saving comprehensive data for step {step_num} (type: {conversation_type or 'main'})...")
        
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
                "comprehensive_export": True
            }
        }
        
        # Save comprehensive JSON
        json_path = conversations_dir / filename
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_json, f, indent=2, default=str, ensure_ascii=False)
        
        logger.debug(f"Comprehensive data saved to {json_path.absolute()}")


def run_formatters(project_dir: Path) -> bool:
    """Run code formatters (black, isort) and return success status."""
    log_step("Running code formatters...")
    
    try:
        results = format_code(project_dir, formatters=["black", "isort"])
        
        # Check if any formatter failed
        for formatter_name, result in results.items():
            if not result.success:
                logger.error(f"{formatter_name} formatting failed: {result.error_message}")
                return False
            log_step(f"{formatter_name} formatting completed successfully")
        
        log_step("All formatters completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error running formatters: {e}")
        return False


def commit_changes(project_dir: Path) -> bool:
    """Commit changes using existing git operations and return success status."""
    log_step("Committing changes...")
    
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
        log_step(f"Changes committed successfully: {commit_result['commit_hash']} - {first_line}")
        return True
    
    except Exception as e:
        logger.error(f"Error committing changes: {e}")
        return False


def push_changes(project_dir: Path) -> bool:
    """Push changes to remote repository and return success status."""
    log_step("Pushing changes to remote...")
    
    try:
        push_result = git_push(project_dir)
        
        if not push_result["success"]:
            logger.error(f"Error pushing changes: {push_result['error']}")
            return False
        
        log_step("Changes pushed successfully to remote")
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


def check_and_fix_mypy(project_dir: Path, step_num: int, llm_method: str) -> bool:
    """Run mypy check and attempt fixes if issues found. Returns True if clean."""
    log_step("Running mypy type checking...")
    
    max_identical_attempts = 3
    previous_outputs = []
    mypy_attempt_counter = 0
    
    try:
        # Initial mypy check using MCP tool
        mypy_result = _run_mypy_check(project_dir)
        
        if mypy_result is None:
            log_step("Mypy check passed - no type errors found")
            return True
        
        log_step("Type errors found, attempting fixes...")
        identical_count = 0
        
        # Retry loop with smart retry logic
        while identical_count < max_identical_attempts:
            # Check if current mypy output is identical to a previous one
            if mypy_result in previous_outputs:
                identical_count += 1
                log_step(f"Identical mypy feedback detected (attempt {identical_count}/{max_identical_attempts})")
                
                if identical_count >= max_identical_attempts:
                    log_step("Maximum identical attempts reached - stopping mypy fixes")
                    break
            else:
                # New output, reset counter
                identical_count = 0
            
            # Add current output to history
            previous_outputs.append(mypy_result)
            mypy_attempt_counter += 1
            
            # Get mypy fix prompt template
            try:
                mypy_prompt_template = get_prompt(str(PROMPTS_FILE_PATH), "Mypy Fix Prompt")
                # Replace placeholder with actual mypy output
                mypy_prompt = mypy_prompt_template.replace("[mypy_output]", mypy_result)
            except Exception as e:
                logger.error(f"Error loading mypy fix prompt: {e}")
                return False
            
            # Call LLM for fixes with comprehensive data capture
            try:
                fix_response, mypy_comprehensive_data = _call_llm_with_comprehensive_capture(mypy_prompt, llm_method, timeout=300)
                
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
                save_conversation_comprehensive(project_dir, mypy_conversation, step_num, "mypy",
                                               comprehensive_data=mypy_comprehensive_data)
                
                log_step(f"Applied mypy fixes from LLM (attempt {mypy_attempt_counter})")
                
            except Exception as e:
                logger.error(f"Error getting mypy fixes from LLM on attempt {mypy_attempt_counter}: {e}")
                return False
            
            # Re-run mypy check to see if issues were resolved
            try:
                mypy_result = _run_mypy_check(project_dir)
                
                if mypy_result is None:
                    log_step("Mypy check passed after fixes")
                    return True
                    
            except Exception as e:
                logger.error(f"Error re-running mypy check on attempt {mypy_attempt_counter}: {e}")
                return False
        
        # If we get here, we couldn't fix all issues
        log_step("Could not resolve all mypy type errors")
        return False
        
    except Exception as e:
        logger.error(f"Error during mypy check and fix: {e}")
        return False


def process_single_task(project_dir: Path, llm_method: str) -> bool:
    """Process a single implementation task. Returns True if successful, False if failed."""
    # Get next incomplete task
    next_task = get_next_task(project_dir)
    if not next_task:
        log_step("No incomplete tasks found")
        return False
    
    # Step 3: Get implementation prompt template
    logger.debug("Loading implementation prompt template...")
    try:
        prompt_template = get_prompt(str(PROMPTS_FILE_PATH), "Implementation Prompt Template using task tracker")
    except Exception as e:
        logger.error(f"Error loading prompt template: {e}")
        return False
    
    # Step 4: Call LLM with prompt and capture comprehensive data
    log_step("Calling LLM for implementation...")
    try:
        # Create the full prompt by combining template with task context
        full_prompt = f"""{prompt_template}

Current task from TASK_TRACKER.md: {next_task}

Please implement this task step by step."""
        
        response, comprehensive_data = _call_llm_with_comprehensive_capture(full_prompt, llm_method, timeout=600)
        
        if not response or not response.strip():
            logger.error("LLM returned empty response")
            return False
        
        log_step("LLM response received successfully")
    
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        return False
    
    # Step 5: Extract step number and save initial implementation conversation
    try:
        # Extract step number from task for conversation naming
        step_match = re.search(r'Step (\d+)', next_task)
        step_num = int(step_match.group(1)) if step_match else 1
        
        # Save initial implementation conversation with comprehensive data
        initial_conversation = f"""# Implementation Task: {next_task}

## Prompt Sent to LLM:
{full_prompt}

## LLM Response:
{response}

---
Generated on: {datetime.now().isoformat()}"""
        
        save_conversation_comprehensive(project_dir, initial_conversation, step_num, 
                                      comprehensive_data=comprehensive_data)
        
    except Exception as e:
        logger.error(f"Error saving initial conversation: {e}")
        return False
    
    # Step 6: Run mypy check and fixes (each fix will be saved separately)
    if not check_and_fix_mypy(project_dir, step_num, llm_method):
        logger.warning("Mypy check failed or found unresolved issues - continuing anyway")
    
    # Step 7: Run formatters
    if not run_formatters(project_dir):
        return False
    
    # Step 8: Commit changes
    if not commit_changes(project_dir):
        return False
    
    # Step 9: Push changes to remote
    if not push_changes(project_dir):
        return False
    
    log_step(f"Task completed successfully: {next_task}")
    return True


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments including project directory and log level."""
    parser = argparse.ArgumentParser(
        description="Continuous implement workflow script that orchestrates existing mcp-coder functionality."
    )
    parser.add_argument(
        "--project-dir",
        metavar="PATH",
        help="Project directory path (default: current directory)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)"
    )
    parser.add_argument(
        "--llm-method",
        choices=["claude_code_cli", "claude_code_api"],
        default="claude_code_api",
        help="LLM method to use (default: claude_code_api)"
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
    """Main workflow orchestration function - processes all implementation tasks in sequence."""
    # Parse command line arguments
    args = parse_arguments()
    project_dir = resolve_project_dir(args.project_dir)
    
    # Setup logging early
    setup_logging(args.log_level)
    
    log_step("Starting implement workflow...")
    log_step(f"Using project directory: {project_dir}")
    
    # Step 1: Check git status and prerequisites
    if not check_git_clean(project_dir):
        sys.exit(1)
    
    if not check_main_branch(project_dir):
        sys.exit(1)
    
    if not check_prerequisites(project_dir):
        sys.exit(1)
    
    # Step 2: Prepare task tracker if needed
    if not prepare_task_tracker(project_dir, args.llm_method):
        sys.exit(1)
    
    # Step 3: Process all incomplete tasks in a loop
    completed_tasks = 0
    while True:
        success = process_single_task(project_dir, args.llm_method)
        if not success:
            # No more tasks or error occurred
            break
        
        completed_tasks += 1
        log_step(f"Completed {completed_tasks} task(s). Checking for more...")
    
    if completed_tasks > 0:
        log_step(f"Implement workflow completed successfully! Processed {completed_tasks} task(s).")
    else:
        log_step("No incomplete implementation tasks found - workflow complete")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
