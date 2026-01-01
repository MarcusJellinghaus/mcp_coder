"""Coordinator CLI commands for automated workflow orchestration.

Provides two main commands:
- coordinator test: Trigger Jenkins integration tests for repositories
- coordinator run: Monitor GitHub issues and dispatch workflows based on labels

The coordinator run command automates the issue → plan → implement → PR pipeline
by filtering eligible issues and triggering appropriate Jenkins workflows.

GitHub API Caching:
Implements efficient caching with incremental fetching using GitHub's 'since' parameter,
duplicate protection (1-minute windows), atomic file storage in ~/.mcp_coder/coordinator_cache/,
and graceful fallback to direct API calls on errors. Cache files: {owner}_{repo}.issues.json
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from ...utils.github_operations.github_utils import RepoIdentifier
from ...utils.github_operations.issue_branch_manager import IssueBranchManager
from ...utils.github_operations.issue_manager import IssueData, IssueManager
from ...utils.github_operations.label_config import load_labels_config
from ...utils.jenkins_operations.client import JenkinsClient
from ...utils.jenkins_operations.models import JobStatus
from ...utils.user_config import (
    create_default_config,
    get_config_file_path,
    get_config_value,
    load_config,
)

logger = logging.getLogger(__name__)


# Default test command for coordinator integration tests
# This comprehensive script verifies the complete environment setup
DEFAULT_TEST_COMMAND = """# Tool verification
which mcp-coder && mcp-coder --version
which mcp-code-checker && mcp-code-checker --help
which mcp-server-filesystem && mcp-server-filesystem --help
mcp-coder verify
export DISABLE_AUTOUPDATER=1
# Environment setup
export MCP_CODER_PROJECT_DIR='/workspace/repo'
export MCP_CODER_VENV_DIR='/workspace/.venv'
uv sync --extra dev
# Claude CLI verification
which claude
claude --mcp-config .mcp.json --strict-mcp-config mcp list
claude --mcp-config .mcp.json --strict-mcp-config -p "What is 1 + 1?"
# MCP Coder functionality test
mcp-coder --log-level {log_level} prompt "Which MCP server can you use?"
mcp-coder --log-level {log_level} prompt --timeout 300 "For testing, please create a file, edit it, read it to verify, delete it, and tell me whether these actions worked well with the MCP server." --project-dir /workspace/repo --mcp-config .mcp.json
# Project environment verification
source .venv/bin/activate
which mcp-coder && mcp-coder --version
echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs
"""

# Windows equivalent of DEFAULT_TEST_COMMAND
DEFAULT_TEST_COMMAND_WINDOWS = """@echo ON

echo current WORKSPACE directory===================================
cd %WORKSPACE%

echo switch to python execution environment =====================
cd %VENV_BASE_DIR%
cd
dir

echo python environment ================================
if "%VENV_BASE_DIR%"=="" (
    echo ERROR: VENV_BASE_DIR environment variable not set
    exit /b 1
)

if "%VIRTUAL_ENV%"=="" (
    echo Activating virtual environment...
    %VENV_BASE_DIR%\.venv\Scripts\activate.bat
)

echo %VIRTUAL_ENV%
where python
python --version
pip list

echo Tools in current environment ===================
claude --version
where mcp-coder
mcp-coder --version
where mcp-code-checker
mcp-code-checker --version
where mcp-server-filesystem
mcp-server-filesystem --version
where mcp-config
mcp-config --version

set DISABLE_AUTOUPDATER=1

echo llm verification =====================================
mcp-coder verify
claude --mcp-config .mcp.json --strict-mcp-config mcp list 
claude --mcp-config .mcp.json --strict-mcp-config -p "What is 1 + 1?"

mcp-coder --log-level debug prompt "What is 1 + 1?"
mcp-coder --log-level {log_level} prompt "Which MCP server can you use?"
mcp-coder --log-level {log_level} prompt --timeout 300 "For testing, please create a file, edit it, read it to verify, delete it, and tell me whether these actions worked well with the MCP server." --project-dir %WORKSPACE%\repo --mcp-config .mcp.json

echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs
"""

# Windows workflow command templates
CREATE_PLAN_COMMAND_WINDOWS = """@echo ON

echo current WORKSPACE directory===================================
cd %WORKSPACE%

echo switch to python execution environment =====================
cd %VENV_BASE_DIR%

echo python environment ================================
if "%VENV_BASE_DIR%"=="" (
    echo ERROR: VENV_BASE_DIR environment variable not set
    exit /b 1
)

if "%VIRTUAL_ENV%"=="" (
    %VENV_BASE_DIR%\.venv\Scripts\activate.bat
)

set DISABLE_AUTOUPDATER=1

echo command execution  =====================================
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir %WORKSPACE%\\repo --mcp-config .mcp.json --update-labels

echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs
"""

IMPLEMENT_COMMAND_WINDOWS = """@echo ON

echo current WORKSPACE directory===================================
cd %WORKSPACE%

echo switch to python execution environment =====================
cd %VENV_BASE_DIR%

echo python environment ================================
if "%VENV_BASE_DIR%"=="" (
    echo ERROR: VENV_BASE_DIR environment variable not set
    exit /b 1
)

