"""Create pull request workflow script for repository cleanup operations.

This module provides utility functions for cleaning up repository state
after feature implementation is complete and orchestrates the complete
PR creation workflow.
"""

import logging
import shutil
import time
from pathlib import Path

from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS, PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.mcp_workspace_git import (
    commit_all_changes,
    extract_issue_number_from_branch,
    get_branch_diff,
    get_current_branch_name,
    git_push,
    is_working_directory_clean,
)
from mcp_coder.mcp_workspace_github import (
    IssueBranchManager,
    IssueManager,
    PullRequestData,
    PullRequestManager,
    get_authenticated_username,
)
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.utils.repo_config import get_repo_flag
from mcp_coder.workflow_steps.prerequisites import check_git_clean, is_branch_not_base
from mcp_coder.workflow_utils.base_branch import (
    check_base_branch_on_origin,
    detect_base_branch,
)
from mcp_coder.workflow_utils.branch_linkage import is_branch_linked_to_issue
from mcp_coder.workflow_utils.failure_handling import (
    format_mcp_unavailable_message,
    llm_failure_reason,
    run_guarded,
)
from mcp_coder.workflow_utils.label_transitions import update_workflow_label
from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerFileNotFoundError,
    get_incomplete_tasks,
)
from mcp_coder.workflows.create_pr.helpers import (
    ensure_closing_reference as ensure_closing_reference,
)
from mcp_coder.workflows.create_pr.helpers import (
    handle_create_pr_failure as _handle_create_pr_failure_impl,
)
from mcp_coder.workflows.create_pr.helpers import parse_pr_summary as parse_pr_summary
from mcp_coder.workflows.create_pr.post_creation import run_post_creation
from mcp_coder.workflows.create_pr.pre_creation import _rebase_if_needed

# Note: PROMPTS_FILE_PATH imported from constants

# Setup logger
logger = logging.getLogger(__name__)


def delete_pr_info_directory(project_dir: Path) -> bool:
    """Delete the entire pr_info/ directory and all its contents.

    Args:
        project_dir: Path to the project root directory

    Returns:
        True if successful or directory doesn't exist, False on error
    """
    pr_info_dir = project_dir / "pr_info"

    # If directory doesn't exist, consider it success (no-op)
    if not pr_info_dir.exists():
        logger.info(f"Directory {pr_info_dir} does not exist - nothing to delete")
        return True

    try:
        # Remove the entire directory tree
        shutil.rmtree(pr_info_dir)
        logger.info(f"Successfully deleted directory: {pr_info_dir}")
        return True

    except PermissionError as e:
        logger.error(f"Permission error deleting {pr_info_dir}: {e}")
        return False
    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error deleting {pr_info_dir}: {e}")
        return False


def clean_profiler_output(project_dir: Path) -> bool:
    """Clean up profiler output files from docs/tests/performance_data/prof/ directory.

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
    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error cleaning {prof_dir}: {e}")
        return False


# Re-export parse_pr_summary for backward compatibility
# (imported from helpers above)


def check_prerequisites(project_dir: Path) -> bool:
    """Validate prerequisites for PR creation workflow.

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

    # Check if git working directory is clean (shared workflow step)
    if not check_git_clean(project_dir):
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
    except TaskTrackerFileNotFoundError:
        logger.info("TASK_TRACKER.md not found - skipping task completeness check")
        # Continue with other prerequisites - task tracker is optional
    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error checking incomplete tasks: {e}")
        return False

    # Check current branch (custom base resolved by the orchestrator; the
    # shared step only compares current vs base).
    try:
        current_branch = get_current_branch_name(project_dir)
        base_branch = detect_base_branch(project_dir, current_branch=current_branch)
    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error checking branch status: {e}")
        return False

    if not is_branch_not_base(current_branch, base_branch):
        return False

    logger.info("All prerequisites passed")
    return True


