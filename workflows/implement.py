#!/usr/bin/env python3
"""
Simple implement workflow script that orchestrates existing mcp-coder functionality.

This script automates the implementation process by:
1. Checking for incomplete tasks using task_tracker
2. Getting prompt using get_prompt()
3. Calling LLM using ask_llm()
4. Saving conversation to pr_info/.conversations/
5. Formatting code using formatters
6. Committing using subprocess call to mcp-coder commit auto

Algorithm:
1. Check prerequisites (git status, task tracker exists)
2. Check for incomplete tasks (entrance condition)
3. Get implementation prompt template using get_prompt()
4. Call LLM with prompt using ask_llm()
5. Save conversation to pr_info/.conversations/step_N.md
6. Run formatters (black, isort) using existing format_code()
7. Commit changes using generate_commit_message_with_llm() and commit_all_changes()
8. Early exit on failures with clear error messages
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from mcp_coder.cli.commands.commit import generate_commit_message_with_llm
from mcp_coder.formatters import format_code
from mcp_coder.llm_interface import ask_llm
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.git_operations import commit_all_changes
from mcp_coder.workflow_utils.task_tracker import get_incomplete_tasks


# Constants
PR_INFO_DIR = "pr_info"
CONVERSATIONS_DIR = f"{PR_INFO_DIR}/.conversations"


def log_step(message: str) -> None:
    """Log step with timestamp for consistent logging format."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def check_prerequisites() -> bool:
    """Verify dependencies and prerequisites are met."""
    log_step("Checking prerequisites...")
    
    # Check if we're in a git repository
    if not os.path.exists(".git"):
        print("Error: Not a git repository")
        return False
    
    # Check if task tracker exists
    task_tracker_path = Path(PR_INFO_DIR) / "TASK_TRACKER.md"
    if not task_tracker_path.exists():
        print(f"Error: {task_tracker_path} not found")
        return False
    
    log_step("Prerequisites check passed")
    return True


def get_next_task() -> Optional[str]:
    """Get next incomplete task from task tracker."""
    log_step("Checking for incomplete tasks...")
    
    try:
        incomplete_tasks = get_incomplete_tasks(PR_INFO_DIR)
        if not incomplete_tasks:
            log_step("No incomplete tasks found")
            return None
        
        next_task = incomplete_tasks[0]
        log_step(f"Found next task: {next_task}")
        return next_task
    
    except Exception as e:
        print(f"Error getting incomplete tasks: {e}")
        return None


def save_conversation(content: str, step_num: int) -> None:
    """Save conversation content to pr_info/.conversations/step_N.md."""
    log_step(f"Saving conversation for step {step_num}...")
    
    # Create conversations directory if it doesn't exist
    conversations_dir = Path(CONVERSATIONS_DIR)
    conversations_dir.mkdir(parents=True, exist_ok=True)
    
    # Find next available filename for this step
    base_name = f"step_{step_num}"
    counter = 1
    filename = f"{base_name}.md"
    
    while (conversations_dir / filename).exists():
        counter += 1
        filename = f"{base_name}_{counter}.md"
    
    # Save the conversation
    conversation_path = conversations_dir / filename
    conversation_path.write_text(content, encoding="utf-8")
    
    log_step(f"Conversation saved to {conversation_path}")


def run_formatters() -> bool:
    """Run code formatters (black, isort) and return success status."""
    log_step("Running code formatters...")
    
    try:
        project_root = Path.cwd()
        results = format_code(project_root, formatters=["black", "isort"])
        
        # Check if any formatter failed
        for formatter_name, result in results.items():
            if not result.success:
                print(f"Error: {formatter_name} formatting failed: {result.error_message}")
                return False
            log_step(f"{formatter_name} formatting completed successfully")
        
        log_step("All formatters completed successfully")
        return True
    
    except Exception as e:
        print(f"Error running formatters: {e}")
        return False


def commit_changes() -> bool:
    """Commit changes using existing git operations and return success status."""
    log_step("Committing changes...")
    
    try:
        project_dir = Path.cwd()
        success, commit_message, error = generate_commit_message_with_llm(project_dir)
        
        if not success:
            print(f"Error generating commit message: {error}")
            return False
        
        # Commit using the generated message
        commit_result = commit_all_changes(commit_message, project_dir)
        
        if not commit_result["success"]:
            print(f"Error committing changes: {commit_result['error']}")
            return False
        
        log_step(f"Changes committed successfully: {commit_result['commit_hash']}")
        return True
    
    except Exception as e:
        print(f"Error committing changes: {e}")
        return False


def main() -> None:
    """Main workflow orchestration function."""
    log_step("Starting implement workflow...")
    
    # Step 1: Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Step 2: Check for incomplete tasks (entrance condition)
    next_task = get_next_task()
    if not next_task:
        log_step("No incomplete tasks found - workflow complete")
        sys.exit(0)
    
    # Step 3: Get implementation prompt template
    log_step("Loading implementation prompt template...")
    try:
        prompt_template = get_prompt("mcp_coder/prompts/prompts.md", "Implementation Prompt Template using task tracker")
    except Exception as e:
        print(f"Error loading prompt template: {e}")
        sys.exit(1)
    
    # Step 4: Call LLM with prompt
    log_step("Calling LLM for implementation...")
    try:
        # Create the full prompt by combining template with task context
        full_prompt = f"""{prompt_template}

Current task from TASK_TRACKER.md: {next_task}

Please implement this task step by step."""
        
        response = ask_llm(full_prompt, provider="claude", method="api", timeout=600)
        
        if not response or not response.strip():
            print("Error: LLM returned empty response")
            sys.exit(1)
        
        log_step("LLM response received successfully")
    
    except Exception as e:
        print(f"Error calling LLM: {e}")
        sys.exit(1)
    
    # Step 5: Save conversation
    try:
        # Extract step number from task for conversation naming
        step_match = re.search(r'Step (\d+)', next_task)
        step_num = int(step_match.group(1)) if step_match else 1
        
        conversation_content = f"""# Implementation Task: {next_task}

## Prompt Sent to LLM:
{full_prompt}

## LLM Response:
{response}

---
Generated on: {datetime.now().isoformat()}
"""
        
        save_conversation(conversation_content, step_num)
    
    except Exception as e:
        print(f"Error saving conversation: {e}")
        sys.exit(1)
    
    # Step 6: Run formatters
    if not run_formatters():
        sys.exit(1)
    
    # Step 7: Commit changes
    if not commit_changes():
        sys.exit(1)
    
    log_step("Implement workflow completed successfully!")


if __name__ == "__main__":
    main()
