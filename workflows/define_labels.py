#!/usr/bin/env python3
"""
Define labels workflow script for GitHub repository label management.

This module provides functionality to define and apply workflow status labels
to a GitHub repository, ensuring consistent label definitions across projects.
"""

import logging
import re

# Setup logger
logger = logging.getLogger(__name__)


# Workflow status labels definition
# Format: (name, color, description)
# Colors are 6-character hex codes WITHOUT '#' prefix (GitHub API format)
WORKFLOW_LABELS = [
    ("status-01:created", "10b981", "Fresh issue, may need refinement"),
    ("status-02:awaiting-planning", "6ee7b7", "Issue is refined and ready for implementation planning"),
    ("status-03:planning", "a7f3d0", "Implementation plan being drafted (auto/in-progress)"),
    ("status-04:plan-review", "3b82f6", "First implementation plan available for review/discussion"),
    ("status-05:plan-ready", "93c5fd", "Implementation plan approved, ready to code"),
    ("status-06:implementing", "bfdbfe", "Code being written (auto/in-progress)"),
    ("status-07:code-review", "f59e0b", "Implementation complete, needs code review"),
    ("status-08:ready-pr", "fbbf24", "Approved for pull request creation"),
    ("status-09:pr-creating", "fed7aa", "Bot is creating the pull request (auto/in-progress)"),
    ("status-10:pr-created", "8b5cf6", "Pull request created, awaiting approval/merge"),
]


def _validate_color_format(color: str) -> bool:
    """Validate that color is a 6-character hex code.
    
    Args:
        color: Color string to validate
        
    Returns:
        True if valid 6-character hex code, False otherwise
    """
    return isinstance(color, str) and bool(re.match(r'^[0-9A-Fa-f]{6}$', color))


# Validate all colors at module load time
def _validate_workflow_labels() -> None:
    """Validate WORKFLOW_LABELS structure and color formats at module load.
    
    Raises:
        ValueError: If any label has invalid structure or color format
    """
    for label in WORKFLOW_LABELS:
        if not isinstance(label, tuple) or len(label) != 3:
            raise ValueError(f"Invalid label structure: {label}. Expected (name, color, description) tuple.")
        
        name, color, description = label
        
        if not isinstance(name, str) or not name:
            raise ValueError(f"Invalid label name: {name}. Must be non-empty string.")
        
        if not _validate_color_format(color):
            raise ValueError(f"Invalid color format for label '{name}': {color}. Expected 6-character hex code.")
        
        if not isinstance(description, str):
            raise ValueError(f"Invalid description for label '{name}': {description}. Must be string.")


# Perform validation at module load
_validate_workflow_labels()
