"""Coordinator CLI commands for automated workflow orchestration."""

# Import from commands module
from .commands import (
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
    execute_coordinator_run,
    execute_coordinator_test,
    format_job_output,
)

# Import from core module
from .core import (  # All private functions for test access
    WORKFLOW_MAPPING,
    CacheData,
    _filter_eligible_issues,
    _get_cache_file_path,
    _load_cache_file,
    _log_cache_metrics,
    _log_stale_cache_entries,
    _save_cache_file,
    _update_issue_labels_in_cache,
    dispatch_workflow,
    get_cache_refresh_minutes,
    get_cached_eligible_issues,
    get_eligible_issues,
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
)

__all__ = [
    # Public CLI interface
    "execute_coordinator_test",
    "execute_coordinator_run",
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
    "_get_cache_file_path",
    "_load_cache_file",
    "_save_cache_file",
    "_update_issue_labels_in_cache",
    "_log_cache_metrics",
    "_log_stale_cache_entries",
]
