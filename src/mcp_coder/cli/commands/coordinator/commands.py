"""CLI command handlers for coordinator package.

The coordinator command monitors GitHub issues and dispatches workflows based on
labels. Use --dry-run to trigger Jenkins integration tests instead.
"""

import argparse
import logging
from time import sleep  # module-level name so tests patch commands.sleep only
from typing import NamedTuple

from ....mcp_workspace_github import (
    BodyTrust,
    BodyTrustResult,
    GitHubRateLimitError,
    IssueBranchManager,
    IssueData,
    IssueManager,
    RepoIdentifier,
    get_all_cached_issues,
    update_issue_labels_in_cache,
)
from ....utils.jenkins_operations.client import JenkinsClient, JenkinsError
from ....utils.log_utils import OUTPUT
from ....utils.user_config import (
    create_default_config,
    get_cache_refresh_minutes,
    get_config_file_path,
    get_dispatch_delay_seconds,
    load_config,
)
from ....workflow_utils.issue_trust import evaluate_body_trust
from ....workflow_utils.rate_limit import (
    as_rate_limit,
    log_rate_limit_stop,
    raise_if_rate_limited,
)
from ....workflows.pr_health import check_pr_health
from ...utils import log_command_startup
from .command_templates import TEST_COMMAND_TEMPLATES
from .core import (
    DispatchResult,
    _filter_eligible_issues,
    build_jenkins_label,
    dispatch_workflow,
    find_waiting_build,
    get_eligible_issues,
    get_jenkins_credentials,
    load_repo_config,
    stage_index,
    validate_repo_config,
)
from .workflow_constants import WORKFLOW_MAPPING

__all__ = [
    "execute_coordinator_test",
    "execute_coordinator_run",
    "format_job_output",
]


logger = logging.getLogger(__name__)


def format_job_output(job_path: str, queue_id: int, url: str | None) -> str:
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
        assert isinstance(repo_config["repo_url"], str)  # noqa: S101
        assert isinstance(repo_config["executor_job_path"], str)  # noqa: S101
        assert isinstance(repo_config["github_credentials_id"], str)  # noqa: S101
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
        assert isinstance(repo_config["executor_os"], str)  # noqa: S101
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
            "LABEL": build_jenkins_label(args.repo_name, args.branch_name, "test"),
        }

        # Start job (API token in Basic Auth bypasses CSRF)
        queue_id = client.start_job(validated_config["executor_job_path"], params)

        # Try to get job URL (may not be available immediately)
        try:
            status = client.get_job_status(queue_id)
            job_url = status.url
        except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
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

    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
        # Let all other exceptions bubble up; main.py's top-level boundary logs
        # the traceback.
        logger.error(f"Unexpected error: {e}")
        raise


class _Repo(NamedTuple):
    """Per-repository values the dispatch loop needs."""

    # Position in config order, the sort tie-break. Not named ``index``:
    # that would shadow tuple.index.
    config_index: int
    name: str
    repo_identifier: RepoIdentifier
    config: dict[str, str]
    issue_manager: IssueManager
    branch_manager: IssueBranchManager
    # Blocked-state key, as Jenkins reports it: two spellings of one path share it.
    job_url: str
    # First configured path that resolved to job_url; used for capacity checks.
    job_path: str


def _dispatch_sort_key(item: tuple[IssueData, _Repo]) -> tuple[int, int]:
    """Stage first, then config repo order; extend the tuple for further criteria.

    Returns:
        The sort key of one work item.
    """
    return (stage_index(item[0]), item[1].config_index)


