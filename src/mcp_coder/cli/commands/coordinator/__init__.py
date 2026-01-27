"""Coordinator CLI commands for automated workflow orchestration."""

# Import external dependencies for test patching support
# Tests patch these at 'mcp_coder.cli.commands.coordinator.<name>'
from ....utils.github_operations.issue_branch_manager import IssueBranchManager

# Import cache-related functions from issue_cache module
# Only public API is re-exported; private helpers stay internal to issue_cache.py
from ....utils.github_operations.issue_cache import (
    CacheData,
    _update_issue_labels_in_cache,
)
from ....utils.github_operations.issue_manager import IssueManager
from ....utils.github_operations.label_config import load_labels_config
from ....utils.jenkins_operations.client import JenkinsClient
from ....utils.user_config import create_default_config, get_config_values

# Import from command_templates module (constants)
from .command_templates import (
    CREATE_PLAN_COMMAND_TEMPLATE,
    CREATE_PLAN_COMMAND_WINDOWS,
    CREATE_PR_COMMAND_TEMPLATE,
    CREATE_PR_COMMAND_WINDOWS,
    DEFAULT_TEST_COMMAND,
    DEFAULT_TEST_COMMAND_WINDOWS,
    IMPLEMENT_COMMAND_TEMPLATE,
    IMPLEMENT_COMMAND_WINDOWS,
    PRIORITY_ORDER,
    TEST_COMMAND_TEMPLATES,
)

# Import from commands module (CLI entry points)
from .commands import (
    execute_coordinator_run,
    execute_coordinator_test,
    execute_coordinator_vscodeclaude,
    execute_coordinator_vscodeclaude_status,
    format_job_output,
)

# Import from core module
from .core import (
    _filter_eligible_issues,
    dispatch_workflow,
    get_cache_refresh_minutes,
    get_cached_eligible_issues,
    get_eligible_issues,
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
)

# Import from workflow_constants module
from .workflow_constants import WORKFLOW_MAPPING

__all__ = [
    # Public CLI interface
    "execute_coordinator_test",
    "execute_coordinator_run",
    "execute_coordinator_vscodeclaude",
    "execute_coordinator_vscodeclaude_status",
    "format_job_output",
    # Public business logic
    "CacheData",
    "dispatch_workflow",
    "get_cached_eligible_issues",
    "get_eligible_issues",
    "load_repo_config",
    "validate_repo_config",
    "get_jenkins_credentials",
    "get_cache_refresh_minutes",
    # Constants and templates
    "DEFAULT_TEST_COMMAND",
    "DEFAULT_TEST_COMMAND_WINDOWS",
    "CREATE_PLAN_COMMAND_WINDOWS",
    "IMPLEMENT_COMMAND_WINDOWS",
    "CREATE_PR_COMMAND_WINDOWS",
    "TEST_COMMAND_TEMPLATES",
    "CREATE_PLAN_COMMAND_TEMPLATE",
    "IMPLEMENT_COMMAND_TEMPLATE",
    "CREATE_PR_COMMAND_TEMPLATE",
    "PRIORITY_ORDER",
    "WORKFLOW_MAPPING",
    # Private functions (for testing)
    "_filter_eligible_issues",
    "_update_issue_labels_in_cache",
    # External dependencies (for test patching)
    "create_default_config",
    "get_config_values",
    "load_labels_config",
    "JenkinsClient",
    "IssueManager",
    "IssueBranchManager",
]
