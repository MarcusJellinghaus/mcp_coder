#!/usr/bin/env python3
"""
Create pull request workflow script for repository cleanup operations.

This module provides utility functions for cleaning up repository state
after feature implementation is complete and orchestrates the complete
PR creation workflow.
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path
from typing import Optional, Tuple

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.interface import ask_llm
from mcp_coder.llm.session import parse_llm_method
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils import (
    commit_all_changes,
    get_branch_diff,
    get_current_branch_name,
    get_parent_branch_name,
    git_push,
    is_working_directory_clean,
)
from mcp_coder.utils.github_operations.pr_manager import PullRequestManager
from mcp_coder.utils.log_utils import setup_logging
from mcp_coder.workflow_utils.task_tracker import get_incomplete_tasks

# Note: PROMPTS_FILE_PATH imported from constants

# Setup logger
logger = logging.getLogger(__name__)


def delete_steps_directory(project_dir: Path) -> bool:
    """
    Delete the pr_info/steps/ directory and all its contents.
    
    Args:
        project_dir: Path to the project root directory
        
    Returns:
        True if successful or directory doesn't exist, False on error
    """
    steps_dir = project_dir / "pr_info" / "steps"
    
    # If directory doesn't exist, consider it success (no-op)
    if not steps_dir.exists():
        logger.info(f"Directory {steps_dir} does not exist - nothing to delete")
        return True
    
    try:
        # Remove the entire directory tree
        shutil.rmtree(steps_dir)
        logger.info(f"Successfully deleted directory: {steps_dir}")
        return True
        
    except PermissionError as e:
        logger.error(f"Permission error deleting {steps_dir}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting {steps_dir}: {e}")
        return False


def clean_profiler_output(project_dir: Path) -> bool:
    """
    Clean up profiler output files from docs/tests/performance_data/prof/ directory.
    
    Removes all files from the profiler output directory while keeping the directory itself.
    This prevents temporary profiler output from being included in pull requests.
    
    Args:
        project_dir: Path to the project root directory
        
    Returns:
        True if successful or directory doesn't exist, False on error
    """
    prof_dir = project_dir / "docs" / "tests" / "performance_data" / "prof"
    
    # If directory doesn't exist, consider it success (no-op)
    if not prof_dir.exists():
        logger.info(f"Directory {prof_dir} does not exist - nothing to clean")
        return True
    
    try:
        # Remove all files in the directory
        file_count = 0
        for file_path in prof_dir.iterdir():
            if file_path.is_file():
                file_path.unlink()
                file_count += 1
        
        if file_count > 0:
            logger.info(f"Successfully deleted {file_count} file(s) from {prof_dir}")
        else:
            logger.info(f"Directory {prof_dir} is already empty")
        return True
        
    except PermissionError as e:
        logger.error(f"Permission error cleaning {prof_dir}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error cleaning {prof_dir}: {e}")
        return False


def truncate_task_tracker(project_dir: Path) -> bool:
    """
    Truncate TASK_TRACKER.md file, keeping only content before '## Tasks' section.
    
    This function reads the TASK_TRACKER.md file, finds the '## Tasks' section,
    and removes all content from that point onward, keeping the section header.
    
    Args:
        project_dir: Path to the project root directory
        
    Returns:
        True if successful, False on error or if file doesn't exist
    """
    tracker_path = project_dir / "pr_info" / "TASK_TRACKER.md"
    
    # Check if file exists
    if not tracker_path.exists():
        logger.error(f"File {tracker_path} does not exist")
        return False
    
    try:
        # Read the current content
        content = tracker_path.read_text(encoding="utf-8")
        
        # Find the "## Tasks" section
        tasks_index = content.find("## Tasks")
        
        if tasks_index == -1:
            # No Tasks section found, append it at the end
            logger.info("No '## Tasks' section found, appending empty section")
            truncated_content = content.rstrip() + "\n\n## Tasks"
        else:
            # Keep everything before "## Tasks" and add the section header back
            truncated_content = content[:tasks_index] + "## Tasks"
        
        # Write the truncated content back
        tracker_path.write_text(truncated_content, encoding="utf-8")
        logger.info(f"Successfully truncated {tracker_path}")
        return True
        
    except PermissionError as e:
        logger.error(f"Permission error accessing {tracker_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error truncating {tracker_path}: {e}")
        return False


def parse_pr_summary(llm_response: str) -> Tuple[str, str]:
    """
    Parse LLM response into PR title and body.
    
    Expected format:
    TITLE: feat: some title
    BODY:
    ## Summary
    ...
    
    Args:
        llm_response: Raw response from LLM
        
    Returns:
        Tuple of (title, body) strings
    """
    if not llm_response or not llm_response.strip():
        logger.warning("Empty LLM response, using fallback PR title/body")
        return "Pull Request", "Pull Request"
    
    content = llm_response.strip()
    
    # Look for TITLE: and BODY: markers
    title_match = None
    body_content = None
    
    # Extract title after "TITLE:"
    for line in content.split("\n"):
        if line.strip().startswith("TITLE:"):
            title_match = line.strip()[6:].strip()  # Remove "TITLE:" prefix
            break
    
    # Extract body after "BODY:"
    body_start = content.find("BODY:")
    if body_start != -1:
        body_content = content[body_start + 5:].strip()  # Remove "BODY:" prefix
    
    # Fallback parsing if structured format not found
    if not title_match:
        logger.warning("No TITLE: found, attempting fallback parsing")
        lines = content.split("\n")
        # Try to find a line that looks like a title (starts with conventional prefix)
        for line in lines:
            line_stripped = line.strip()
            if any(line_stripped.startswith(prefix) for prefix in ["feat:", "fix:", "docs:", "refactor:", "test:", "chore:"]):
                title_match = line_stripped
                break
        
        # If still no title found, use first non-empty line
        if not title_match:
            for line in lines:
                if line.strip():
                    title_match = line.strip()
                    break
    
    if not body_content:
        logger.warning("No BODY: found, using full response as body")
        body_content = content
    
    # Final fallbacks
    title = title_match or "Pull Request"
    body = body_content or "Pull Request"
    
    logger.info(f"Parsed PR title: {title}")
    return title, body


def check_prerequisites(project_dir: Path) -> bool:
    """
    Validate prerequisites for PR creation workflow.
    
    Checks:
    1. Git working directory is clean
    2. No incomplete tasks exist
    3. Current branch is not the parent branch
    4. Current branch can be determined
    
    Args:
        project_dir: Path to project directory
        
    Returns:
        True if all prerequisites pass, False otherwise
    """
    logger.info("Checking prerequisites for PR creation...")
    
    # Check if git working directory is clean
    try:
        if not is_working_directory_clean(project_dir):
            logger.error("Git working directory is not clean. Please commit or stash changes.")
            return False
        logger.info("✓ Git working directory is clean")
    except Exception as e:
        logger.error(f"Error checking git status: {e}")
        return False
    
    # Check for incomplete tasks
    try:
        pr_info_dir = str(project_dir / "pr_info")
        incomplete_tasks = get_incomplete_tasks(pr_info_dir)
        if incomplete_tasks:
            logger.error(f"Found {len(incomplete_tasks)} incomplete tasks:")
            for task in incomplete_tasks:
                logger.error(f"  - {task}")
            logger.error("Please complete all tasks before creating PR.")
            return False
        logger.info("✓ No incomplete tasks found")
    except Exception as e:
        logger.error(f"Error checking incomplete tasks: {e}")
        return False
    
    # Check current branch
    try:
        current_branch = get_current_branch_name(project_dir)
        if current_branch is None:
            logger.error("Could not determine current branch (possibly detached HEAD)")
            return False
        
        parent_branch = get_parent_branch_name(project_dir)
        if parent_branch is None:
            logger.error("Could not determine parent branch")
            return False
        
        if current_branch == parent_branch:
            logger.error(f"Current branch '{current_branch}' is the parent branch. Please create feature branch.")
            return False
        
        logger.info(f"✓ Current branch '{current_branch}' is not parent branch '{parent_branch}'")
    except Exception as e:
        logger.error(f"Error checking branch status: {e}")
        return False
    
    logger.info("All prerequisites passed")
    return True


def _load_prompt_or_exit(header: str) -> str:
    """Load prompt template or exit with clear error message."""
    try:
        return get_prompt(str(PROMPTS_FILE_PATH), header)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Critical error: Cannot load prompt '{header}': {e}")
        logger.error(f"Expected prompt file: {PROMPTS_FILE_PATH}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error loading prompt '{header}': {e}")
        sys.exit(1)


def generate_pr_summary(project_dir: Path, llm_method: str = "claude_code_api") -> Tuple[str, str]:
    """
    Generate PR title and body using LLM and git diff.
    
    Args:
        project_dir: Path to project directory
        
    Returns:
        Tuple of (title, body) strings
    """
    logger.info("Generating PR summary...")
    
    # Get branch diff
    logger.info("Getting branch diff...")
    diff_content = get_branch_diff(project_dir, exclude_paths=["pr_info/steps/"])
    
    if not diff_content or not diff_content.strip():
        logger.warning("No diff content found, using fallback PR summary")
        return "Pull Request", "Pull Request"
    
    # Load prompt template (exits on failure)
    logger.info("Loading PR summary prompt template...")
    prompt_template = _load_prompt_or_exit("PR Summary Generation")
    
    # Generate summary
    full_prompt = prompt_template.replace("[git_diff_content]", diff_content)
    
    logger.info(f"Calling LLM for PR summary using method: {llm_method}...")
    try:
        provider, method = parse_llm_method(llm_method)
        llm_response = ask_llm(full_prompt, provider=provider, method=method, timeout=300)
        
        if not llm_response or not llm_response.strip():
            logger.error("LLM returned empty response - cannot generate meaningful PR summary")
            logger.error("This indicates a configuration issue with the LLM provider.")
            sys.exit(1)
        
        title, body = parse_pr_summary(llm_response)
        logger.info("PR summary generated successfully")
        return title, body
        
    except Exception as e:
        logger.error(f"Critical error: LLM API failed: {e}")
        logger.error("Cannot generate PR summary without working LLM connection.")
        logger.error("Please fix LLM configuration before creating PR.")
        sys.exit(1)


def cleanup_repository(project_dir: Path) -> bool:
    """
    Clean up repository by deleting steps directory, truncating task tracker, and cleaning profiler output.
    
    Args:
        project_dir: Path to project directory
        
    Returns:
        True if all cleanup operations succeed, False otherwise
    """
    logger.info("Cleaning up repository...")
    
    success = True
    
    # Delete steps directory
    logger.info("Deleting pr_info/steps/ directory...")
    if not delete_steps_directory(project_dir):
        logger.error("Failed to delete steps directory")
        success = False
    
    # Truncate task tracker
    logger.info("Truncating TASK_TRACKER.md...")
    if not truncate_task_tracker(project_dir):
        logger.error("Failed to truncate task tracker")
        success = False
    
    # Clean profiler output
    logger.info("Cleaning profiler output files...")
    if not clean_profiler_output(project_dir):
        logger.error("Failed to clean profiler output")
        success = False
    
    if success:
        logger.info("Repository cleanup completed successfully")
    else:
        logger.error("Repository cleanup completed with errors")
    
    return success


def create_pull_request(project_dir: Path, title: str, body: str) -> bool:
    """
    Create GitHub pull request using PullRequestManager.
    
    Args:
        project_dir: Path to project directory
        title: PR title
        body: PR body/description
        
    Returns:
        True if PR created successfully, False otherwise
    """
    logger.info("Creating GitHub pull request...")
    
    try:
        # Get current and parent branches
        current_branch = get_current_branch_name(project_dir)
        if current_branch is None:
            logger.error("Could not determine current branch")
            return False
        
        parent_branch = get_parent_branch_name(project_dir)
        if parent_branch is None:
            logger.error("Could not determine parent branch")
            return False
        
        # Create PR using PullRequestManager
        pr_manager = PullRequestManager(project_dir)
        pr_result = pr_manager.create_pull_request(
            title=title,
            head_branch=current_branch,
            base_branch=parent_branch,
            body=body
        )
        
        if not pr_result or not pr_result.get("number"):
            logger.error("Failed to create pull request")
            return False
        
        pr_number = pr_result["number"]
        pr_url = pr_result.get("url", "")
        
        logger.info(f"Pull request created successfully: #{pr_number}")
        if pr_url:
            logger.info(f"PR URL: {pr_url}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating pull request: {e}")
        return False


def log_step(message: str) -> None:
    """Log step with structured logging instead of print."""
    logger.info(message)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments including project directory and log level."""
    parser = argparse.ArgumentParser(
        description="Create pull request workflow script that generates PR summary and cleans up repository."
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
    """Main workflow orchestration function - creates PR and cleans up repository."""
    # Parse command line arguments
    args = parse_arguments()
    project_dir = resolve_project_dir(args.project_dir)
    
    # Setup logging early
    setup_logging(args.log_level)
    
    log_step("Starting create PR workflow...")
    log_step(f"Using project directory: {project_dir}")
    
    # Step 1: Check prerequisites
    log_step("Step 1/4: Checking prerequisites...")
    if not check_prerequisites(project_dir):
        logger.error("Prerequisites check failed")
        sys.exit(1)
    
    # Step 2: Generate PR summary
    log_step("Step 2/5: Generating PR summary...")
    title, body = generate_pr_summary(project_dir, args.llm_method)
    
    # Step 3: Push any existing commits
    log_step("Step 3/5: Pushing commits...")
    push_result = git_push(project_dir)
    if not push_result["success"]:
        logger.warning(f"Failed to push commits: {push_result['error']}")
    else:
        log_step("Commits pushed successfully")
    
    # Step 4: Create pull request
    log_step("Step 4/5: Creating pull request...")
    if not create_pull_request(project_dir, title, body):
        logger.error("Failed to create pull request")
        sys.exit(1)
    
    # Step 5: Clean up repository
    log_step("Step 5/5: Cleaning up repository...")
    cleanup_success = cleanup_repository(project_dir)
    
    if cleanup_success:
        # Check if there are changes to commit
        if not is_working_directory_clean(project_dir):
            # Commit cleanup changes
            log_step("Committing cleanup changes...")
            commit_result = commit_all_changes(
                "Clean up pr_info/steps planning files", 
                project_dir
            )
            
            if commit_result["success"]:
                log_step(f"Cleanup committed: {commit_result['commit_hash']}")
                
                # Push cleanup commit
                log_step("Pushing cleanup changes...")
                push_result = git_push(project_dir)
                
                if push_result["success"]:
                    log_step("Cleanup changes pushed successfully")
                else:
                    logger.warning(f"Failed to push cleanup changes: {push_result['error']}")
            else:
                # Don't warn about "No staged files" - this is expected when cleanup had no effect
                error_msg = commit_result.get("error", "")
                if error_msg and "No staged files" in error_msg:
                    log_step("No cleanup changes to commit (files were already clean)")
                else:
                    logger.warning(f"Failed to commit cleanup changes: {commit_result['error']}")
        else:
            log_step("No cleanup changes to commit")
    else:
        logger.warning("Repository cleanup completed with errors, but PR was created successfully")
    
    log_step("Create PR workflow completed successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
