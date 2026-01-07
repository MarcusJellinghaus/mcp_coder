"""Core business logic for coordinator package.

This module contains:
- Configuration management functions
- CacheData class and caching system
- Issue filtering functions
- Workflow dispatch function
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Lazy imports from coordinator package to enable test patching
# Tests can patch at 'mcp_coder.cli.commands.coordinator.<name>'
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TypedDict
from urllib.parse import quote

from ....utils.github_operations.github_utils import RepoIdentifier
from ....utils.github_operations.issue_branch_manager import IssueBranchManager
from ....utils.github_operations.issue_manager import IssueData, IssueManager
from ....utils.jenkins_operations.client import JenkinsClient
from ....utils.jenkins_operations.models import JobStatus
from ....utils.timezone_utils import (
    format_for_cache,
    is_within_duration,
    now_utc,
    parse_iso_timestamp,
)
from ....utils.user_config import get_config_file_path
from .command_templates import (
    CREATE_PLAN_COMMAND_TEMPLATE,
    CREATE_PLAN_COMMAND_WINDOWS,
    CREATE_PR_COMMAND_TEMPLATE,
    CREATE_PR_COMMAND_WINDOWS,
    IMPLEMENT_COMMAND_TEMPLATE,
    IMPLEMENT_COMMAND_WINDOWS,
    PRIORITY_ORDER,
)
from .workflow_constants import WORKFLOW_MAPPING

if TYPE_CHECKING:
    from types import ModuleType


def _get_coordinator() -> "ModuleType":
    """Get coordinator package for late binding of patchable functions."""
    from mcp_coder.cli.commands import coordinator

    return coordinator


logger = logging.getLogger(__name__)


def load_repo_config(repo_name: str) -> dict[str, Optional[str]]:
    """Load repository configuration from config file.

    Args:
        repo_name: Name of repository to load (e.g., "mcp_coder")

    Returns:
        Dictionary with repo_url, executor_job_path, github_credentials_id, executor_os
        Values may be None except executor_os which defaults to "linux" (normalized to lowercase)
    """
    # Use late binding for patchable function access
    coordinator = _get_coordinator()

    section = f"coordinator.repos.{repo_name}"

    repo_url = coordinator.get_config_value(section, "repo_url")
    executor_job_path = coordinator.get_config_value(section, "executor_job_path")
    github_credentials_id = coordinator.get_config_value(
        section, "github_credentials_id"
    )

    # Load executor_os with default and normalize to lowercase
    executor_os = coordinator.get_config_value(section, "executor_os")
    if executor_os:
        executor_os = executor_os.lower()  # Normalize to lowercase
    else:
        executor_os = "linux"  # Default

    # Always return dict with field values (may be None except executor_os)
    return {
        "repo_url": repo_url,
        "executor_job_path": executor_job_path,
        "github_credentials_id": github_credentials_id,
        "executor_os": executor_os,
    }


def validate_repo_config(repo_name: str, config: dict[str, Optional[str]]) -> None:
    """Validate repository configuration has all required fields.

    Args:
        repo_name: Name of repository being validated
        config: Repository configuration dict with possibly None values

    Raises:
        ValueError: If any required fields are missing or invalid with detailed error message
    """
    required_fields = ["repo_url", "executor_job_path", "github_credentials_id"]
    missing_fields = []

    for field in required_fields:
        if field not in config or not config[field]:
            missing_fields.append(field)

    if missing_fields:
        config_path = get_config_file_path()
        section_name = f"coordinator.repos.{repo_name}"

        # Build concise one-line error message for each missing field
        if len(missing_fields) == 1:
            field = missing_fields[0]
            error_msg = (
                f"Config file: {config_path} - "
                f"section [{section_name}] - "
                f"value for field '{field}' missing"
            )
        else:
            # Multiple missing fields
            fields_str = "', '".join(missing_fields)
            error_msg = (
                f"Config file: {config_path} - "
                f"section [{section_name}] - "
                f"values for fields '{fields_str}' missing"
            )

        raise ValueError(error_msg)

    # Validate executor_os field (already normalized to lowercase by load_repo_config)
    executor_os = config.get("executor_os", "linux")
    if executor_os not in ["windows", "linux"]:
        config_path = get_config_file_path()
        section_name = f"coordinator.repos.{repo_name}"
        error_msg = (
            f"Config file: {config_path} - "
            f"section [{section_name}] - "
            f"value for field 'executor_os' invalid: got '{executor_os}'. "
            f"Must be 'windows' or 'linux' (case-insensitive)"
        )
        raise ValueError(error_msg)


def get_cache_refresh_minutes() -> int:
    """Get cache refresh threshold from config with default fallback.

    Returns:
        Cache refresh threshold in minutes (default: 1440 = 24 hours)
    """
    # Use late binding for patchable function access
    coordinator = _get_coordinator()

    value = coordinator.get_config_value("coordinator", "cache_refresh_minutes")

    if value is None:
        return 1440  # Default: 24 hours

    try:
        result = int(value)
        if result <= 0:
            logger.warning(
                f"Invalid cache_refresh_minutes value '{value}' (must be positive), using default 1440"
            )
            return 1440
        return result
    except (ValueError, TypeError):
        logger.warning(
            f"Invalid cache_refresh_minutes value '{value}' (must be integer), using default 1440"
        )
        return 1440


def get_jenkins_credentials() -> tuple[str, str, str]:
    """Get Jenkins credentials from environment or config file.

    Priority: Environment variables > Config file

    Returns:
        Tuple of (server_url, username, api_token)

    Raises:
        ValueError: If any required credential is missing
    """
    # Use late binding for patchable function access
    coordinator = _get_coordinator()

    # get_config_value automatically checks environment variables first
    server_url = coordinator.get_config_value("jenkins", "server_url")
    username = coordinator.get_config_value("jenkins", "username")
    api_token = coordinator.get_config_value("jenkins", "api_token")

    # Check for missing credentials
    missing = []
    if not server_url:
        missing.append("server_url")
    if not username:
        missing.append("username")
    if not api_token:
        missing.append("api_token")

    if missing:
        raise ValueError(
            f"Jenkins configuration incomplete. Missing: {', '.join(missing)}\n"
            f"Set via environment variables (JENKINS_URL, JENKINS_USER, JENKINS_TOKEN) "
            f"or config file [jenkins] section"
        )

    # Type narrowing: if we reach here, all values are non-None
    assert server_url is not None
    assert username is not None
    assert api_token is not None

    return (server_url, username, api_token)


class CacheData(TypedDict):
    """Type definition for coordinator issue cache structure.

    Attributes:
        last_checked: ISO 8601 timestamp of last cache refresh, or None if never checked
        issues: Dictionary mapping issue number (as string) to IssueData
    """

    last_checked: Optional[str]
    issues: Dict[str, IssueData]


def _load_cache_file(cache_file_path: Path) -> CacheData:
    """Load cache file or return empty cache structure.

    Args:
        cache_file_path: Path to cache file

    Returns:
        CacheData with last_checked and issues, or empty structure on errors
    """
    try:
        if not cache_file_path.exists():
            return {"last_checked": None, "issues": {}}

        with cache_file_path.open("r") as f:
            data = json.load(f)

        # Validate structure
        if not isinstance(data, dict) or "issues" not in data:
            logger.warning(f"Invalid cache structure in {cache_file_path}, recreating")
            return {"last_checked": None, "issues": {}}

        # Return as CacheData since we validated the structure
        return {"last_checked": data.get("last_checked"), "issues": data["issues"]}

    except (json.JSONDecodeError, OSError, PermissionError) as e:
        logger.warning(f"Cache load error for {cache_file_path}: {e}, starting fresh")
        return {"last_checked": None, "issues": {}}


def _log_cache_metrics(action: str, repo_name: str, **kwargs: Any) -> None:
    """Log detailed cache performance metrics at DEBUG level.

    Args:
        action: Cache action ('hit', 'miss', 'refresh', 'save')
        repo_name: Repository name for logging context
        **kwargs: Additional metrics (age_minutes, issue_count, reason, etc.)
    """
    if action == "hit":
        age_minutes = kwargs.get("age_minutes", 0)
        issue_count = kwargs.get("issue_count", 0)
        logger.debug(
            f"Cache hit for {repo_name}: age={age_minutes}m, issues={issue_count}"
        )
    elif action == "miss":
        reason = kwargs.get("reason", "unknown")
        logger.debug(f"Cache miss for {repo_name}: reason='{reason}'")
    elif action == "refresh":
        refresh_type = kwargs.get("refresh_type", "unknown")
        issue_count = kwargs.get("issue_count", 0)
        logger.debug(
            f"Cache refresh for {repo_name}: type={refresh_type}, new_issues={issue_count}"
        )
    elif action == "save":
        total_issues = kwargs.get("total_issues", 0)
        logger.debug(f"Cache save for {repo_name}: total_issues={total_issues}")


def _save_cache_file(cache_file_path: Path, cache_data: CacheData) -> bool:
    """Save cache data to file using atomic write.

    Args:
        cache_file_path: Path to cache file
        cache_data: CacheData to save

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        cache_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp file, then rename
        temp_path = cache_file_path.with_suffix(".tmp")
        with temp_path.open("w") as f:
            json.dump(cache_data, f, indent=2)
        temp_path.replace(cache_file_path)  # Atomic rename

        return True

    except (OSError, PermissionError) as e:
        logger.warning(f"Cache save error for {cache_file_path}: {e}")
        return False