def _collect_work(
    repo_names: list[str],
    force_refresh: bool,
    jenkins_client: JenkinsClient,
    blocked: set[str],
) -> list[tuple[IssueData, _Repo]]:
    """Load each repo's config and fetch its eligible issues, in config order.

    Resolves each repo's executor job and checks its capacity once per job URL,
    before any GitHub call. A busy job's URL is added to ``blocked`` and its
    repos are skipped: no managers, no fetch (``force_refresh`` does not override).

    For each repo with capacity and a working issue cache, PR-health runs on
    the full cached issue list (not only the eligible issues). A cache failure
    falls back to a direct fetch of the eligible issues and skips PR-health.

    An invalid repo config (ValueError) and a rate limit during a fetch or
    from PR-health propagate to the caller's handlers.

    Args:
        repo_names: Repository names from the config, in config order.
        force_refresh: Bypass the issue cache.
        jenkins_client: Client for the job lookups and capacity checks.
        blocked: Job URLs without capacity; busy jobs found here are added.

    Returns:
        One (issue, repo) item per eligible issue, unsorted: repos in config
        order, issues in fetch order within a repo.

    Raises:
        JenkinsError: If a job lookup or capacity check fails.
    """  # noqa: DOC502 - raised by get_job_url / find_waiting_build
    work: list[tuple[IssueData, _Repo]] = []
    job_urls: dict[str, str] = {}  # configured path -> job URL
    job_paths: dict[str, str] = {}  # job URL -> first configured path
    checked: set[str] = set()
    for index, repo_name in enumerate(repo_names):
        # Load and validate repo config
        repo_config = load_repo_config(repo_name)
        validate_repo_config(repo_name, repo_config)

        # Log repository header with URL
        repo_url = repo_config["repo_url"]
        logger.info(f"{'=' * 80}")
        logger.info(f"Processing repository: {repo_url}")
        logger.info(f"{'=' * 80}")

        # Type narrowing: validate_repo_config raises if any fields are None
        # Assert to help mypy understand the values are str after validation
        assert isinstance(repo_config["repo_url"], str)  # noqa: S101
        assert isinstance(repo_config["executor_job_path"], str)  # noqa: S101
        assert isinstance(repo_config["github_credentials_id"], str)  # noqa: S101
        executor_os_val = repo_config.get("executor_os")
        validated_config: dict[str, str] = {
            "repo_url": repo_config["repo_url"],
            "executor_job_path": repo_config["executor_job_path"],
            "github_credentials_id": repo_config["github_credentials_id"],
            "executor_os": (
                executor_os_val if isinstance(executor_os_val, str) else "linux"
            ),
        }

        # Capacity gate, before any GitHub call
        job_path = validated_config["executor_job_path"]
        if job_path not in job_urls:
            job_urls[job_path] = jenkins_client.get_job_url(job_path)
        job_url = job_urls[job_path]
        job_paths.setdefault(job_url, job_path)
        if job_url not in checked:
            checked.add(job_url)
            if find_waiting_build(jenkins_client, job_paths[job_url]):
                blocked.add(job_url)
        if job_url in blocked:
            logger.debug("Skipping repository %s: executor job busy", repo_name)
            continue

        # Create managers
        issue_manager = IssueManager(repo_url=validated_config["repo_url"])
        branch_manager = IssueBranchManager(repo_url=validated_config["repo_url"])

        # Get all issues using cache, eligible issues filtered from that list
        repo_identifier = RepoIdentifier.from_repo_url(validated_config["repo_url"])
        try:
            all_issues = get_all_cached_issues(
                repo_identifier,
                issue_manager=issue_manager,
                force_refresh=force_refresh,
                cache_refresh_minutes=get_cache_refresh_minutes(),
            )
            eligible_issues = _filter_eligible_issues(all_issues)
        except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
            raise_if_rate_limited(e)
            logger.warning(
                f"Cache failed for {repo_identifier.full_name}: {e}, using direct fetch"
            )
            eligible_issues = get_eligible_issues(issue_manager)
        else:
            # Only with a working cache; errors here must not trigger the fallback
            check_pr_health(repo_name, validated_config, all_issues)

        logger.info(f"Found {len(eligible_issues)} eligible issues")

        if not eligible_issues:
            logger.info(f"No eligible issues for {repo_name}")
            continue

        repo = _Repo(
            config_index=index,
            name=repo_name,
            repo_identifier=repo_identifier,
            config=validated_config,
            issue_manager=issue_manager,
            branch_manager=branch_manager,
            job_url=job_url,
            job_path=job_paths[job_url],
        )
        work.extend((issue, repo) for issue in eligible_issues)
    return work


