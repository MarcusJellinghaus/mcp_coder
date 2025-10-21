"""Core workflow logic for create-pr command.

This module will be fully implemented in Step 2.
For now, it contains a stub to allow CLI command testing.
"""

from pathlib import Path


def run_create_pr_workflow(project_dir: Path, provider: str, method: str) -> int:
    """Execute the create-pr workflow.

    This is a stub implementation that will be replaced in Step 2.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider to use (e.g., 'claude')
        method: LLM method to use (e.g., 'cli' or 'api')

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    raise NotImplementedError("run_create_pr_workflow will be implemented in Step 2")