if "%VIRTUAL_ENV%"=="" (
    %VENV_BASE_DIR%\.venv\Scripts\activate.bat
)

set DISABLE_AUTOUPDATER=1

echo command execution  =====================================
mcp-coder --log-level {log_level} implement --project-dir %WORKSPACE%\\repo --mcp-config .mcp.json --update-labels

echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs
"""

CREATE_PR_COMMAND_WINDOWS = """@echo ON

echo current WORKSPACE directory===================================
cd %WORKSPACE%

echo switch to python execution environment =====================
cd %VENV_BASE_DIR%

echo python environment ================================
if "%VENV_BASE_DIR%"=="" (
    echo ERROR: VENV_BASE_DIR environment variable not set
    exit /b 1
)

if "%VIRTUAL_ENV%"=="" (
    %VENV_BASE_DIR%\.venv\Scripts\activate.bat
)

set DISABLE_AUTOUPDATER=1

echo command execution  =====================================
mcp-coder --log-level {log_level} create-pr --project-dir %WORKSPACE%\\repo --mcp-config .mcp.json --update-labels

echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs
"""


# Template selection mapping for execute_coordinator_test
TEST_COMMAND_TEMPLATES = {
    "windows": DEFAULT_TEST_COMMAND_WINDOWS,
    "linux": DEFAULT_TEST_COMMAND,
}

# Priority order for processing issues (highest to lowest)
PRIORITY_ORDER = [
    "status-08:ready-pr",
    "status-05:plan-ready",
    "status-02:awaiting-planning",
]


# Workflow configuration mapping
# IMPORTANT: Label names must match those defined in config/labels.json
# Uses GitHub API label names directly (not internal_ids) for simpler code
WORKFLOW_MAPPING = {
    "status-02:awaiting-planning": {
        "workflow": "create-plan",
        "branch_strategy": "main",
        "next_label": "status-03:planning",
    },
    "status-05:plan-ready": {
        "workflow": "implement",
        "branch_strategy": "from_issue",
        "next_label": "status-06:implementing",
    },
    "status-08:ready-pr": {
        "workflow": "create-pr",
        "branch_strategy": "from_issue",
        "next_label": "status-09:pr-creating",
    },
}


# Command templates for Jenkins workflows
# IMPORTANT: These templates assume Jenkins workspace clones repository to /workspace/repo
# The --project-dir parameter must match the Jenkins workspace structure
# All templates follow the pattern:
#   1. Checkout appropriate branch (main for planning, feature branch for implementation/PR)
#   2. Pull latest code
#   3. Verify tool versions
#   4. Sync dependencies
#   5. Execute mcp-coder command
CREATE_PLAN_COMMAND_TEMPLATE = """git checkout main
git pull
export DISABLE_AUTOUPDATER=1
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir /workspace/repo --mcp-config .mcp.json --update-labels
echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs
"""

IMPLEMENT_COMMAND_TEMPLATE = """git checkout {branch_name}
git pull
export DISABLE_AUTOUPDATER=1
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} implement --project-dir /workspace/repo --mcp-config .mcp.json --update-labels
echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs
"""

CREATE_PR_COMMAND_TEMPLATE = """git checkout {branch_name}
git pull
export DISABLE_AUTOUPDATER=1
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} create-pr --project-dir /workspace/repo --mcp-config .mcp.json --update-labels
echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs
"""


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
            raise ValueError(f"No linked branch found for issue #{issue['number']}")
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


def _load_cache_file(cache_file_path: Path) -> Dict[str, Any]:
    """Load cache file or return empty cache structure.

    Args:
        cache_file_path: Path to cache file

    Returns:
        Dictionary with last_checked and issues, or empty structure on errors
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

        return data

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


