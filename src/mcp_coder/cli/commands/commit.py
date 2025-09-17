"""Commit commands for the MCP Coder CLI."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

from ...utils.git_operations import (
    is_git_repository,
    stage_all_changes,
    get_git_diff_for_commit,
    commit_staged_files,
)
from ...llm_interface import ask_llm
from ...prompt_manager import get_prompt
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
        print(f"\nGenerated commit message:")
        print("=" * 50)
        print(commit_message)
        print("=" * 50)
        
        response = input("\nProceed with commit? (y/N): ").strip().lower()
        if response != 'y':
            print("Commit cancelled.")
            return 0
    
    # 4. Create commit
    commit_result = commit_staged_files(commit_message, project_dir)
    if not commit_result["success"]:
        print(f"Error: {commit_result['error']}", file=sys.stderr)
        return 2
        
    print(f"✅ Commit created: {commit_result['commit_hash']}")
    return 0


def generate_commit_message_with_llm(project_dir: Path) -> Tuple[bool, str, Optional[str]]:
    """Generate commit message using LLM. Returns (success, message, error)."""
    logger.debug("Generating commit message with LLM for %s", project_dir)
    
    try:
        # Stage all changes first
        if not stage_all_changes(project_dir):
            return False, "", "Failed to stage changes"
        
        # Get git diff
        git_diff = get_git_diff_for_commit(project_dir)
        if git_diff is None:
            return False, "", "Failed to get git diff"
        
        if not git_diff.strip():
            return False, "", "No changes to commit"
        
        # Load commit prompt
        try:
            base_prompt = get_prompt(
                "src/mcp_coder/prompts/prompts.md", 
                "Git Commit Message Generation"
            )
        except Exception as e:
            logger.error("Failed to load commit prompt: %s", e)
            return False, "", "Failed to load commit prompt template"
        
        # Combine prompt with git diff
        full_prompt = f"{base_prompt}\n\n=== GIT DIFF ===\n{git_diff}"
        
        # Ask LLM with API method (as specified in the requirements)
        logger.debug("Sending prompt to LLM")
        response = ask_llm(full_prompt, provider="claude", method="api")
        
        # Parse response
        commit_message, _ = parse_llm_commit_response(response)
        
        if not commit_message.strip():
            return False, "", "LLM returned empty commit message"
        
        logger.info("Successfully generated commit message: %s", commit_message.split('\n')[0])
        return True, commit_message, None
        
    except Exception as e:
        logger.error("Error generating commit message with LLM: %s", e)
        return False, "", f"LLM communication failed: {str(e)}"


def parse_llm_commit_response(response: str) -> Tuple[str, Optional[str]]:
    """Parse LLM response into commit summary and body."""
    if not response or not response.strip():
        return "", None
    
    # Split response into lines
    lines = response.strip().split('\n')
    
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
    body = '\n'.join(body_lines) if body_lines else None
    
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
