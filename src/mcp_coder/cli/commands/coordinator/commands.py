"""CLI command handlers for coordinator package.

Provides two main commands:
- coordinator test: Trigger Jenkins integration tests for repositories
- coordinator run: Monitor GitHub issues and dispatch workflows based on labels

The coordinator run command automates the issue → plan → implement → PR pipeline
by filtering eligible issues and triggering appropriate Jenkins workflows.
"""

import argparse
import logging
import sys
from typing import Any, List, Optional

from ....utils.github_operations.github_utils import RepoIdentifier
from ....utils.github_operations.issue_branch_manager import IssueBranchManager
from ....utils.github_operations.issue_cache import (
    get_all_cached_issues,
    update_issue_labels_in_cache,
)
from ....utils.github_operations.issue_manager import IssueData, IssueManager
from ....utils.jenkins_operations.client import JenkinsClient
from ....utils.user_config import (
    create_default_config,
    get_cache_refresh_minutes,
    get_config_file_path,
    load_config,
)

# VSCodeClaude imports - now from workflows layer
from ....workflows.vscodeclaude import (
    VSCodeClaudeConfig,
    VSCodeClaudeSession,
    cleanup_stale_sessions,
    get_active_session_count,
    get_linked_branch_for_issue,
    load_repo_vscodeclaude_config,
    load_sessions,
    load_vscodeclaude_config,
    prepare_and_launch_session,
    process_eligible_issues,
    restart_closed_sessions,
)
from .command_templates import TEST_COMMAND_TEMPLATES
from .core import (
    dispatch_workflow,
    get_cached_eligible_issues,
    get_eligible_issues,
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
)
from .workflow_constants import WORKFLOW_MAPPING

__all__ = [
    "execute_coordinator_test",
    "execute_coordinator_run",
    "execute_coordinator_vscodeclaude",
    "execute_coordinator_vscodeclaude_status",
    "format_job_output",
]


logger = logging.getLogger(__name__)


def format_job_output(job_path: str, queue_id: int, url: Optional[str]) -> str:
    """Format job trigger output message.

    Args:
        job_path: Jenkins job path
        queue_id: Queue ID from Jenkins
        url: Job URL if available (may be None if not started yet)

    Returns:
        Formatted output string
    """
    output = f"Job triggered: {job_path} - test - queue: {queue_id}"

    if url:
        output += f"\n{url}"
    else:
        # Construct fallback message when job URL not available yet
        output += "\n(Job URL will be available once build starts)"

    return output


def execute_coordinator_test(args: argparse.Namespace) -> int:
    """Execute coordinator test command.

    Args:
        args: Parsed command line arguments with:
            - repo_name: Repository name to test
            - branch_name: Git branch to test

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        # Auto-create config on first run
        created = create_default_config()
        if created:
            config_path = get_config_file_path()
            logger.info(
                "Created default config file. Please update with your credentials."
            )
            print(f"Created default config file at {config_path}")
            print("Please update it with your Jenkins and repository information.")
            return 1  # Exit to let user configure

        # Load and validate repository config
        repo_config = load_repo_config(args.repo_name)
        validate_repo_config(args.repo_name, repo_config)

        # Type narrowing: validate_repo_config raises if any fields are None
        # Assert to help mypy understand the values are non-None after validation
        assert repo_config["repo_url"] is not None
        assert repo_config["executor_job_path"] is not None
        assert repo_config["github_credentials_id"] is not None
        validated_config: dict[str, str] = {
            "repo_url": repo_config["repo_url"],
            "executor_job_path": repo_config["executor_job_path"],
            "github_credentials_id": repo_config["github_credentials_id"],
        }

        # Get Jenkins credentials
        server_url, username, api_token = get_jenkins_credentials()

        # Create Jenkins client
        client = JenkinsClient(server_url, username, api_token)

        # Select template based on OS using dictionary mapping
        # executor_os is guaranteed to be non-None and one of {"windows", "linux"} after validation
        assert repo_config["executor_os"] is not None
        executor_os: str = repo_config["executor_os"]
        test_command = TEST_COMMAND_TEMPLATES[executor_os].format(
            log_level=args.log_level
        )

        # Build job parameters
        params = {
            "REPO_URL": validated_config["repo_url"],
            "BRANCH_NAME": args.branch_name,
            "COMMAND": test_command,  # OS-aware selection
            "GITHUB_CREDENTIALS_ID": validated_config["github_credentials_id"],
        }

        # Start job (API token in Basic Auth bypasses CSRF)
        queue_id = client.start_job(validated_config["executor_job_path"], params)

        # Try to get job URL (may not be available immediately)
        try:
            status = client.get_job_status(queue_id)
            job_url = status.url
        except Exception as e:
            logger.debug(f"Could not get job status: {e}")
            job_url = None

        # Format and print output
        output = format_job_output(
            validated_config["executor_job_path"], queue_id, job_url
        )
        print(output)

        return 0

    except ValueError as e:
        # User-facing errors (config issues) - print only, no logging
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        # Let all other exceptions bubble up with full traceback
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise


def execute_coordinator_run(args: argparse.Namespace) -> int:
    """Execute coordinator run command.

    Args:
        args: Parsed command line arguments with:
            - all: Process all repositories (bool)
            - repo: Single repository name (str, optional)
            - log_level: Logging level (str)

    Returns:
        int: Exit code (0 for success, 1 for error)

    Raises:
        Exception: Any unexpected errors (not caught, let bubble up)
    """
    try:
        # Step 1: Auto-create config on first run
        created = create_default_config()
        if created:
            config_path = get_config_file_path()
            logger.info(
                "Created default config file. Please update with your credentials."
            )
            print(f"Created default config file at {config_path}")
            print("Please update it with your Jenkins and repository information.")
            return 1  # Exit to let user configure

        # Step 2: Determine repository list
        if args.repo:
            # Single repository mode
            repo_names = [args.repo]
        elif args.all:
            # All repositories mode - extract from config
            config_data = load_config()

            repos_section = config_data.get("coordinator", {}).get("repos", {})
            repo_names = list(repos_section.keys())

            if not repo_names:
                print("No repositories configured in config file", file=sys.stderr)
                logger.warning("No repositories found in config")
                return 1
        else:
            # Should not reach here due to argparse mutually exclusive group
            print("Error: Either --all or --repo must be specified", file=sys.stderr)
            return 1

        # Step 3: Get Jenkins credentials (shared across all repos)
        server_url, username, api_token = get_jenkins_credentials()
        jenkins_client = JenkinsClient(server_url, username, api_token)

        # Step 4: Process each repository
        for repo_name in repo_names:
            # Step 4a: Load and validate repo config
            repo_config = load_repo_config(repo_name)
            validate_repo_config(repo_name, repo_config)

            # Log repository header with URL
            repo_url = repo_config["repo_url"]
            logger.info(f"{'='*80}")
            logger.info(f"Processing repository: {repo_url}")
            logger.info(f"{'='*80}")

            # Type narrowing: validate_repo_config raises if any fields are None
            # Assert to help mypy understand the values are non-None after validation
            assert repo_config["repo_url"] is not None
            assert repo_config["executor_job_path"] is not None
            assert repo_config["github_credentials_id"] is not None
            validated_config: dict[str, str] = {
                "repo_url": repo_config["repo_url"],
                "executor_job_path": repo_config["executor_job_path"],
                "github_credentials_id": repo_config["github_credentials_id"],
                "executor_os": repo_config.get("executor_os") or "linux",
            }

            # Step 4b: Create managers
            issue_manager = IssueManager(repo_url=validated_config["repo_url"])
            branch_manager = IssueBranchManager(repo_url=validated_config["repo_url"])

            # Step 4c: Get eligible issues using cache
            # Create RepoIdentifier from repo_url
            repo_url = validated_config["repo_url"]
            try:
                repo_identifier = RepoIdentifier.from_repo_url(repo_url)
                repo_full_name = repo_identifier.full_name
            except ValueError:
                # Fallback: use repo_name if URL format is unexpected
                repo_full_name = repo_name

            try:
                eligible_issues = get_cached_eligible_issues(
                    repo_full_name=repo_full_name,
                    issue_manager=issue_manager,
                    force_refresh=args.force_refresh,
                    cache_refresh_minutes=get_cache_refresh_minutes(),
                )
            except Exception as e:
                logger.warning(
                    f"Cache failed for {repo_full_name}: {e}, using direct fetch"
                )
                eligible_issues = get_eligible_issues(issue_manager)

            logger.info(f"Found {len(eligible_issues)} eligible issues")

            # Skip if no eligible issues or duplicate protection triggered
            if not eligible_issues:
                logger.info(f"No eligible issues for {repo_name}")
                continue

            # Step 4d: Dispatch workflows for each eligible issue (fail-fast)
            for issue in eligible_issues:
                # Find current bot_pickup label to determine workflow
                current_label = None
                for label in issue["labels"]:
                    if label in WORKFLOW_MAPPING:
                        current_label = label
                        break

                if not current_label:
                    logger.error(
                        f"Issue #{issue['number']} has no workflow label, skipping"
                    )
                    continue

                workflow_config = WORKFLOW_MAPPING[current_label]
                workflow_name = workflow_config["workflow"]

                try:
                    dispatch_workflow(
                        issue=issue,
                        workflow_name=workflow_name,
                        repo_config=validated_config,
                        jenkins_client=jenkins_client,
                        issue_manager=issue_manager,
                        branch_manager=branch_manager,
                        log_level=args.log_level,
                    )

                    # Update cache with new labels immediately after successful dispatch
                    try:
                        update_issue_labels_in_cache(
                            repo_full_name=repo_full_name,
                            issue_number=issue["number"],
                            old_label=current_label,
                            new_label=workflow_config["next_label"],
                        )
                    except Exception as cache_error:
                        logger.warning(
                            f"Cache update failed for issue #{issue['number']}: {cache_error}"
                        )

                except Exception as e:
                    # Fail-fast: log error and exit immediately
                    logger.error(
                        f"Failed processing issue #{issue['number']}: {e}",
                        exc_info=True,
                    )
                    print(
                        f"Error: Failed to process issue #{issue['number']}: {e}",
                        file=sys.stderr,
                    )
                    return 1

            logger.info(f"Successfully processed all issues in {repo_name}")

        # Step 5: Success - all repos processed
        return 0

    except ValueError as e:
        # User-facing errors (config issues) - print only, no logging
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        # Let all other exceptions bubble up with full traceback
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise


def _get_repo_full_name_from_url(repo_url: str) -> str:
    """Extract full repo name (owner/repo) from repo URL.

    Args:
        repo_url: Repository URL like https://github.com/owner/repo.git

    Returns:
        Full repo name like "owner/repo"
    """
    try:
        repo_identifier = RepoIdentifier.from_repo_url(repo_url)
        return repo_identifier.full_name
    except ValueError:
        # Fallback: extract from URL directly
        url_clean = repo_url.rstrip("/")
        if url_clean.endswith(".git"):
            url_clean = url_clean[:-4]
        parts = url_clean.split("/")
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
        return ""


def _build_cached_issues_by_repo(
    repo_names: list[str],
) -> dict[str, dict[int, IssueData]]:
    """Build cached issues dict for all configured repos.

    Args:
        repo_names: List of repository config names

    Returns:
        Dict mapping repo_full_name to {issue_number: IssueData}
    """
    cached_issues_by_repo: dict[str, dict[int, IssueData]] = {}

    for repo_name in repo_names:
        try:
            repo_config: dict[str, Any] = load_repo_config(repo_name)
            repo_url = repo_config.get("repo_url", "")
            if not repo_url:
                continue

            repo_full_name = _get_repo_full_name_from_url(repo_url)
            if not repo_full_name:
                continue

            # Create issue manager and fetch cached issues
            issue_manager_instance: IssueManager = IssueManager(repo_url=repo_url)
            all_issues = get_all_cached_issues(
                repo_full_name=repo_full_name,
                issue_manager=issue_manager_instance,
                force_refresh=False,
                cache_refresh_minutes=get_cache_refresh_minutes(),
            )

            # Build issues_by_number dict
            issues_by_number: dict[int, IssueData] = {
                issue["number"]: issue for issue in all_issues
            }
            cached_issues_by_repo[repo_full_name] = issues_by_number

        except Exception as e:
            logger.warning(f"Failed to build cache for {repo_name}: {e}")

    return cached_issues_by_repo


def execute_coordinator_vscodeclaude(args: argparse.Namespace) -> int:
    """Execute coordinator vscodeclaude command.

    Args:
        args: Parsed arguments with:
            - repo: Optional repository filter
            - max_sessions: Optional max sessions override
            - cleanup: Whether to delete stale folders
            - intervene: Intervention mode flag
            - issue: Issue number for intervention

    Returns:
        Exit code (0 success, 1 error)
    """
    try:
        # Auto-create config if needed
        created = create_default_config()
        if created:
            config_path = get_config_file_path()
            print(f"Created default config at {config_path}")
            print("Please configure [coordinator.vscodeclaude] section.")
            return 1

        # Load vscodeclaude config
        vscodeclaude_config = load_vscodeclaude_config()

        # Handle intervention mode
        if args.intervene:
            if not args.issue:
                print("Error: --intervene requires --issue NUMBER", file=sys.stderr)
                return 1
            return _handle_intervention_mode(args, vscodeclaude_config)

        # Determine max sessions
        max_sessions = args.max_sessions or vscodeclaude_config["max_sessions"]

        # Get repo list for cache building
        config_data = load_config()
        repos_section = config_data.get("coordinator", {}).get("repos", {})
        repo_names = list(repos_section.keys())

        # Build cached issues for all repos (used for staleness checks)
        cached_issues_by_repo = _build_cached_issues_by_repo(repo_names)

        # Step 1: Handle cleanup (BEFORE restart)
        # - Always runs: dry_run=True shows what would be cleaned, dry_run=False actually deletes
        # - This ensures users always see what's cleanable
        if args.cleanup:
            cleanup_stale_sessions(
                dry_run=False, cached_issues_by_repo=cached_issues_by_repo
            )
        else:
            cleanup_stale_sessions(
                dry_run=True, cached_issues_by_repo=cached_issues_by_repo
            )

        # Step 2: Restart closed sessions (pass cache for staleness checks)
        restarted = restart_closed_sessions(cached_issues_by_repo=cached_issues_by_repo)
        for session in restarted:
            repo_short = session["repo"].split("/")[-1]
            print(
                f"Restarted: {repo_short} #{session['issue_number']} "
                f"({session['status']}) PID:{session['vscode_pid']}"
            )

        # Step 3: Check repo list (already loaded above)
        if not repo_names:
            print("No repositories configured in config file", file=sys.stderr)
            return 1

        # Step 4: Process each repository
        total_started: List[VSCodeClaudeSession] = []
        for repo_name in repo_names:
            # Apply repo filter if specified
            if args.repo and repo_name != args.repo:
                continue

            repo_config = load_repo_config(repo_name)

            # Build validated config dict - use empty string fallback for optional repo_url
            validated_config: dict[str, str] = {
                "repo_url": repo_config.get("repo_url") or "",
            }

            started = process_eligible_issues(
                repo_name=repo_name,
                repo_config=validated_config,
                vscodeclaude_config=vscodeclaude_config,
                max_sessions=max_sessions,
                repo_filter=args.repo,
            )
            total_started.extend(started)

        # Print summary
        if total_started:
            print(f"\nStarted {len(total_started)} new session(s):")
            for session in total_started:
                repo_short = session["repo"].split("/")[-1]
                print(
                    f"  {repo_short} - #{session['issue_number']}: {session['status']}"
                )
        else:
            current = get_active_session_count()
            print(f"\nNo new sessions started (active: {current}/{max_sessions})")

        return 0

    except ValueError as e:
        # User-facing errors (config issues) - print only, no logging
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        # Let all other exceptions bubble up with full traceback
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise


def execute_coordinator_vscodeclaude_status(args: argparse.Namespace) -> int:
    """Execute coordinator vscodeclaude status command.

    Args:
        args: Parsed arguments with:
            - repo: Optional repository filter

    Returns:
        Exit code (0 success)
    """
    from pathlib import Path

    from tabulate import tabulate

    from ....workflows.vscodeclaude import (
        check_folder_dirty,
        check_vscode_running,
        clear_vscode_window_cache,
        is_vscode_window_open_for_folder,
    )

    # Refresh window cache once for all sessions
    clear_vscode_window_cache()

    # Load sessions
    store = load_sessions()
    sessions = store["sessions"]

    # Apply repo filter if specified
    if args.repo:
        sessions = [s for s in sessions if args.repo in s["repo"]]

    if not sessions:
        print("No active sessions")
        return 0

    # Build table data
    table_data = []
    for session in sessions:
        issue_num = f"#{session['issue_number']}"
        repo_short = session["repo"].split("/")[-1]
        # Shorten status (remove "status-" prefix)
        status_raw = session["status"]
        status = status_raw.replace("status-", "") if status_raw else ""

        # Check if VSCode is running: window title check (reliable) or PID check (fallback)
        is_running = is_vscode_window_open_for_folder(
            session["folder"],
            issue_number=session["issue_number"],
            repo=session["repo"],
        ) or check_vscode_running(session.get("vscode_pid"))
        vscode_status = "Running" if is_running else "Closed"

        # Check for uncommitted changes
        folder_path = Path(session["folder"])
        if folder_path.exists():
            is_dirty = check_folder_dirty(folder_path)
            changes = "Dirty" if is_dirty else "Clean"
        else:
            changes = "-"

        # Determine next action
        if is_running:
            next_action = "(active)"
        elif not folder_path.exists():
            next_action = "-> Remove"
        elif is_dirty:
            next_action = "!! Manual"
        else:
            next_action = "-> Restart"

        # Add intervention marker
        if session.get("is_intervention"):
            issue_num = f"{issue_num} [I]"

        table_data.append(
            [issue_num, repo_short, status, vscode_status, changes, next_action]
        )

    # Print table
    headers = ["Issue", "Repo", "Status", "VSCode", "Changes", "Next Action"]
    print(tabulate(table_data, headers=headers, tablefmt="simple"))

    return 0


def _handle_intervention_mode(
    args: argparse.Namespace,
    vscodeclaude_config: VSCodeClaudeConfig,
) -> int:
    """Handle intervention mode for vscodeclaude.

    Args:
        args: Parsed arguments with issue number
        vscodeclaude_config: VSCodeClaude config

    Returns:
        Exit code (0 success, 1 error)
    """
    # Get the repo (required for intervention)
    if not args.repo:
        print("Error: --intervene requires --repo NAME", file=sys.stderr)
        return 1

    # Load repo config
    repo_config = load_repo_config(args.repo)
    validated_config: dict[str, str] = {
        "repo_url": repo_config.get("repo_url") or "",
    }

    # Create issue manager to get issue data
    repo_url = validated_config["repo_url"]
    issue_manager = IssueManager(repo_url=repo_url)
    branch_manager = IssueBranchManager(repo_url=repo_url)

    # Get issue
    issue = issue_manager.get_issue(args.issue)
    if issue["number"] == 0:
        print(f"Error: Issue #{args.issue} not found", file=sys.stderr)
        return 1

    # Get linked branch
    branch_name = get_linked_branch_for_issue(branch_manager, args.issue)

    # Load repo vscodeclaude config
    repo_vscodeclaude_config = load_repo_vscodeclaude_config(args.repo)

    # Print warning
    print("\n" + "!" * 60)
    print("INTERVENTION MODE - Automation disabled")
    print("!" * 60)
    print(f"Issue: #{args.issue}")
    print(f"Branch: {branch_name or 'main'}")
    print("!" * 60 + "\n")

    # Prepare and launch session
    session = prepare_and_launch_session(
        issue=issue,
        repo_config=validated_config,
        vscodeclaude_config=vscodeclaude_config,
        repo_vscodeclaude_config=repo_vscodeclaude_config,
        branch_name=branch_name,
        is_intervention=True,
    )

    print(f"Started intervention session: #{session['issue_number']}")
    return 0