def _get_cache_file_path(repo_identifier: RepoIdentifier) -> Path:
    """Get cache file path using RepoIdentifier.

    Args:
        repo_identifier: Repository identifier with owner and repo name

    Returns:
        Path to cache file
    """
    cache_dir = Path.home() / ".mcp_coder" / "coordinator_cache"
    return cache_dir / f"{repo_identifier.cache_safe_name}.issues.json"


def _update_issue_labels_in_cache(
    repo_full_name: str, issue_number: int, old_label: str, new_label: str
) -> None:
    """Update issue labels in cache after successful dispatch.

    Updates the cached issue labels to reflect GitHub label changes made
    during workflow dispatch. This prevents stale cache data from causing
    duplicate dispatches within the 1-minute duplicate protection window.

    Args:
        repo_full_name: Repository in "owner/repo" format (e.g., "anthropics/claude-code")
        issue_number: GitHub issue number to update
        old_label: Label to remove from cached issue
        new_label: Label to add to cached issue

    Note:
        Cache update failures are logged as warnings but do not interrupt
        the main workflow. The next cache refresh will fetch correct data
        from GitHub API.
    """
    # Use late binding for patchable function access
    coordinator = _get_coordinator()

    try:
        # Step 1: Parse repository identifier
        repo_identifier = RepoIdentifier.from_full_name(repo_full_name)

        # Step 2: Load existing cache
        cache_file_path = coordinator._get_cache_file_path(repo_identifier)
        cache_data = coordinator._load_cache_file(cache_file_path)

        # Step 3: Find target issue in cache
        issue_key = str(issue_number)
        if issue_key not in cache_data["issues"]:
            logger.warning(
                f"Issue #{issue_number} not found in cache for {repo_full_name}"
            )
            return

        # Step 4: Update issue labels
        issue = cache_data["issues"][issue_key]
        current_labels = list(issue.get("labels", []))

        # Remove old label if present
        if old_label in current_labels:
            current_labels.remove(old_label)

        # Add new label if not already present
        if new_label and new_label not in current_labels:
            current_labels.append(new_label)

        # Update cached issue
        issue["labels"] = current_labels
        cache_data["issues"][issue_key] = issue

        # Step 5: Save updated cache
        save_success = coordinator._save_cache_file(cache_file_path, cache_data)
        if save_success:
            logger.debug(
                f"Updated issue #{issue_number} labels in cache: '{old_label}' -> '{new_label}'"
            )
        else:
            logger.warning(
                f"Cache update failed for issue #{issue_number}: save operation failed"
            )

    except ValueError as e:
        # Repository parsing or cache structure errors
        logger.warning(f"Cache update failed for issue #{issue_number}: {e}")
    except Exception as e:
        # Any unexpected errors - don't break main workflow
        logger.warning(
            f"Unexpected error updating cache for issue #{issue_number}: {e}"
        )


def _log_stale_cache_entries(
    cached_issues: Dict[str, IssueData], fresh_issues: Dict[str, IssueData]
) -> None:
    """Log detailed staleness information when cached data differs from fresh data.

    Args:
        cached_issues: Issues from cache (issue_number -> IssueData)
        fresh_issues: Fresh issues from API (issue_number -> IssueData)
    """
    # Check for state/label changes in existing issues
    for issue_num, cached_issue in cached_issues.items():
        if issue_num in fresh_issues:
            fresh_issue = fresh_issues[issue_num]

            # Check state changes
            if cached_issue.get("state") != fresh_issue.get("state"):
                logger.info(
                    f"Issue #{issue_num}: cached state '{cached_issue.get('state')}' != "
                    f"actual '{fresh_issue.get('state')}'"
                )

            # Check label changes
            cached_labels = set(cached_issue.get("labels", []))
            fresh_labels = set(fresh_issue.get("labels", []))
            if cached_labels != fresh_labels:
                logger.info(
                    f"Issue #{issue_num}: cached labels {sorted(cached_labels)} != "
                    f"actual {sorted(fresh_labels)}"
                )
        else:
            # Issue no longer exists
            logger.info(f"Issue #{issue_num}: no longer exists in repository")


def _filter_eligible_issues(issues: List[IssueData]) -> List[IssueData]:
    """Filter issues for eligibility (same logic as get_eligible_issues).

    Args:
        issues: List of issues to filter

    Returns:
        List of eligible issues sorted by priority
    """
    # Use late binding for patchable function access
    coordinator = _get_coordinator()

    # Load label configuration
    from importlib import resources

    config_resource = resources.files("mcp_coder.config") / "labels.json"
    config_path = Path(str(config_resource))
    labels_config = coordinator.load_labels_config(config_path)

    # Extract bot_pickup labels and ignore_labels
    bot_pickup_labels = set()
    for label in labels_config["workflow_labels"]:
        if label["category"] == "bot_pickup":
            bot_pickup_labels.add(label["name"])

    ignore_labels_set = set(labels_config.get("ignore_labels", []))

    # Filter issues (only open state)
    eligible_issues = []
    for issue in issues:
        # Skip if not open
        if issue.get("state") != "open":
            continue

        issue_labels = set(issue["labels"])

        # Count bot_pickup labels on this issue
        bot_pickup_count = len(issue_labels & bot_pickup_labels)

        # Skip if not exactly one bot_pickup label
        if bot_pickup_count != 1:
            continue

        # Skip if has any ignore_labels
        if issue_labels & ignore_labels_set:
            continue

        # Issue is eligible
        eligible_issues.append(issue)

    # Sort by priority
    priority_map = {label: i for i, label in enumerate(PRIORITY_ORDER)}

    def get_priority(issue: IssueData) -> int:
        """Get priority index for an issue (lower = higher priority)."""
        for label in issue["labels"]:
            if label in priority_map:
                return priority_map[label]
        return len(PRIORITY_ORDER)  # Lowest priority

    eligible_issues.sort(key=get_priority)
    return eligible_issues