def generate_pr_summary(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
) -> tuple[str, str]:
    """Generate PR title and body using LLM and git diff.

    Args:
        project_dir: Path to project directory
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional path to MCP configuration file
        settings_file: Optional path to .claude/settings.local.json; forwarded to prompt_llm.

    Returns:
        Tuple of (title, body) strings

    Raises:
        ValueError: If LLM returns an empty response.
        FileNotFoundError: If the prompt template file cannot be found.
    """
    logger.info("Generating PR summary...")

    # Get base branch for diff
    current_branch = get_current_branch_name(project_dir)
    base_branch = detect_base_branch(project_dir, current_branch=current_branch)
    if base_branch is None:
        logger.error("Could not detect base branch for PR summary generation")
        return "Pull Request", "Could not generate summary - base branch unknown"

    # Get branch diff
    logger.info("Getting branch diff...")
    diff_content = get_branch_diff(
        project_dir, base_branch=base_branch, exclude_paths=["pr_info/"]
    )

    if not diff_content or not diff_content.strip():
        logger.warning("No diff content found, using fallback PR summary")
        return "Pull Request", "Pull Request"

    # Load prompt template
    logger.info("Loading PR summary prompt template...")
    try:
        prompt_template = get_prompt(str(PROMPTS_FILE_PATH), "PR Summary Generation")
    except (FileNotFoundError, ValueError) as e:
        logger.error(
            f"Critical error: Cannot load prompt 'PR Summary Generation' from {PROMPTS_FILE_PATH}: {e}"
        )
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Unexpected error loading prompt 'PR Summary Generation': {e}")
        raise

    # Generate summary
    full_prompt = prompt_template.replace("[git_diff_content]", diff_content)

    logger.info(f"Calling LLM for PR summary using provider={provider}...")
    try:
        branch_name = get_branch_name_for_logging(project_dir)
        env_vars = prepare_llm_environment(project_dir)
        llm_response = prompt_llm(
            full_prompt,
            provider=provider,
            # Inactivity budget (was wall-clock), kept below the CI step cap.
            timeout=300,
            env_vars=env_vars,
            project_dir=str(project_dir),
            mcp_config=mcp_config,
            settings_file=settings_file,
            branch_name=branch_name,
        )["text"]

        if not llm_response or not llm_response.strip():
            logger.error(
                "LLM returned empty response - cannot generate meaningful PR summary"
            )
            logger.error("This indicates a configuration issue with the LLM provider.")
            raise ValueError("LLM returned empty response")

        title, body = parse_pr_summary(llm_response)
        logger.info("PR summary generated successfully")
        return title, body

    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Critical error: LLM API failed: {e}")
        logger.error("Cannot generate PR summary without working LLM connection.")
        logger.error("Please fix LLM configuration before creating PR.")
        raise


def cleanup_repository(project_dir: Path) -> bool:
    """Clean up repository by deleting pr_info/ directory and profiler output.

    Args:
        project_dir: Path to project directory

    Returns:
        True if all cleanup operations succeed, False otherwise
    """
    logger.info("Cleaning up repository...")
    success = True

    # Delete entire pr_info/ directory
    logger.info("Deleting pr_info/ directory...")
    if not delete_pr_info_directory(project_dir):
        logger.error("Failed to delete pr_info directory")
        success = False

    # Clean profiler output (outside pr_info/)
    logger.info("Cleaning profiler output files...")
    if not clean_profiler_output(project_dir):
        logger.error("Failed to clean profiler output")
        success = False

    if success:
        logger.info("Repository cleanup completed successfully")
    else:
        logger.error("Repository cleanup completed with errors")

    return success


def create_pull_request(
    project_dir: Path, title: str, body: str
) -> tuple[PullRequestData | None, str | None]:
    """Create GitHub pull request using PullRequestManager.

    Args:
        project_dir: Path to project directory
        title: PR title
        body: PR body/description

    Returns:
        Tuple of (PullRequestData dict, None) on success,
        (None, error_message) on failure.
    """
    logger.info("Creating GitHub pull request...")

    # Get current and base branches
    current_branch = get_current_branch_name(project_dir)
    if current_branch is None:
        logger.error("Could not determine current branch")
        return None, "Could not determine current branch"

    base_branch = detect_base_branch(project_dir, current_branch=current_branch)
    if base_branch is None:
        logger.error(
            "Could not detect base branch for PR creation.\n"
            "Tip: Add '### Base Branch' section to your GitHub issue."
        )
        return None, "Could not detect base branch for PR creation"

    missing_err = check_base_branch_on_origin(project_dir, base_branch)
    if missing_err:
        logger.error(missing_err)
        return None, missing_err

    try:
        # Create PR using PullRequestManager
        pr_manager = PullRequestManager(project_dir)
        pr_result = pr_manager.create_pull_request(
            title=title,
            head_branch=current_branch,
            base_branch=base_branch,
            body=body,
        )

        return pr_result, None

    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error creating pull request: {e}")
        return None, f"Error creating pull request: {e}"


