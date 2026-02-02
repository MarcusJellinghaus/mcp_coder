"""Coordinator CLI commands for automated workflow orchestration."""

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
    "dispatch_workflow",
    "get_cached_eligible_issues",
    "get_eligible_issues",
    "load_repo_config",
    "validate_repo_config",
    "get_jenkins_credentials",
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
    # Internal (kept for compatibility if needed)
    "_filter_eligible_issues",
]