def get_eligible_issues(
    issue_manager: IssueManager, log_level: str = "INFO"
) -> list[IssueData]:
    """Get issues ready for automation, sorted by priority.

    Args:
        issue_manager: IssueManager instance for GitHub API calls
        log_level: Logging level for debug output

    Returns:
        List of IssueData sorted by priority:
        1. status-08:ready-pr (highest priority)
        2. status-05:plan-ready
        3. status-02:awaiting-planning (lowest priority)

    Raises:
        GithubException: If GitHub API errors occur
    """
    # Use late binding for patchable function access
    coordinator = _get_coordinator()

    # Load label configuration
    # Uses bundled package config (coordinator operates without local project context)
    from importlib import resources

    config_resource = resources.files("mcp_coder.config") / "labels.json"
    config_path = Path(str(config_resource))
    labels_config = coordinator.load_labels_config(config_path)

    # Extract bot_pickup labels (labels with category="bot_pickup")
    bot_pickup_labels = set()
    for label in labels_config["workflow_labels"]:
        if label["category"] == "bot_pickup":
            bot_pickup_labels.add(label["name"])

    # Extract ignore_labels set for filtering
    ignore_labels_set = set(labels_config.get("ignore_labels", []))

    # Query all open issues (exclude pull requests)
    all_issues = issue_manager.list_issues(state="open", include_pull_requests=False)
    logger.debug(f"Found {len(all_issues)} open issues")

    # Filter issues
    eligible_issues = []
    for issue in all_issues:
        issue_labels = set(issue["labels"])

        # Count bot_pickup labels on this issue
        bot_pickup_count = len(issue_labels & bot_pickup_labels)

        # Skip if not exactly one bot_pickup label
        if bot_pickup_count != 1:
            continue

        # Skip if has any ignore_labels
        if issue_labels & ignore_labels_set:
            continue

        # Issue is eligible
        eligible_issues.append(issue)

    logger.debug(f"Filtered to {len(eligible_issues)} eligible issues")

    # Sort by priority
    priority_map = {label: i for i, label in enumerate(PRIORITY_ORDER)}

    def get_priority(issue: IssueData) -> int:
        """Get priority index for an issue (lower = higher priority)."""
        for label in issue["labels"]:
            if label in priority_map:
                return priority_map[label]
        # Should not happen if filtering worked correctly
        return len(PRIORITY_ORDER)  # Lowest priority

    eligible_issues.sort(key=get_priority)

    return eligible_issues