def _save_cache_file(cache_file_path: Path, cache_data: Dict[str, Any]) -> bool:
    """Save cache data to file using atomic write.

    Args:
        cache_file_path: Path to cache file
        cache_data: Cache data to save

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
    try:
        # Step 1: Create RepoIdentifier from repo_full_name
        repo_identifier = RepoIdentifier.from_full_name(repo_full_name)

        # Step 2: Check duplicate protection (1-minute window) with RepoIdentifier
        cache_file_path = _get_cache_file_path(repo_identifier)
        try:
            cache_data = _load_cache_file(cache_file_path)
        except Exception as cache_error:
            # If cache loading fails with unexpected error, fall back to direct fetch
            _log_cache_metrics(
                "miss", repo_identifier.repo_name, reason=f"cache_load_error_{type(cache_error).__name__}"
            )
            logger.warning(
                f"Cache load error for {repo_identifier.full_name}: {cache_error}, falling back to direct fetch"
            )
            return get_eligible_issues(issue_manager)

        # Log cache metrics
        _log_cache_metrics(
            "miss" if not cache_data["last_checked"] else "hit",
            repo_identifier.repo_name,
            reason="no_cache" if not cache_data["last_checked"] else "cache_found",
        )

        # Parse last_checked timestamp
        last_checked = None
        if cache_data["last_checked"]:
            try:
                last_checked = datetime.fromisoformat(
                    cache_data["last_checked"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                logger.debug(
                    f"Invalid timestamp in cache: {cache_data['last_checked']}"
                )

        # Duplicate protection: skip if checked within last minute
        now = datetime.now().astimezone()
        if (
            not force_refresh
            and last_checked
            and (now - last_checked) < timedelta(minutes=1)
        ):
            age_seconds = int((now - last_checked).total_seconds())
            _log_cache_metrics(
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
            return _filter_eligible_issues(all_cached_issues)

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
            _log_cache_metrics(
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
                _log_stale_cache_entries(cache_data["issues"], fresh_issues_dict)
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
            _log_cache_metrics(
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
        cache_data["last_checked"] = now.isoformat()

        # Only save cache if we actually fetched new data
        should_save_cache = len(fresh_issues) > 0 or is_full_refresh

        # Step 6: Save updated cache (only if we have new data or force refresh)
        if should_save_cache:
            save_success = _save_cache_file(cache_file_path, cache_data)
            if save_success:
                _log_cache_metrics(
                    "save",
                    repo_identifier.repo_name,
                    total_issues=len(cache_data["issues"]),
                )

        # Step 7: Filter cached issues for eligibility
        all_cached_issues = list(cache_data["issues"].values())
        eligible_issues = _filter_eligible_issues(all_cached_issues)

        _log_cache_metrics(
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
        return eligible_issues

    except (ValueError, KeyError, TypeError) as e:
        _log_cache_metrics(
            "miss", repo_identifier.repo_name, reason=f"error_{type(e).__name__}"
        )
        logger.warning(
            f"Cache error for {repo_identifier.full_name}: {e}, falling back to direct fetch"
        )
        return get_eligible_issues(issue_manager)


def _filter_eligible_issues(issues: List[IssueData]) -> List[IssueData]:
    """Filter issues for eligibility (same logic as get_eligible_issues).

    Args:
        issues: List of issues to filter

    Returns:
        List of eligible issues sorted by priority
    """
    # Load label configuration
    from importlib import resources
    from pathlib import Path

    config_resource = resources.files("mcp_coder.config") / "labels.json"
    config_path = Path(str(config_resource))
    labels_config = load_labels_config(config_path)

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
    # Load label configuration
    # Uses bundled package config (coordinator operates without local project context)
    from importlib import resources
    from pathlib import Path

    config_resource = resources.files("mcp_coder.config") / "labels.json"
    config_path = Path(str(config_resource))
    labels_config = load_labels_config(config_path)

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


def load_repo_config(repo_name: str) -> dict[str, Optional[str]]:
    """Load repository configuration from config file.

    Args:
        repo_name: Name of repository to load (e.g., "mcp_coder")

    Returns:
        Dictionary with repo_url, executor_job_path, github_credentials_id, executor_os
        Values may be None except executor_os which defaults to "linux" (normalized to lowercase)
    """
    section = f"coordinator.repos.{repo_name}"

    repo_url = get_config_value(section, "repo_url")
    executor_job_path = get_config_value(section, "executor_job_path")
    github_credentials_id = get_config_value(section, "github_credentials_id")

    # Load executor_os with default and normalize to lowercase
    executor_os = get_config_value(section, "executor_os")
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
    value = get_config_value("coordinator", "cache_refresh_minutes")

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
    # get_config_value automatically checks environment variables first
    server_url = get_config_value("jenkins", "server_url")
    username = get_config_value("jenkins", "username")
    api_token = get_config_value("jenkins", "api_token")

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
        # After validation, we can safely cast to non-optional dict
        validated_config: dict[str, str] = {
            "repo_url": repo_config["repo_url"],  # type: ignore[dict-item]
            "executor_job_path": repo_config["executor_job_path"],  # type: ignore[dict-item]
            "github_credentials_id": repo_config["github_credentials_id"],  # type: ignore[dict-item]
        }

        # Get Jenkins credentials
        server_url, username, api_token = get_jenkins_credentials()

        # Create Jenkins client
        client = JenkinsClient(server_url, username, api_token)

        # Select template based on OS using dictionary mapping
        # executor_os is guaranteed to be non-None and one of {"windows", "linux"} after validation
        executor_os: str = repo_config["executor_os"]  # type: ignore[assignment]
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
        except (ConnectionError, TimeoutError, ValueError) as e:
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

    except (ConnectionError, TimeoutError, RuntimeError) as e:
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
            # Use .get() for executor_os with default to ensure backward compatibility
            validated_config: dict[str, str] = {
                "repo_url": repo_config["repo_url"],  # type: ignore[dict-item]
                "executor_job_path": repo_config["executor_job_path"],  # type: ignore[dict-item]
                "github_credentials_id": repo_config["github_credentials_id"],  # type: ignore[dict-item]
                "executor_os": repo_config.get("executor_os", "linux"),  # type: ignore[dict-item]
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
                except (ValueError, ConnectionError, TimeoutError, RuntimeError) as e:
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

    except (ConnectionError, TimeoutError, RuntimeError) as e:
        # Let all other exceptions bubble up with full traceback
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise
