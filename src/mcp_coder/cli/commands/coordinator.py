"""Coordinator CLI commands for automated workflow orchestration.

Provides two main commands:
- coordinator test: Trigger Jenkins integration tests for repositories
- coordinator run: Monitor GitHub issues and dispatch workflows based on labels

The coordinator run command automates the issue → plan → implement → PR pipeline
by filtering eligible issues and triggering appropriate Jenkins workflows.
"""

import argparse
import logging
import sys
from typing import Optional
from urllib.parse import quote

from ...utils.github_operations.issue_branch_manager import IssueBranchManager
from ...utils.github_operations.issue_manager import IssueData, IssueManager
from ...utils.github_operations.label_config import load_labels_config
from ...utils.jenkins_operations.client import JenkinsClient
from ...utils.jenkins_operations.models import JobStatus
from ...utils.user_config import (
    create_default_config,
    get_config_file_path,
    get_config_value,
)

logger = logging.getLogger(__name__)


# Default test command for coordinator integration tests
# This comprehensive script verifies the complete environment setup
DEFAULT_TEST_COMMAND = """# Tool verification
which mcp-coder && mcp-coder --version
which mcp-code-checker && mcp-code-checker --help
which mcp-server-filesystem && mcp-server-filesystem --help
mcp-coder verify
# Environment setup
export MCP_CODER_PROJECT_DIR='/workspace/repo'
export MCP_CODER_VENV_DIR='/workspace/.venv'
uv sync --extra dev
# Claude CLI verification
which claude
claude mcp list
claude -p "What is 1 + 1?"
# MCP Coder functionality test
mcp-coder --log-level debug prompt "What is 1 + 1?"
# Project environment verification
source .venv/bin/activate
which mcp-coder && mcp-coder --version
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

echo command execution  =====================================
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir %WORKSPACE%\\repo --mcp-config .mcp.json
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

echo command execution  =====================================
mcp-coder --log-level {log_level} implement --project-dir %WORKSPACE%\\repo --mcp-config .mcp.json
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

echo command execution  =====================================
mcp-coder --log-level {log_level} create-pr --project-dir %WORKSPACE%\\repo --mcp-config .mcp.json
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
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir /workspace/repo --mcp-config /workspace/repo/.mcp.linux.json
"""

IMPLEMENT_COMMAND_TEMPLATE = """git checkout {branch_name}
git pull
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} implement --project-dir /workspace/repo --mcp-config /workspace/repo/.mcp.linux.json
"""

CREATE_PR_COMMAND_TEMPLATE = """git checkout {branch_name}
git pull
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} create-pr --project-dir /workspace/repo --mcp-config /workspace/repo/.mcp.linux.json
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
        test_command = TEST_COMMAND_TEMPLATES[executor_os]

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
            import tomllib

            config_path = get_config_file_path()
            with open(config_path, "rb") as f:
                config_data = tomllib.load(f)

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
            validated_config: dict[str, str] = {
                "repo_url": repo_config["repo_url"],  # type: ignore[dict-item]
                "executor_job_path": repo_config["executor_job_path"],  # type: ignore[dict-item]
                "github_credentials_id": repo_config["github_credentials_id"],  # type: ignore[dict-item]
            }

            # Step 4b: Create managers
            issue_manager = IssueManager(repo_url=validated_config["repo_url"])
            branch_manager = IssueBranchManager(repo_url=validated_config["repo_url"])

            # Step 4c: Get eligible issues
            eligible_issues = get_eligible_issues(issue_manager)
            logger.info(f"Found {len(eligible_issues)} eligible issues")

            # Step 4d: If no issues, continue to next repo
            if not eligible_issues:
                logger.info(f"No eligible issues for {repo_name}")
                continue

            # Step 4e: Dispatch workflows for each eligible issue (fail-fast)
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
