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

# Lazy imports from coordinator package to enable test patching
# Tests can patch at 'mcp_coder.cli.commands.coordinator.<name>'
from typing import List, Optional

from ....utils.github_operations.github_utils import RepoIdentifier
from ....utils.jenkins_operations.models import JobStatus
from ....utils.user_config import get_config_file_path, load_config
from .command_templates import TEST_COMMAND_TEMPLATES
from .core import _get_coordinator, validate_repo_config
from .vscodeclaude import (
    DEFAULT_MAX_SESSIONS,
    VSCodeClaudeSession,
    get_active_session_count,
    get_eligible_vscodeclaude_issues,
    get_github_username,
    get_linked_branch_for_issue,
    load_repo_vscodeclaude_config,
    load_sessions,
    load_vscodeclaude_config,
    prepare_and_launch_session,
    process_eligible_issues,
    restart_closed_sessions,
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
        # Get coordinator for patchable function access
        coordinator = _get_coordinator()

        # Auto-create config on first run
        created = coordinator.create_default_config()
        if created:
            config_path = get_config_file_path()
            logger.info(
                "Created default config file. Please update with your credentials."
            )
            print(f"Created default config file at {config_path}")
            print("Please update it with your Jenkins and repository information.")
            return 1  # Exit to let user configure

        # Load and validate repository config
        repo_config = coordinator.load_repo_config(args.repo_name)
        validate_repo_config(args.repo_name, repo_config)

        # Type narrowing: validate_repo_config raises if any fields are None
        # After validation, we can safely cast to non-optional dict
        validated_config: dict[str, str] = {
            "repo_url": repo_config["repo_url"],
            "executor_job_path": repo_config["executor_job_path"],
            "github_credentials_id": repo_config["github_credentials_id"],
        }

        # Get Jenkins credentials
        server_url, username, api_token = coordinator.get_jenkins_credentials()

        # Create Jenkins client
        client = coordinator.JenkinsClient(server_url, username, api_token)

        # Select template based on OS using dictionary mapping
        # executor_os is guaranteed to be non-None and one of {"windows", "linux"} after validation
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
        # User-facing errors (config issues)
        print(f"Error: {e}", file=sys.stderr)
        logger.error(f"Configuration error: {e}")
        return 1

    except Exception as e:
        # Let all other exceptions bubble up with full traceback
        # (per issue spec: "Let exceptions bubble up naturally for debugging")
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
        # Get coordinator for patchable function access
        coordinator = _get_coordinator()

        # Step 1: Auto-create config on first run
        created = coordinator.create_default_config()
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
        server_url, username, api_token = coordinator.get_jenkins_credentials()
        jenkins_client = coordinator.JenkinsClient(server_url, username, api_token)

        # Step 4: Process each repository
        for repo_name in repo_names:
            # Step 4a: Load and validate repo config
            repo_config = coordinator.load_repo_config(repo_name)
            validate_repo_config(repo_name, repo_config)

            # Log repository header with URL
            repo_url = repo_config["repo_url"]
            logger.info(f"{'='*80}")
            logger.info(f"Processing repository: {repo_url}")
            logger.info(f"{'='*80}")

            # Type narrowing: validate_repo_config raises if any fields are None
            # Use .get() for executor_os with default to ensure backward compatibility
            validated_config: dict[str, str] = {
                "repo_url": repo_config["repo_url"],
                "executor_job_path": repo_config["executor_job_path"],
                "github_credentials_id": repo_config["github_credentials_id"],
                "executor_os": repo_config.get("executor_os", "linux"),
            }

            # Step 4b: Create managers
            issue_manager = coordinator.IssueManager(
                repo_url=validated_config["repo_url"]
            )
            branch_manager = coordinator.IssueBranchManager(
                repo_url=validated_config["repo_url"]
            )

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
                eligible_issues = coordinator.get_cached_eligible_issues(
                    repo_full_name=repo_full_name,
                    issue_manager=issue_manager,
                    force_refresh=args.force_refresh,
                    cache_refresh_minutes=coordinator.get_cache_refresh_minutes(),
                )
            except Exception as e:
                logger.warning(
                    f"Cache failed for {repo_full_name}: {e}, using direct fetch"
                )
                eligible_issues = coordinator.get_eligible_issues(issue_manager)

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
                    coordinator.dispatch_workflow(
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
                        coordinator._update_issue_labels_in_cache(
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
        # User-facing errors (config issues)
        print(f"Error: {e}", file=sys.stderr)
        logger.error(f"Configuration error: {e}")
        return 1

    except Exception as e:
        # Let all other exceptions bubble up with full traceback
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise


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
        coordinator = _get_coordinator()

        # Auto-create config if needed
        created = coordinator.create_default_config()
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

        # Step 1: Restart closed sessions
        restarted = restart_closed_sessions()
        for session in restarted:
            print(f"Restarted: #{session['issue_number']} ({session['status']})")

        # Step 2: Handle cleanup if requested
        if args.cleanup:
            _cleanup_stale_sessions(dry_run=False)
        else:
            # List stale sessions without deleting
            _cleanup_stale_sessions(dry_run=True)

        # Step 3: Get repo list
        config_data = load_config()
        repos_section = config_data.get("coordinator", {}).get("repos", {})
        repo_names = list(repos_section.keys())

        if not repo_names:
            print("No repositories configured in config file", file=sys.stderr)
            return 1

        # Step 4: Process each repository
        total_started: List[VSCodeClaudeSession] = []
        for repo_name in repo_names:
            # Apply repo filter if specified
            if args.repo and repo_name != args.repo:
                continue

            repo_config = coordinator.load_repo_config(repo_name)

            # Build validated config dict
            validated_config: dict[str, str] = {
                "repo_url": repo_config.get("repo_url", ""),
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
                print(f"  #{session['issue_number']}: {session['status']}")
        else:
            current = get_active_session_count()
            print(f"\nNo new sessions started (active: {current}/{max_sessions})")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        logger.error(f"Configuration error: {e}")
        return 1

    except Exception as e:
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
    # Load sessions
    store = load_sessions()
    sessions = store["sessions"]

    # Apply repo filter if specified
    if args.repo:
        sessions = [s for s in sessions if args.repo in s["repo"]]

    # Display header
    print("\n" + "=" * 70)
    print("VSCODECLAUDE SESSIONS")
    print("=" * 70)

    if not sessions:
        print("  No active sessions")
    else:
        # Display each session
        for session in sessions:
            issue_num = session["issue_number"]
            repo = session["repo"]
            status = session["status"]
            pid = session.get("vscode_pid", "N/A")
            intervention = " [INTERVENTION]" if session.get("is_intervention") else ""

            from .vscodeclaude import check_vscode_running

            running = "✓" if check_vscode_running(session.get("vscode_pid")) else "✗"

            print(f"  #{issue_num} ({repo}) - {status}{intervention}")
            print(f"    PID: {pid} [{running}] | Folder: {session['folder']}")

    print("=" * 70 + "\n")

    return 0


def _handle_intervention_mode(
    args: argparse.Namespace,
    vscodeclaude_config: dict[str, object],
) -> int:
    """Handle intervention mode for vscodeclaude.

    Args:
        args: Parsed arguments with issue number
        vscodeclaude_config: VSCodeClaude config

    Returns:
        Exit code (0 success, 1 error)
    """
    coordinator = _get_coordinator()

    # Get the repo (required for intervention)
    if not args.repo:
        print("Error: --intervene requires --repo NAME", file=sys.stderr)
        return 1

    # Load repo config
    repo_config = coordinator.load_repo_config(args.repo)
    validated_config: dict[str, str] = {
        "repo_url": repo_config.get("repo_url", ""),
    }

    # Create issue manager to get issue data
    repo_url = validated_config["repo_url"]
    issue_manager = coordinator.IssueManager(repo_url=repo_url)
    branch_manager = coordinator.IssueBranchManager(repo_url=repo_url)

    # Get issue
    issue = issue_manager.get_issue(args.issue)
    if not issue:
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
        vscodeclaude_config=vscodeclaude_config,  # type: ignore[arg-type]
        repo_vscodeclaude_config=repo_vscodeclaude_config,
        branch_name=branch_name,
        is_intervention=True,
    )

    print(f"Started intervention session: #{session['issue_number']}")
    return 0


def _cleanup_stale_sessions(dry_run: bool = True) -> None:
    """Clean up stale sessions (folders without running VSCode).

    Args:
        dry_run: If True, only list stale sessions without deleting
    """
    import shutil
    from pathlib import Path

    from .vscodeclaude import check_vscode_running, remove_session

    store = load_sessions()
    stale_sessions = []

    for session in store["sessions"]:
        if not check_vscode_running(session.get("vscode_pid")):
            folder_path = Path(session["folder"])
            if folder_path.exists():
                stale_sessions.append(session)

    if not stale_sessions:
        return

    print("\nStale sessions found:")
    for session in stale_sessions:
        print(f"  #{session['issue_number']}: {session['folder']}")

    if dry_run:
        print("\nUse --cleanup to delete these folders")
    else:
        for session in stale_sessions:
            folder_path = Path(session["folder"])
            try:
                shutil.rmtree(folder_path)
                remove_session(session["folder"])
                print(f"  Deleted: {session['folder']}")
            except Exception as e:
                logger.warning(f"Failed to delete {session['folder']}: {e}")
