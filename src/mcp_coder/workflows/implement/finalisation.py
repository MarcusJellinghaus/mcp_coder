"""Finalisation stage for the implement workflow.

Verifies and completes any remaining tasks after the main task loop, then
commits and pushes the resulting changes.
"""

import logging
from pathlib import Path
from typing import Optional

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.storage.session_storage import store_session
from mcp_coder.mcp_workspace_git import commit_all_changes, get_full_status
from mcp_coder.prompt_manager import get_prompt_with_substitutions
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.workflow_utils.commit_operations import generate_commit_message_with_llm
from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerFileNotFoundError,
    has_incomplete_work,
)

from .constants import (
    COMMIT_MESSAGE_FILE,
    LLM_FINALISATION_TIMEOUT_SECONDS,
    PR_INFO_DIR,
)
from .task_processing import push_changes

logger = logging.getLogger(__name__)


def run_finalisation(
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    settings_file: str | None = None,
    execution_dir: Optional[Path] = None,
) -> bool:
    """Run implementation finalisation to verify and complete remaining tasks.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional path to MCP configuration file
        settings_file: Optional path to .claude/settings.local.json; forwarded to prompt_llm.
        execution_dir: Optional working directory for Claude subprocess

    Returns:
        bool: True if finalisation succeeded or was skipped (no tasks), False on error
    """
    logger.info("Running implementation finalisation...")

    # 1. Check if there are incomplete tasks
    try:
        pr_info_path = str(project_dir / PR_INFO_DIR)
        if not has_incomplete_work(pr_info_path):
            logger.info("No incomplete tasks - skipping finalisation")
            return True
    except TaskTrackerFileNotFoundError:
        logger.error("Task tracker not found - cannot run finalisation")
        return False

    logger.info("Found incomplete tasks - calling LLM to finalise...")

    # 2. Prepare environment and call LLM with finalisation prompt
    env_vars = prepare_llm_environment(project_dir)
    branch_name = get_branch_name_for_logging(project_dir)

    finalisation_prompt = get_prompt_with_substitutions(
        str(PROMPTS_FILE_PATH),
        "Finalisation Prompt",
        {
            "pr_info_dir": PR_INFO_DIR,
            "commit_message_path": f"{PR_INFO_DIR}/{COMMIT_MESSAGE_FILE}",
        },
    )

    llm_response = prompt_llm(
        finalisation_prompt,
        provider=provider,
        # Inactivity budget (was wall-clock), kept below the CI step cap.
        timeout=LLM_FINALISATION_TIMEOUT_SECONDS,
        env_vars=env_vars,
        execution_dir=str(execution_dir) if execution_dir else None,
        mcp_config=mcp_config,
        settings_file=settings_file,
        branch_name=branch_name,
    )
    response = llm_response["text"]
    try:
        store_session(
            llm_response,
            finalisation_prompt,
            store_path=str(project_dir / ".mcp-coder" / "implement_sessions"),
            step_name="finalisation",
            branch_name=branch_name,
        )
    except Exception as e:
        logger.warning("Failed to store finalisation session: %s", e)

    # 3. Check for empty/failed response
    if not response or not response.strip():
        logger.error("Finalisation LLM returned empty response")
        return False

    logger.debug("Finalisation LLM response received")

    # 4. Check if there are changes to commit
    status = get_full_status(project_dir)
    if not status["staged"] and not status["modified"] and not status["untracked"]:
        logger.info("No changes after finalisation - nothing to commit")
        return True

    # 5. Get commit message (3-level fallback: file → LLM → default)
    commit_message = None
    commit_msg_path = project_dir / COMMIT_MESSAGE_FILE

    # Level 1: Read from file
    if commit_msg_path.exists():
        commit_message = commit_msg_path.read_text(encoding="utf-8").strip()
        # Always delete file after reading (even if empty)
        commit_msg_path.unlink()
        if commit_message:
            logger.debug("Read and deleted commit message file")
        else:
            logger.debug("Commit message file was empty, deleted")

    # Level 2: Generate with LLM
    if not commit_message:
        logger.info("Generating commit message with LLM...")
        success, llm_message, error = generate_commit_message_with_llm(
            project_dir,
            provider=provider,
            execution_dir=str(execution_dir) if execution_dir else None,
        )
        if success and llm_message:
            commit_message = llm_message
            logger.debug("Commit message generated by LLM")
        else:
            logger.warning(f"LLM commit message generation failed: {error}")

    # Level 3: Use default
    if not commit_message:
        commit_message = "Finalisation: complete remaining tasks"
        logger.warning("Using default commit message")

    # 6. Stage all changes and commit
    logger.info("Committing finalisation changes...")
    commit_result = commit_all_changes(commit_message, project_dir)
    if not commit_result["success"]:
        logger.error(f"Failed to commit finalisation changes: {commit_result['error']}")
        return False

    # 7. Push changes
    logger.info("Pushing finalisation changes...")
    if not push_changes(project_dir):
        logger.warning("Failed to push finalisation changes")
        return False

    return True