def _recheck_after_delay(
    jenkins_client: JenkinsClient, pending: _Repo, delay: int, blocked: set[str]
) -> None:
    """Sleep ``delay`` seconds, then re-check the job that got the last build.

    Adds ``pending.job_url`` to ``blocked`` when that job still has a waiting
    build. The delay must exceed the Jenkins quiet period: a build in its quiet
    period is a queue item, not a build, and so invisible to the check.

    Args:
        jenkins_client: Client for the capacity check.
        pending: Repo whose executor job got the last started build.
        delay: Seconds to wait before the check.
        blocked: Job URLs without capacity; updated in place.

    Raises:
        JenkinsError: If the build list cannot be read.
    """  # noqa: DOC502 - raised by find_waiting_build
    sleep(delay)
    if find_waiting_build(jenkins_client, pending.job_path):
        blocked.add(pending.job_url)


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

        # Wrong TOML type -> ValueError -> ERROR line, exit 1
        delay = get_dispatch_delay_seconds()

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

        # Step 4: Collect the eligible issues of all repos, then sort globally
        # (stable: keeps fetch order on ties)
        # Busy executor jobs end up in ``blocked`` (job URLs); ``pending`` is the
        # repo whose job got the last build and still needs its re-check.
        blocked: set[str] = set()
        work = _collect_work(repo_names, args.force_refresh, jenkins_client, blocked)
        work.sort(key=_dispatch_sort_key)

        # Step 5: Dispatch workflows for each eligible issue (fail-fast)
        skipped: dict[str, list[tuple[int, BodyTrustResult]]] = {}
        pending: _Repo | None = None
        try:
            for issue, repo in work:
                if repo.job_url in blocked:
                    continue

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

                # The delay is taken before the next attempt, so none after the
                # last dispatch. Outside the dispatch try: a gate error is not an
                # issue failure.
                if pending is not None:
                    _recheck_after_delay(jenkins_client, pending, delay, blocked)
                    pending = None
                    if repo.job_url in blocked:
                        continue

                # Gate: never feed an untrusted body to a workflow.
                # Outside the dispatch try so a rate limit stops the run.
                trust = evaluate_body_trust(repo.issue_manager, issue)
                if trust.status is not BodyTrust.TRUSTED:
                    logger.debug(
                        "Issue #%d skipped: body %s (%s)",
                        issue["number"],
                        trust.status.value,
                        trust.reason,
                    )
                    skipped.setdefault(repo.name, []).append((issue["number"], trust))
                    continue

                workflow_config = WORKFLOW_MAPPING[current_label]
                workflow_name = workflow_config["workflow"]

                try:
                    result = dispatch_workflow(
                        issue=issue,
                        workflow_name=workflow_name,
                        repo_config=repo.config,
                        repo_name=repo.name,
                        jenkins_client=jenkins_client,
                        issue_manager=repo.issue_manager,
                        branch_manager=repo.branch_manager,
                        log_level=args.log_level,
                    )
                    if result is DispatchResult.STARTED_LABEL_RATE_LIMITED:
                        # Job started, label swap hit a rate limit
                        return 1
                    if result is DispatchResult.STARTED:
                        pending = repo

                    # Update cache with new labels immediately after successful dispatch
                    try:
                        update_issue_labels_in_cache(
                            repo.repo_identifier,
                            issue_number=issue["number"],
                            old_label=current_label,
                            new_label=workflow_config["next_label"],
                        )
                    except Exception as cache_error:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
                        raise_if_rate_limited(cache_error)
                        logger.warning(
                            f"Cache update failed for issue #{issue['number']}: {cache_error}"
                        )

                except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
                    raise_if_rate_limited(e)
                    # Fail-fast: log error and exit immediately
                    logger.error(f"Failed processing issue #{issue['number']}: {e}")
                    return 1
        finally:
            for repo_name, repo_skipped in skipped.items():
                logger.info(
                    "Skipped %d issue(s) in %s with untrusted body: %s",
                    len(repo_skipped),
                    repo_name,
                    ", ".join(
                        f"#{number} ({trust_result.status.value}: {trust_result.reason})"
                        for number, trust_result in repo_skipped
                    ),
                )

        logger.info("Finished dispatching eligible issues")

        # Step 6: Success - all repos processed
        return 0

    except GitHubRateLimitError as e:
        log_rate_limit_stop(e)
        return 0

    except JenkinsError as e:
        # Job lookup or capacity check failed: the message is the diagnosis.
        logger.error("%s", e)
        return 1

    except ValueError as e:
        if (rl := as_rate_limit(e)) is not None:
            log_rate_limit_stop(rl)
            return 0
        logger.error("%s", e)
        return 1

    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow per sub-workflow error types
        if (rl := as_rate_limit(e)) is not None:
            log_rate_limit_stop(rl)
            return 0
        # Let all other exceptions bubble up with full traceback
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise
