#!/usr/bin/env python3
"""
Create pull request workflow script for repository cleanup operations.

This module provides utility functions for cleaning up repository state
after feature implementation is complete.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

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