def get_cached_eligible_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
) -> List[IssueData]:
    """Get eligible issues using cache for performance and duplicate protection.

    Uses GitHub API caching with incremental fetching via the 'since' parameter
    for efficient API usage. The 'since' parameter allows fetching only issues
    modified after a specific timestamp, reducing API calls and improving performance.

    Args:
        repo_full_name: Repository in "owner/repo" format (e.g., "anthropics/claude-code")
        issue_manager: IssueManager for GitHub API calls
        force_refresh: Bypass cache entirely
        cache_refresh_minutes: Full refresh threshold (default: 1440 = 24 hours)

    Returns:
        List of eligible issues (open state, meeting bot pickup criteria)
    """
    # Use late binding for patchable function access
    coordinator = _get_coordinator()

    repo_identifier = None
    try:
        # Step 1: Create RepoIdentifier from repo_full_name
        repo_identifier = RepoIdentifier.from_full_name(repo_full_name)

        # Step 2: Check duplicate protection (1-minute window) with RepoIdentifier
        cache_file_path = coordinator._get_cache_file_path(repo_identifier)
        try:
            cache_data = coordinator._load_cache_file(cache_file_path)
        except Exception as cache_error:
            # If cache loading fails with unexpected error, fall back to direct fetch
            coordinator._log_cache_metrics(
                "miss",
                repo_identifier.repo_name,
                reason=f"cache_load_error_{type(cache_error).__name__}",
            )
            logger.warning(
                f"Cache load error for {repo_identifier.full_name}: {cache_error}, falling back to direct fetch"
            )
            return coordinator.get_eligible_issues(issue_manager)  # type: ignore[no-any-return]

        # Log cache metrics
        coordinator._log_cache_metrics(
            "miss" if not cache_data["last_checked"] else "hit",
            repo_identifier.repo_name,
            reason="no_cache" if not cache_data["last_checked"] else "cache_found",
        )

        # Parse last_checked timestamp using timezone utilities
        last_checked = None
        if cache_data["last_checked"]:
            try:
                # Parse timezone-aware datetime and convert to UTC
                last_checked = parse_iso_timestamp(cache_data["last_checked"])
            except ValueError as e:
                logger.debug(
                    f"Invalid timestamp in cache: {cache_data['last_checked']}, error: {e}"
                )

        # Duplicate protection: skip if checked within last minute
        now = now_utc()
        if (
            not force_refresh
            and last_checked
            and is_within_duration(last_checked, 60.0, now)
        ):
            age_seconds = int((now - last_checked).total_seconds())
            coordinator._log_cache_metrics(
                "hit",
                repo_identifier.repo_name,
                age_minutes=0,
                reason=f"duplicate_protection_{age_seconds}s",
            )
            logger.info(
                f"Skipping {repo_identifier.repo_name} - checked {age_seconds}s ago"
            )
            # Return cached eligible issues instead of empty list
            all_cached_issues = list(cache_data["issues"].values())
            return coordinator._filter_eligible_issues(all_cached_issues)  # type: ignore[no-any-return]

        # Step 3: Determine refresh strategy
        is_full_refresh = (
            force_refresh
            or not last_checked
            or (now - last_checked) > timedelta(minutes=cache_refresh_minutes)
        )

        # Step 4: Fetch issues using appropriate method
        if is_full_refresh:
            refresh_type = "force" if force_refresh else "full"
            logger.debug(
                f"Full refresh for {repo_identifier.repo_name} (type={refresh_type})"
            )
            fresh_issues = issue_manager.list_issues(
                state="open", include_pull_requests=False
            )
            coordinator._log_cache_metrics(
                "refresh",
                repo_identifier.repo_name,
                refresh_type=refresh_type,
                issue_count=len(fresh_issues),
            )

            # Log staleness if we had cached data
            if cache_data["issues"]:
                fresh_issues_dict = {
                    str(issue["number"]): issue for issue in fresh_issues
                }
                coordinator._log_stale_cache_entries(
                    cache_data["issues"], fresh_issues_dict
                )
        else:
            # last_checked is guaranteed to be non-None here due to is_full_refresh logic
            assert last_checked is not None
            cache_age_minutes = int((now - last_checked).total_seconds() / 60)
            logger.debug(
                f"Incremental refresh for {repo_identifier.repo_name} since {last_checked} (age={cache_age_minutes}m)"
            )
            # GitHub API 'since' parameter expects ISO 8601 timestamp
            # Only returns issues modified after this timestamp
            fresh_issues = issue_manager.list_issues(
                state="open", include_pull_requests=False, since=last_checked
            )
            coordinator._log_cache_metrics(
                "refresh",
                repo_identifier.repo_name,
                refresh_type="incremental",
                issue_count=len(fresh_issues),
            )

        # Step 5: Merge fresh issues with cached issues
        # Convert to dict for easier merging
        fresh_issues_dict = {str(issue["number"]): issue for issue in fresh_issues}

        # Update cache with fresh data
        cache_data["issues"].update(fresh_issues_dict)
        cache_data["last_checked"] = format_for_cache(now)

        # Always save cache to update last_checked timestamp
        # This ensures incremental fetches work properly on subsequent runs
        save_success = coordinator._save_cache_file(cache_file_path, cache_data)
        if save_success:
            coordinator._log_cache_metrics(
                "save",
                repo_identifier.repo_name,
                total_issues=len(cache_data["issues"]),
            )

        # Step 7: Filter cached issues for eligibility
        all_cached_issues = list(cache_data["issues"].values())
        eligible_issues = coordinator._filter_eligible_issues(all_cached_issues)

        coordinator._log_cache_metrics(
            "hit",
            repo_identifier.repo_name,
            age_minutes=(
                int((now - last_checked).total_seconds() / 60) if last_checked else 0
            ),
            issue_count=len(eligible_issues),
        )

        logger.debug(
            f"Cache returned {len(eligible_issues)} eligible issues for {repo_identifier.repo_name}"
        )
        return eligible_issues  # type: ignore[no-any-return]

    except (ValueError, KeyError, TypeError) as e:
        repo_name = repo_identifier.repo_name if repo_identifier else "unknown_repo"
        full_name = repo_identifier.full_name if repo_identifier else "unknown/unknown"
        coordinator._log_cache_metrics(
            "miss", repo_name, reason=f"error_{type(e).__name__}"
        )
        logger.warning(
            f"Cache error for {full_name}: {e}, falling back to direct fetch"
        )
        return coordinator.get_eligible_issues(issue_manager)  # type: ignore[no-any-return]


