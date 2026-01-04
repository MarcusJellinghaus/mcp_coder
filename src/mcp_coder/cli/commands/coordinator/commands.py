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
from typing import Optional

from ....utils.github_operations.github_utils import RepoIdentifier
from ....utils.github_operations.issue_branch_manager import IssueBranchManager
from ....utils.github_operations.issue_manager import IssueManager
from ....utils.jenkins_operations.client import JenkinsClient
from ....utils.jenkins_operations.models import JobStatus
from ....utils.user_config import (
    create_default_config,
    get_config_file_path,
    load_config,
)
from .core import (
    WORKFLOW_MAPPING,
    _update_issue_labels_in_cache,
    dispatch_workflow,
    get_cache_refresh_minutes,
    get_cached_eligible_issues,
    get_eligible_issues,
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
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
    %VENV_BASE_DIR%\\.venv\\Scripts\\activate.bat
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
mcp-coder --log-level {log_level} prompt --timeout 300 "For testing, please create a file, edit it, read it to verify, delete it, and tell me whether these actions worked well with the MCP server." --project-dir %WORKSPACE%\\repo --mcp-config .mcp.json

echo archive after execution =======================================
dir .mcp-coder\\create_plan_sessions
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
    %VENV_BASE_DIR%\\.venv\\Scripts\\activate.bat
)

set DISABLE_AUTOUPDATER=1

echo command execution  =====================================
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir %WORKSPACE%\\\\repo --mcp-config .mcp.json --update-labels

echo archive after execution =======================================
dir .mcp-coder\\create_plan_sessions
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
    %VENV_BASE_DIR%\\.venv\\Scripts\\activate.bat
)

set DISABLE_AUTOUPDATER=1

echo command execution  =====================================
mcp-coder --log-level {log_level} implement --project-dir %WORKSPACE%\\\\repo --mcp-config .mcp.json --update-labels

echo archive after execution =======================================
dir .mcp-coder\\create_plan_sessions
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
    %VENV_BASE_DIR%\\.venv\\Scripts\\activate.bat
)

set DISABLE_AUTOUPDATER=1

echo command execution  =====================================
mcp-coder --log-level {log_level} create-pr --project-dir %WORKSPACE%\\\\repo --mcp-config .mcp.json --update-labels

echo archive after execution =======================================
dir .mcp-coder\\create_plan_sessions
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

                    # Update cache with new labels immediately after successful dispatch
                    try:
                        _update_issue_labels_in_cache(
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
