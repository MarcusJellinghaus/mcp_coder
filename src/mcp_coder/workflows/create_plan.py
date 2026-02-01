#!/usr/bin/env python3
"""
Create plan workflow script for GitHub issue planning.

This module orchestrates the complete plan generation workflow including
argument parsing, prerequisite validation, branch management, prompt execution,
and output validation.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS, PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.session import parse_llm_method
from mcp_coder.llm.storage.session_storage import store_session
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.git_operations.branches import checkout_branch
from mcp_coder.utils.git_operations.readers import is_working_directory_clean
from mcp_coder.utils.git_operations.remotes import git_push
from mcp_coder.utils.git_operations.workflows import commit_all_changes
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.utils.github_operations.issue_branch_manager import IssueBranchManager
from mcp_coder.utils.github_operations.issue_manager import IssueData, IssueManager
from mcp_coder.workflow_utils.task_tracker import TASK_TRACKER_TEMPLATE

# Setup logger
logger = logging.getLogger(__name__)

# Timeout for Implementation Plan Creation prompt (15 minutes)
# This prompt requires more time than the standard 600s timeout used by other prompts
# because it generates detailed multi-file implementation plans with pseudocode and algorithms.
PROMPT_3_TIMEOUT = 900  # 15 minutes


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
        if not is_working_directory_clean(
            project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
        ):
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
        issue_data = issue_manager.get_issue(issue_number)  # pylint: disable=no-member

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


def manage_branch(
    project_dir: Path,
    issue_number: int,
    issue_title: str,
    base_branch: Optional[str] = None,
) -> Optional[str]:
    """Get existing linked branch or create new one.

    Args:
        project_dir: Path to the project directory containing git repository
        issue_number: GitHub issue number to link branch to
        issue_title: GitHub issue title for branch name generation
        base_branch: Optional base branch to create from (uses repo default if None)

    Returns:
        Branch name if successful, None on error
    """
    logger.info("Managing branch for issue #%d...", issue_number)

    try:
        # Create IssueBranchManager instance
        manager = IssueBranchManager(project_dir)

        # Get linked branches
        linked_branches = manager.get_linked_branches(issue_number)

        # If linked branches exist, use the first one
        if linked_branches:
            branch_name = linked_branches[0]
            logger.info("Using existing linked branch: %s", branch_name)
        else:
            # Create new branch on GitHub
            result = manager.create_remote_branch_for_issue(
                issue_number,
                base_branch=base_branch,
            )
            if not result["success"]:
                logger.error(
                    "Failed to create branch: %s", result.get("error", "Unknown error")
                )
                return None
            branch_name = result["branch_name"]
            logger.info("Created new branch: %s", branch_name)

        # Checkout the branch locally
        if not checkout_branch(branch_name, project_dir):
            logger.error("Failed to checkout branch: %s", branch_name)
            return None

        logger.info("Switched to branch: %s", branch_name)
        return branch_name

    except Exception as e:
        logger.error("Error managing branch: %s", e)
        return None


def check_pr_info_not_exists(project_dir: Path) -> bool:
    """Check that pr_info/ directory does not exist.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if pr_info/ does not exist, False if it exists
    """
    pr_info_dir = project_dir / "pr_info"

    return not pr_info_dir.exists()


def create_pr_info_structure(project_dir: Path) -> bool:
    """Create pr_info/ directory structure and TASK_TRACKER.md.

    Creates:
    - pr_info/
    - pr_info/steps/
    - pr_info/.conversations/
    - pr_info/TASK_TRACKER.md (from template)

    Args:
        project_dir: Path to the project directory

    Returns:
        True if successful, False on error
    """
    try:
        # Build base path
        pr_info_dir = project_dir / "pr_info"

        # Create pr_info/ directory
        pr_info_dir.mkdir(parents=True, exist_ok=False)

        # Create pr_info/steps/ directory
        steps_dir = pr_info_dir / "steps"
        steps_dir.mkdir()

        # Create pr_info/.conversations/ directory
        conversations_dir = pr_info_dir / ".conversations"
        conversations_dir.mkdir()

        # Write TASK_TRACKER_TEMPLATE to pr_info/TASK_TRACKER.md
        task_tracker_path = pr_info_dir / "TASK_TRACKER.md"
        task_tracker_path.write_text(TASK_TRACKER_TEMPLATE, encoding="utf-8")

        logger.info("Created pr_info/ directory structure successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to create pr_info/ directory structure: {e}")
        return False


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


def format_initial_prompt(prompt_template: str, issue_data: IssueData) -> str:
    """Format initial analysis prompt with issue content.

    Args:
        prompt_template: The prompt template string
        issue_data: IssueData object with issue details

    Returns:
        Combined prompt text with issue data appended
    """
    # Create issue section
    issue_section = (
        "---\n"
        "## Issue to Implement:\n"
        f"**Title:** {issue_data['title']}\n"
        f"**Number:** #{issue_data['number']}\n"
        "**Description:**\n"
        f"{issue_data['body']}"
    )

    # Append to prompt template
    return prompt_template + "\n\n" + issue_section


def run_planning_prompts(
    project_dir: Path,
    issue_data: IssueData,
    llm_method: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
) -> bool:
    """Execute three planning prompts with session continuation.

    Args:
        project_dir: Path to the project directory
        issue_data: IssueData object with issue details
        llm_method: LLM method string (e.g., "claude_code_cli")
        mcp_config: Optional path to MCP configuration file
        execution_dir: Optional working directory for Claude subprocess

    Returns:
        True if all prompts succeed, False on error
    """
    logger.info("Starting planning prompt execution...")

    # Prepare environment variables for LLM subprocess
    env_vars = prepare_llm_environment(project_dir)
    logger.debug(f"Environment variables prepared: {list(env_vars.keys())}")

    # Get branch name for logging (with issue_id fallback)
    branch_name = get_branch_name_for_logging(project_dir, issue_data["number"])

    # Prepare session storage path (relative to project directory)
    session_storage_path = str(project_dir / ".mcp-coder" / "create_plan_sessions")
    logger.info(f"Conversation logs will be stored in: {session_storage_path}")

    # Load all three prompts
    logger.info("Loading prompt templates...")
    prompt_1 = _load_prompt_or_exit("Initial Analysis")
    logger.debug(
        f"Prompt 1 loaded: {len(prompt_1)} chars, preview: {prompt_1[:200]}..."
    )

    prompt_2 = _load_prompt_or_exit("Simplification Review")
    logger.debug(
        f"Prompt 2 loaded: {len(prompt_2)} chars, preview: {prompt_2[:200]}..."
    )

    prompt_3 = _load_prompt_or_exit("Implementation Plan Creation")
    logger.debug(
        f"Prompt 3 loaded: {len(prompt_3)} chars, preview: {prompt_3[:200]}..."
    )

    # Format initial prompt with issue data
    formatted_prompt_1 = format_initial_prompt(prompt_1, issue_data)
    logger.debug(
        f"Formatted prompt 1: {len(formatted_prompt_1)} chars (includes issue data)"
    )

    # Parse llm_method
    try:
        provider, method = parse_llm_method(llm_method)
        logger.debug(f"LLM method: provider={provider}, method={method}")
    except ValueError as e:
        logger.error(f"Invalid LLM method: {e}")
        return False

    # Execute first prompt
    logger.info("Executing prompt 1: Initial Analysis...")
    logger.debug(f"Sending {len(formatted_prompt_1)} chars to LLM with timeout=600s")
    try:
        response_1 = prompt_llm(
            formatted_prompt_1,
            provider=provider,
            method=method,
            session_id=None,
            timeout=600,
            env_vars=env_vars,
            project_dir=str(project_dir),
            execution_dir=str(execution_dir) if execution_dir else None,
            mcp_config=mcp_config,
            branch_name=branch_name,
        )

        if not response_1 or not response_1.get("text"):
            logger.error("Prompt 1 returned empty response")
            return False

        session_id = response_1.get("session_id")
        if not session_id:
            logger.error("Prompt 1 did not return session_id")
            return False

        logger.info(f"Prompt 1 completed (session: {session_id})")

        # Store conversation for logging/debugging
        try:
            # Convert LLMResponseDict to format expected by store_session
            response_data = {
                "text": response_1["text"],
                "session_info": {
                    "session_id": session_id,
                    "model": response_1.get("provider", "claude"),
                },
                "result_info": response_1.get("raw_response", {}),
            }
            stored_path = store_session(
                response_data, "Initial Analysis", store_path=session_storage_path
            )
            logger.info(f"Prompt 1 conversation logged to file: {stored_path}")
            logger.debug(f"  Response length: {len(response_1['text'])} chars")
        except Exception as storage_error:
            logger.warning(f"Failed to store prompt 1 conversation: {storage_error}")

    except Exception as e:
        logger.error(f"Error executing prompt 1: {e}")
        return False

    # Execute second prompt with session continuation
    logger.info("Executing prompt 2: Simplification Review...")
    logger.debug(
        f"Sending {len(prompt_2)} chars to LLM with session_id={session_id[:16]}... timeout=600s"
    )
    try:
        response_2 = prompt_llm(
            prompt_2,
            provider=provider,
            method=method,
            session_id=session_id,
            timeout=600,
            env_vars=env_vars,
            project_dir=str(project_dir),
            execution_dir=str(execution_dir) if execution_dir else None,
            mcp_config=mcp_config,
            branch_name=branch_name,
        )

        if not response_2 or not response_2.get("text"):
            logger.error("Prompt 2 returned empty response")
            return False

        logger.info("Prompt 2 completed")

        # Store conversation for logging/debugging
        try:
            response_data = {
                "text": response_2["text"],
                "session_info": {
                    "session_id": session_id,
                    "model": response_2.get("provider", "claude"),
                },
                "result_info": response_2.get("raw_response", {}),
            }
            stored_path = store_session(
                response_data, "Simplification Review", store_path=session_storage_path
            )
            logger.info(f"Prompt 2 conversation logged to file: {stored_path}")
            logger.debug(f"  Response length: {len(response_2['text'])} chars")
        except Exception as storage_error:
            logger.warning(f"Failed to store prompt 2 conversation: {storage_error}")

    except Exception as e:
        logger.error(f"Error executing prompt 2: {e}")
        return False

    # Execute third prompt with session continuation
    logger.info("Executing prompt 3: Implementation Plan Creation...")
    logger.debug(
        f"Sending {len(prompt_3)} chars to LLM with session_id={session_id[:16]}... timeout={PROMPT_3_TIMEOUT}s"
    )
    try:
        response_3 = prompt_llm(
            prompt_3,
            provider=provider,
            method=method,
            session_id=session_id,
            timeout=PROMPT_3_TIMEOUT,
            env_vars=env_vars,
            project_dir=str(project_dir),
            execution_dir=str(execution_dir) if execution_dir else None,
            mcp_config=mcp_config,
            branch_name=branch_name,
        )

        if not response_3 or not response_3.get("text"):
            logger.error("Prompt 3 returned empty response")
            return False

        logger.info("Prompt 3 completed")

        # Store conversation for logging/debugging
        try:
            response_data = {
                "text": response_3["text"],
                "session_info": {
                    "session_id": session_id,
                    "model": response_3.get("provider", "claude"),
                },
                "result_info": response_3.get("raw_response", {}),
            }
            stored_path = store_session(
                response_data,
                "Implementation Plan Creation",
                store_path=session_storage_path,
            )
            logger.info(f"Prompt 3 conversation logged to file: {stored_path}")
            logger.debug(f"  Response length: {len(response_3['text'])} chars")
        except Exception as storage_error:
            logger.warning(f"Failed to store prompt 3 conversation: {storage_error}")

    except Exception as e:
        logger.error(f"Error executing prompt 3: {e}")
        return False

    logger.info("All planning prompts executed successfully")
    logger.info(f"Full conversation session ID: {session_id}")
    logger.info(f"Conversation logs stored in: {session_storage_path}/")
    return True


def validate_output_files(project_dir: Path) -> bool:
    """Validate required output files exist.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if files exist, False otherwise
    """
    logger.info("Validating output files...")

    summary_path = project_dir / "pr_info" / "steps" / "summary.md"
    step_1_path = project_dir / "pr_info" / "steps" / "step_1.md"

    if not summary_path.exists():
        logger.error(f"Required file not found: {summary_path}")
        return False

    if not step_1_path.exists():
        logger.error(f"Required file not found: {step_1_path}")
        return False

    logger.info("✓ Required output files exist")
    return True


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


def run_create_plan_workflow(
    issue_number: int,
    project_dir: Path,
    provider: str,
    method: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
    update_labels: bool = False,
) -> int:
    """Main workflow orchestration function - creates implementation plan for GitHub issue.

    Args:
        issue_number: GitHub issue number to create plan for
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
        mcp_config: Optional path to MCP configuration file
        execution_dir: Optional working directory for Claude subprocess
        update_labels: If True, update GitHub issue labels on success

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    # Note: Logging already setup by CLI layer
    # Note: project_dir already resolved and validated by CLI layer

    # Combine provider and method for legacy function compatibility
    llm_method = f"{provider}_code_{method}"

    logger.info(f"Starting create plan workflow for project: {project_dir}")
    logger.info(f"GitHub issue number: {issue_number}")
    logger.info(f"LLM method: {llm_method}")

    # Step 1: Validate prerequisites
    logger.info("Step 1/7: Validating prerequisites...")
    success, issue_data = check_prerequisites(project_dir, issue_number)
    if not success:
        logger.error("Prerequisites validation failed")
        return 1

    # Step 2: Manage branch
    logger.info("Step 2/7: Managing branch...")
    base_branch = issue_data.get("base_branch")
    if base_branch:
        logger.info(f"Using base branch from issue: {base_branch}")
    branch_name = manage_branch(
        project_dir,
        issue_number,
        issue_data["title"],
        base_branch=base_branch,
    )
    if branch_name is None:
        logger.error("Branch management failed")
        return 1

    # Step 3: Check pr_info/ doesn't exist and create structure
    logger.info("Step 3/7: Setting up pr_info/ directory structure...")
    if not check_pr_info_not_exists(project_dir):
        logger.error(
            "pr_info/ directory already exists. Please clean up before creating a new plan."
        )
        return 1

    if not create_pr_info_structure(project_dir):
        logger.error("Failed to create pr_info/ directory structure")
        return 1

    # Step 4: Run initial analysis
    logger.info(
        f"Step 4/7: Running initial analysis for issue #{issue_number} '{issue_data['title']}'..."
    )

    # Step 5: Run simplification review
    logger.info("Step 5/7: Running simplification review...")

    # Step 6: Generate implementation plan
    logger.info("Step 6/7: Generating implementation plan...")
    if not run_planning_prompts(
        project_dir, issue_data, llm_method, mcp_config, execution_dir
    ):
        logger.error("Planning prompts execution failed")
        return 1

    # Step 7: Validate output files
    logger.info("Step 7/7: Validating output files...")
    if not validate_output_files(project_dir):
        logger.error("Output files validation failed")
        return 1

    # Commit changes
    logger.info("Committing generated plan...")
    commit_message = f"Initial plan generated for issue #{issue_number}"
    commit_result = commit_all_changes(commit_message, project_dir)
    if not commit_result["success"]:
        logger.warning(f"Commit failed: {commit_result.get('error')}")
    else:
        logger.info(f"Committed with hash: {commit_result['commit_hash']}")

    # Push changes
    logger.info("Pushing changes to remote...")
    push_result = git_push(project_dir)
    if not push_result["success"]:
        logger.warning(f"Push failed: {push_result.get('error')}")
    else:
        logger.info("Successfully pushed changes to remote")

    # Update GitHub issue label if requested
    if update_labels:
        logger.info("Updating GitHub issue label...")
        try:
            issue_manager = IssueManager(project_dir)
            success = issue_manager.update_workflow_label(
                from_label_id="planning",
                to_label_id="plan_review",
            )

            if success:
                logger.info("✓ Issue label updated: planning → plan-review")
            else:
                logger.warning("✗ Failed to update issue label (non-blocking)")

        except Exception as e:
            logger.error(f"Error updating issue label (non-blocking): {e}")

    logger.info("Create plan workflow completed successfully!")
    return 0