def validate_branch_issue_linkage(project_dir: Path) -> int | None:
    """Validate current branch is linked to an issue.

    "Linked" means the branch is a linked branch of the issue, or the head
    of an open PR that closes the issue.

    Args:
        project_dir: Path to the project directory

    Returns:
        Issue number if branch is linked, None otherwise (not linked,
        lookup failed, or an error occurred)
    """
    try:
        # 1. Get current branch name
        branch_name = get_current_branch_name(project_dir)
        if not branch_name:
            logger.warning("Could not determine current branch name")
            return None

        # 2. Extract issue number from branch name
        issue_number = extract_issue_number_from_branch(branch_name)
        if issue_number is None:
            logger.warning(
                f"Branch name '{branch_name}' does not start with issue number"
            )
            return None

        # 3. Check linked branches and open closing PRs (helper logs outcome)
        branch_manager = IssueBranchManager(project_dir=project_dir)
        if is_branch_linked_to_issue(branch_manager, issue_number, branch_name):
            return issue_number
        return None

    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error validating branch-issue linkage: {e}")
        return None


# Backward-compatible alias for a function moved to the helpers module.
# Tests patch this name at "mcp_coder.workflows.create_pr.core.*",
# so keeping it in this module's namespace is required.
_handle_create_pr_failure = _handle_create_pr_failure_impl


def _add_pr_assignee_best_effort(project_dir: Path, pr_number: int) -> None:
    """Assign the PR to the authenticated user on the auto-review path only.

    No-op when auto_review_implementation is off for the repo. Best-effort:
    logs a warning on failure, never raises.

    Args:
        project_dir: Path to the project directory (git remote → repo config).
        pr_number: Number of the freshly created pull request.
    """
    if not get_repo_flag(project_dir, "auto_review_implementation"):
        return

    try:
        username = get_authenticated_username()
        PullRequestManager(project_dir).add_assignees(pr_number, username)
        logger.log(OUTPUT, "Assigned PR #%s to %s", pr_number, username)
    except Exception as e:  # pylint: disable=broad-exception-caught  # best-effort; never fail the workflow
        logger.warning("assignee-add failed (non-blocking): %s", e)


def _cleanup_commit_push(project_dir: Path) -> tuple[str, str] | None:
    """Clean up pr_info/ and profiler output, commit, push.

    Args:
        project_dir: Path to the project directory.

    Returns:
        None on success, else (stage, message) for _handle_create_pr_failure.
    """
    # Step 3: Clean up repository
    logger.log(OUTPUT, "Step 3/5: Cleaning up repository...")
    if not cleanup_repository(project_dir):
        logger.error("Repository cleanup failed")
        return "cleanup", "Repository cleanup failed"

    # Check if there are changes to commit
    if not is_working_directory_clean(
        project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
    ):
        # Commit cleanup changes
        logger.log(OUTPUT, "Committing cleanup changes...")
        commit_result = commit_all_changes(
            "chore: clean up build artifacts", project_dir
        )

        if not commit_result["success"]:
            # Ignore "No staged files" - this is expected when cleanup had no effect
            error_msg = commit_result.get("error") or ""
            if "No staged files" not in error_msg:
                logger.error(
                    f"Failed to commit cleanup changes: {commit_result['error']}"
                )
                return "cleanup", f"Failed to commit cleanup: {commit_result['error']}"
            logger.log(
                OUTPUT, "No cleanup changes to commit (files were already clean)"
            )
        else:
            logger.log(OUTPUT, "Cleanup committed: %s", commit_result["commit_hash"])
    else:
        logger.log(OUTPUT, "No cleanup changes to commit")

    # Step 4: Push commits
    logger.log(OUTPUT, "Step 4/5: Pushing commits...")
    push_result = git_push(project_dir)
    if not push_result["success"]:
        logger.error(f"Failed to push commits: {push_result['error']}")
        return "push", push_result.get("error", "Unknown push error")
    logger.log(OUTPUT, "Commits pushed successfully")
    return None