def dispatch_workflow(
    issue: IssueData,
    workflow_name: str,
    repo_config: dict[str, str],
    jenkins_client: JenkinsClient,
    issue_manager: IssueManager,
    branch_manager: IssueBranchManager,
    log_level: str,
) -> None:
    """Trigger Jenkins job for workflow and update issue label.

    Args:
        issue: GitHub issue data
        workflow_name: Workflow to execute ("create-plan", "implement", "create-pr")
        repo_config: Repository configuration with repo_url, executor_test_path, credentials
        jenkins_client: Jenkins client for job triggering
        issue_manager: IssueManager for label updates
        branch_manager: IssueBranchManager for branch resolution
        log_level: Log level to pass to workflow command

    Raises:
        ValueError: If linked branch missing for implement/create-pr
        JenkinsError: If job trigger or status check fails
    """
    # Step 1: Find current workflow label from issue
    current_label = None
    for label in issue["labels"]:
        if label in WORKFLOW_MAPPING:
            current_label = label
            break

    if not current_label:
        raise ValueError(f"No workflow label found on issue #{issue['number']}")

    workflow_config = WORKFLOW_MAPPING[current_label]

    # Step 2: Determine branch name based on branch_strategy
    if workflow_config["branch_strategy"] == "main":
        branch_name = "main"
    else:  # from_issue
        branches = branch_manager.get_linked_branches(issue["number"])
        if not branches:
            logger.warning(
                f"No linked branch found for issue #{issue['number']}, skipping workflow dispatch"
            )
            return
        branch_name = branches[0]

    # Step 3: Select appropriate command template based on executor_os and build command
    executor_os = repo_config.get("executor_os", "linux")

    if executor_os == "windows":
        # Windows templates
        if workflow_config["workflow"] == "create-plan":
            command = CREATE_PLAN_COMMAND_WINDOWS.format(
                log_level=log_level, issue_number=issue["number"]
            )
        elif workflow_config["workflow"] == "implement":
            command = IMPLEMENT_COMMAND_WINDOWS.format(
                log_level=log_level, branch_name=branch_name
            )
        else:  # create-pr
            command = CREATE_PR_COMMAND_WINDOWS.format(
                log_level=log_level, branch_name=branch_name
            )
    else:
        # Linux templates (default)
        if workflow_config["workflow"] == "create-plan":
            command = CREATE_PLAN_COMMAND_TEMPLATE.format(
                log_level=log_level, issue_number=issue["number"]
            )
        elif workflow_config["workflow"] == "implement":
            command = IMPLEMENT_COMMAND_TEMPLATE.format(
                log_level=log_level, branch_name=branch_name
            )
        else:  # create-pr
            command = CREATE_PR_COMMAND_TEMPLATE.format(
                log_level=log_level, branch_name=branch_name
            )

    # Step 4: Build Jenkins job parameters
    params = {
        "REPO_URL": repo_config["repo_url"],
        "BRANCH_NAME": branch_name,
        "COMMAND": command,
        "GITHUB_CREDENTIALS_ID": repo_config["github_credentials_id"],
    }

    # Step 5: Trigger Jenkins job
    queue_id = jenkins_client.start_job(repo_config["executor_job_path"], params)

    # Step 6: Get job status to retrieve build URL
    job_status = jenkins_client.get_job_status(queue_id)

    # Build Jenkins links: pipeline URL and build URL (if available)
    jenkins_base_url = jenkins_client._client.server.rstrip("/")
    # Convert job path to URL format: "Tests/mcp-coder-test" -> "Tests/job/mcp-coder-test"
    # URL-encode each part to handle spaces and special characters
    job_path_parts = repo_config["executor_job_path"].split("/")
    encoded_parts = [quote(part, safe="") for part in job_path_parts]
    pipeline_url = f"{jenkins_base_url}/job/" + "/job/".join(encoded_parts)

    if job_status.url:
        # Build has started - show build URL
        jenkins_link = f"Build: {job_status.url}"
    else:
        # Build still queued - show pipeline URL only
        jenkins_link = f"Pipeline: {pipeline_url}"

    # Step 7: Update issue labels (remove old, add new)
    issue_manager.remove_labels(issue["number"], current_label)
    issue_manager.add_labels(issue["number"], workflow_config["next_label"])

    # Step 8: Log success with issue and Jenkins links
    issue_url = issue["url"]
    logger.info(
        f"Successfully dispatched {workflow_config['workflow']} workflow for issue #{issue['number']}: "
        f"removed '{current_label}', added '{workflow_config['next_label']}' | "
        f"Issue: {issue_url} | {jenkins_link}"
    )
