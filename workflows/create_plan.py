#!/usr/bin/env python3
"""
Create plan workflow script for generating implementation plans from GitHub issues.

This module orchestrates the plan generation workflow including:
- Validating prerequisites (clean git state, issue exists)
- Managing branches (create or use existing issue-linked branch)
- Generating implementation plan using LLM prompts
- Creating structured task breakdown
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from mcp_coder.utils.log_utils import setup_logging

# Setup logger
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments including project directory and log level.
    
    Returns:
        argparse.Namespace with parsed arguments:
        - issue_number: int (required)
        - project_dir: Optional[str]
        - log_level: str (default: "INFO")
        - llm_method: str (default: "claude_code_cli")
    """
    parser = argparse.ArgumentParser(
        description="Create plan workflow script that generates implementation plan from GitHub issue."
    )
    parser.add_argument(
        "issue_number",
        type=int,
        help="GitHub issue number to create plan for"
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


def resolve_project_dir(project_dir_arg: Optional[str]) -> Path:
    """
    Convert project directory argument to absolute Path, with validation.
    
    Validates that the directory:
    - Exists and is accessible
    - Is a directory (not a file)
    - Contains a .git subdirectory (is a git repository)
    
    Args:
        project_dir_arg: Optional project directory path from CLI argument
        
    Returns:
        Path: Absolute, validated path to project directory
        
    Exits:
        Exits with error code 1 if validation fails
    """
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
    """Main workflow orchestration function - generates implementation plan from issue."""
    # Parse command line arguments
    args = parse_arguments()
    project_dir = resolve_project_dir(args.project_dir)
    
    # Setup logging early
    setup_logging(args.log_level)
    
    logger.info("Starting create plan workflow...")
    logger.info(f"Issue number: {args.issue_number}")
    logger.info(f"Using project directory: {project_dir}")
    logger.info(f"LLM method: {args.llm_method}")
    
    # TODO: Implement workflow steps in subsequent tasks
    logger.info("Workflow implementation pending - argument parsing complete")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