def _resolve_issue_from_pr(project_dir: Path, pr_number: int) -> int | None:
    """Closing-references fallback: first issue the PR closes, or None. Never raises.

    Args:
        project_dir: Path to the project directory.
        pr_number: Number of the pull request to query.

    Returns:
        The first closing issue number, or None if none found or lookup failed.
    """
    logger.info("Attempting fallback: querying PR closing issues references...")
    try:
        pr_mgr = PullRequestManager(project_dir)
        closing_issues = pr_mgr.get_closing_issue_numbers(pr_number)
        if len(closing_issues) == 1:
            logger.info("Fallback found closing issue #%s from PR", closing_issues[0])
            return closing_issues[0]
        if len(closing_issues) > 1:
            logger.warning(
                "Multiple closing issues found: %s, using first (#%s)",
                closing_issues,
                closing_issues[0],
            )
            return closing_issues[0]
        logger.debug("No closing issues found for PR #%s", pr_number)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to query closing issues (non-blocking): %s", e)
    return None


def run_create_pr_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
) -> int:
    """Main workflow orchestration function - creates PR and cleans up repository.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional path to MCP configuration file
        settings_file: Optional path to .claude/settings.local.json; forwarded to prompt_llm.
        update_issue_labels: If True, update GitHub issue labels on success
        post_issue_comments: If True, post comments on the issue on failure

    Returns:
        int: Exit code. 0 once the PR exists and every phase B outcome was
        handled (final label pr_created / pr_merge_conflict / failing_ci,
        i.e. 10 / 74 / 81); 1 when phase A fails or either phase crashes.

    Note:
        The workflow runs as two phases, each wrapped in :func:`run_guarded`.
        Phase A (prerequisites → PR creation) nets SIGTERM / unexpected exits
        into the general ``pr_creating_failed`` label. Deliberate failure
        sites still call :func:`_handle_create_pr_failure` and ``return 1``;
        the summary-generation catch classifies the LLM failure into
        ``pr_creating_timeout`` / ``pr_creating_mcp`` / ``pr_creating_failed``.
        Phase B (mergeability check, CI wait, final label) always runs once
        the PR exists, also with ``update_issue_labels=False``; a crash there
        posts a crash comment and sets ``pr_created``.
    """
    logger.log(OUTPUT, "Starting create PR workflow...")
    logger.log(OUTPUT, "Using project directory: %s", project_dir)

    start_time = time.time()

    # Branch-issue linkage, used for the PR body's closing reference and for
    # the final label. It usually still resolves after PR creation (via open
    # closing PRs). It is None only when the branch lacks the issue prefix,
    # the PR has no closing reference, or the lookup fails; phase A's
    # closing-references fallback covers the first case.
    cached_issue_number: int | None = validate_branch_issue_linkage(project_dir)
    if cached_issue_number:
        logger.log(OUTPUT, "Branch linked to issue #%s", cached_issue_number)
    else:
        logger.warning("Branch not linked to any issue")

    def phase_a() -> int:
        nonlocal cached_issue_number

        # Step 1: Check prerequisites
        logger.log(OUTPUT, "Step 1/5: Checking prerequisites...")
        if not check_prerequisites(project_dir):
            logger.error("Prerequisites check failed")
            elapsed = time.time() - start_time
            _handle_create_pr_failure(
                stage="prerequisites",
                message="Prerequisites check failed",
                project_dir=project_dir,
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
                elapsed_time=elapsed,
                issue_number=cached_issue_number,
            )
            return 1

        # Rebase onto the base branch when behind (never fails the workflow)
        _rebase_if_needed(project_dir)

        # Step 2: Generate PR summary
        logger.log(OUTPUT, "Step 2/5: Generating PR summary...")
        try:
            title, body = generate_pr_summary(
                project_dir, provider, mcp_config, settings_file
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Failed to generate PR summary: {e}")
            elapsed = time.time() - start_time
            reason = llm_failure_reason(e) or "general"
            category = {
                "timeout": "pr_creating_timeout",
                "mcp_unavailable": "pr_creating_mcp",
            }.get(reason, "pr_creating_failed")
            message = (
                format_mcp_unavailable_message(e)
                if isinstance(e, McpServersUnavailableError)
                else str(e)
            )
            _handle_create_pr_failure(
                stage="summary_generation",
                message=message,
                project_dir=project_dir,
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
                elapsed_time=elapsed,
                issue_number=cached_issue_number,
                category=category,
            )
            return 1

        # Steps 3-4: Clean up repository, commit, push
        failure = _cleanup_commit_push(project_dir)
        if failure:
            stage, message = failure
            elapsed = time.time() - start_time
            _handle_create_pr_failure(
                stage=stage,
                message=message,
                project_dir=project_dir,
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
                elapsed_time=elapsed,
                issue_number=cached_issue_number,
            )
            return 1

        # Step 5: Create pull request
        logger.log(OUTPUT, "Step 5/5: Creating pull request...")
        if cached_issue_number:
            body = ensure_closing_reference(body, cached_issue_number)
        pr_result, pr_error = create_pull_request(project_dir, title, body)
        if not pr_result:
            error_msg = pr_error or "Failed to create pull request"
            logger.error(error_msg)
            elapsed = time.time() - start_time
            _handle_create_pr_failure(
                stage="pr_creation",
                message=error_msg,
                project_dir=project_dir,
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
                elapsed_time=elapsed,
                issue_number=cached_issue_number,
            )
            return 1

        pr_number = pr_result["number"]
        pr_url = pr_result.get("url", "")
        pr_title = title
        current_branch = get_current_branch_name(project_dir)
        base_branch = detect_base_branch(project_dir, current_branch=current_branch)
        logger.log(OUTPUT, "PR Number: #%s", pr_number)
        logger.log(OUTPUT, "PR URL: %s", pr_url)
        logger.log(OUTPUT, "PR Title: %s", pr_title)
        logger.log(OUTPUT, "Base Branch: %s", base_branch)
        logger.log(OUTPUT, "Head Branch: %s", current_branch)

        # Auto-review path only: assign the PR to the authenticated user
        # (best-effort — never fails the workflow or flips a label).
        _add_pr_assignee_best_effort(project_dir, pr_number)

        # Fallback: query closingIssuesReferences if no issue found from branch
        if update_issue_labels and cached_issue_number is None:
            cached_issue_number = _resolve_issue_from_pr(project_dir, pr_number)
        return 0

    def phase_b() -> int:
        branch = get_current_branch_name(project_dir)
        if branch is None:
            logger.error("Could not determine current branch; skipping PR checks")
            label = "pr_created"
        else:
            label = run_post_creation(project_dir, branch)

        if update_issue_labels and cached_issue_number:
            logger.log(OUTPUT, "Updating GitHub issue label...")
            try:
                success = update_workflow_label(
                    IssueManager(project_dir),
                    from_label_id="pr_creating",
                    to_label_id=label,
                    validated_issue_number=cached_issue_number,
                )
                if success:
                    logger.log(OUTPUT, "✓ Issue label updated: pr_creating → %s", label)
                else:
                    logger.warning("✗ Failed to update issue label (non-blocking)")
            except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
                logger.error(f"Error updating issue label (non-blocking): {e}")
        else:
            if update_issue_labels:
                logger.warning(
                    "Skipping label update: branch was not linked to an issue"
                )
            logger.log(OUTPUT, "Post-creation outcome: %s (label not updated)", label)

        if update_issue_labels and cached_issue_number is None:
            logger.log(OUTPUT, "Create PR workflow completed with warnings")
        else:
            logger.log(OUTPUT, "Create PR workflow completed successfully!")
        return 0

    rc = run_guarded(
        phase_a,
        project_dir=project_dir,
        from_label_id="pr_creating",
        general_category="pr_creating_failed",
        workflow_title="PR Creation",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
        issue_number=cached_issue_number,
    )
    if rc != 0:
        return rc
    # Read after phase A, so an issue found by the closing-references fallback is used.
    return run_guarded(
        phase_b,
        project_dir=project_dir,
        from_label_id="pr_creating",
        general_category="pr_created",
        workflow_title="PR Creation",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
        issue_number=cached_issue_number,
    )
