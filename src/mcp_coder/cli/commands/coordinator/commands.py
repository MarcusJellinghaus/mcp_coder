"""CLI command handlers for coordinator package.

The coordinator command monitors GitHub issues and dispatches workflows based on
labels. Use --dry-run to trigger Jenkins integration tests instead.
"""

import argparse
import logging
from typing import Optional

from ....mcp_workspace_github import (
    IssueBranchManager,
    IssueManager,
    RepoIdentifier,
    update_issue_labels_in_cache,
)
from ....utils.jenkins_operations.client import JenkinsClient
from ....utils.log_utils import OUTPUT
from ....utils.user_config import (
    create_default_config,
    get_cache_refresh_minutes,
    get_config_file_path,
    load_config,
)
from ...utils import log_command_startup
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
                "Created default config file. Please update with your credentials.",
            )
            logger.log(OUTPUT, "Created default config file at %s", config_path)
            logger.log(
                OUTPUT, "Please update it with your Jenkins and repository information."
            )
            return 1  # Exit to let user configure

        # Load and validate repository config
        repo_config = load_repo_config(args.repo_name)
        validate_repo_config(args.repo_name, repo_config)

        # Type narrowing: validate_repo_config raises if any fields are None
        # Assert to help mypy understand the values are str after validation
        assert isinstance(repo_config["repo_url"], str)
        assert isinstance(repo_config["executor_job_path"], str)
        assert isinstance(repo_config["github_credentials_id"], str)
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
        assert isinstance(repo_config["executor_os"], str)
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
        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
            logger.debug(f"Could not get job status: {e}")
            job_url = None

        # Format and print output
        output = format_job_output(
            validated_config["executor_job_path"], queue_id, job_url
        )
        logger.log(OUTPUT, "%s", output)

        return 0

    except ValueError as e:
        logger.error("%s", e)
        return 1

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
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

    """
    try:
        log_command_startup("coordinator run")

        # Step 1: Auto-create config on first run
        created = create_default_config()
        if created:
            config_path = get_config_file_path()
            logger.info(
                "Created default config file. Please update with your credentials.",
            )
            logger.log(OUTPUT, "Created default config file at %s", config_path)
            logger.log(
                OUTPUT, "Please update it with your Jenkins and repository information."
            )
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
                logger.error("No repositories configured in config file")
                return 1
        else:
            # Should not reach here due to argparse mutually exclusive group
            logger.error("Either --all or --repo must be specified")
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
            # Assert to help mypy understand the values are str after validation
            assert isinstance(repo_config["repo_url"], str)
            assert isinstance(repo_config["executor_job_path"], str)
            assert isinstance(repo_config["github_credentials_id"], str)
            executor_os_val = repo_config.get("executor_os")
            validated_config: dict[str, str] = {
                "repo_url": repo_config["repo_url"],
                "executor_job_path": repo_config["executor_job_path"],
                "github_credentials_id": repo_config["github_credentials_id"],
                "executor_os": (
                    executor_os_val if isinstance(executor_os_val, str) else "linux"
                ),
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
            except (
                Exception
            ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
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
                            RepoIdentifier.from_full_name(repo_full_name),
                            issue_number=issue["number"],
                            old_label=current_label,
                            new_label=workflow_config["next_label"],
                        )
                    except (
                        Exception
                    ) as cache_error:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
                        logger.warning(
                            f"Cache update failed for issue #{issue['number']}: {cache_error}"
                        )

                except (
                    Exception
                ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
                    # Fail-fast: log error and exit immediately
                    logger.error(
                        f"Failed processing issue #{issue['number']}: {e}",
                        exc_info=True,
                    )
                    return 1

            logger.info(f"Successfully processed all issues in {repo_name}")

        # Step 5: Success - all repos processed
        return 0

    except ValueError as e:
        logger.error("%s", e)
        return 1

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
        # Let all other exceptions bubble up with full traceback
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise
