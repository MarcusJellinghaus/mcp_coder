#!/usr/bin/env python3
"""
Create plan workflow script for GitHub issue planning.

This module orchestrates the complete plan generation workflow including
argument parsing, prerequisite validation, branch management, prompt execution,
and output validation.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from mcp_coder.utils.git_operations.repository import is_working_directory_clean
from mcp_coder.utils.github_operations.issue_manager import IssueData, IssueManager
from mcp_coder.utils.log_utils import setup_logging

# Setup logger
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments including project directory and log level."""
    parser = argparse.ArgumentParser(
        description="Create plan workflow script that generates implementation plan for GitHub issue."
    )
    parser.add_argument(
        "issue_number",
        type=int,
        help="GitHub issue number (required)"
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
        default="claude_code_cli",
        help="LLM method to use (default: claude_code_cli)"
    )

    return parser.parse_args()


def check_prerequisites(project_dir: Path, issue_number: int) -> tuple[bool, IssueData]:
    """Validate prerequisites for plan creation workflow.
    
    Validates that the git working directory is clean and that the specified
    GitHub issue exists and is accessible.
    
    Args:
        project_dir: Path to the project directory containing git repository
        issue_number: GitHub issue number to validate
        
    Returns:
        Tuple of (success: bool, issue_data: IssueData)
        - success: True if all prerequisites pass, False otherwise
        - issue_data: IssueData object with issue details, or empty IssueData on failure
    """
    logger.info("Checking prerequisites for plan creation...")
    
    # Create empty IssueData for failure cases
    empty_issue_data = IssueData(
        number=0,
        title="",
        body="",
        state="",
        labels=[],
        assignees=[],
        user=None,
        created_at=None,
        updated_at=None,
        url="",
        locked=False,
    )
    
    # Check if git working directory is clean
    try:
        if not is_working_directory_clean(project_dir):
            logger.error(
                "✗ Git working directory is not clean. "
                "Please commit or stash your changes before creating a plan."
            )
            return (False, empty_issue_data)
        logger.info("✓ Git working directory is clean")
    except ValueError as e:
        logger.error(f"✗ Error checking git status: {e}")
        return (False, empty_issue_data)
    except Exception as e:
        logger.error(f"✗ Unexpected error checking git status: {e}")
        return (False, empty_issue_data)
    
    # Fetch and validate GitHub issue
    try:
        issue_manager = IssueManager(project_dir)
        issue_data = issue_manager.get_issue(issue_number)
        
        # Check if issue was found (number == 0 indicates not found)
        if issue_data["number"] == 0:
            logger.error(f"✗ Issue #{issue_number} not found or not accessible")
            return (False, empty_issue_data)
        
        logger.info(f"✓ Issue #{issue_data['number']} exists: '{issue_data['title']}'")
        
    except Exception as e:
        logger.error(f"✗ Error fetching issue #{issue_number}: {e}")
        return (False, empty_issue_data)
    
    logger.info("All prerequisites passed")
    return (True, issue_data)


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
    """Main workflow orchestration function - creates implementation plan for GitHub issue."""
    # Parse command line arguments
    args = parse_arguments()
    project_dir = resolve_project_dir(args.project_dir)
    
    # Setup logging early
    setup_logging(args.log_level)
    
    logger.info("Starting create plan workflow...")
    logger.info(f"Using project directory: {project_dir}")
    logger.info(f"GitHub issue number: {args.issue_number}")
    logger.info(f"LLM method: {args.llm_method}")
    
    # Placeholder for future implementation
    logger.info("Workflow implementation in progress...")
    
    logger.info("Create plan workflow completed successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
