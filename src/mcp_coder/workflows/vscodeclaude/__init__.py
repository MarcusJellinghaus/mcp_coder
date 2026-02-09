"""VSCodeClaude session management utilities.

This module provides utilities for managing VSCode/Claude Code sessions
for interactive workflow stages.
"""

# Cleanup
from .cleanup import (
    cleanup_stale_sessions,
    delete_session_folder,
    get_stale_sessions,
)

# Configuration
from .config import (
    get_github_username,
    load_repo_vscodeclaude_config,
    load_vscodeclaude_config,
    sanitize_folder_name,
)

# Issue filtering
from .issues import (
    _filter_eligible_vscodeclaude_issues,
    get_cached_eligible_vscodeclaude_issues,
    get_eligible_vscodeclaude_issues,
    get_human_action_labels,
    get_linked_branch_for_issue,
)

# Orchestration
from .orchestrator import (
    get_stage_display_name,
    handle_pr_created_issues,
    launch_vscode,
    prepare_and_launch_session,
    process_eligible_issues,
    restart_closed_sessions,
    truncate_title,
)

# Session management
from .sessions import (
    add_session,
    check_vscode_running,
    clear_vscode_process_cache,
    clear_vscode_window_cache,
    get_active_session_count,
    get_session_for_issue,
    get_sessions_file_path,
    is_vscode_open_for_folder,
    is_vscode_window_open_for_folder,
    load_sessions,
    remove_session,
    save_sessions,
    update_session_pid,
)

# Status
from .status import (
    check_folder_dirty,
    display_status_table,
    get_folder_git_status,
    get_issue_current_status,
    get_next_action,
    is_issue_closed,
    is_session_stale,
)

# Types and constants
from .types import (
    DEFAULT_MAX_SESSIONS,
    DEFAULT_PROMPT_TIMEOUT,
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
    VSCodeClaudeSession,
    VSCodeClaudeSessionStore,
)

# Workspace setup
from .workspace import (
    create_startup_script,
    create_status_file,
    create_vscode_task,
    create_working_folder,
    create_workspace_file,
    get_working_folder_path,
    run_setup_commands,
    setup_git_repo,
    update_gitignore,
    validate_mcp_json,
    validate_setup_commands,
)

__all__ = [
    # Types
    "VSCodeClaudeSession",
    "VSCodeClaudeSessionStore",
    "VSCodeClaudeConfig",
    "RepoVSCodeClaudeConfig",
    # Constants
    "DEFAULT_MAX_SESSIONS",
    "DEFAULT_PROMPT_TIMEOUT",
    # Session management
    "get_sessions_file_path",
    "load_sessions",
    "save_sessions",
    "check_vscode_running",
    "clear_vscode_process_cache",
    "clear_vscode_window_cache",
    "is_vscode_open_for_folder",
    "is_vscode_window_open_for_folder",
    "get_session_for_issue",
    "add_session",
    "remove_session",
    "get_active_session_count",
    "update_session_pid",
    # Configuration
    "load_vscodeclaude_config",
    "load_repo_vscodeclaude_config",
    "get_github_username",
    "sanitize_folder_name",
    # Issue filtering
    "get_human_action_labels",
    "get_eligible_vscodeclaude_issues",
    "get_cached_eligible_vscodeclaude_issues",
    "_filter_eligible_vscodeclaude_issues",
    "get_linked_branch_for_issue",
    # Workspace setup
    "get_working_folder_path",
    "create_working_folder",
    "setup_git_repo",
    "validate_mcp_json",
    "validate_setup_commands",
    "run_setup_commands",
    "update_gitignore",
    "create_workspace_file",
    "create_startup_script",
    "create_vscode_task",
    "create_status_file",
    # Orchestration
    "launch_vscode",
    "get_stage_display_name",
    "truncate_title",
    "prepare_and_launch_session",
    "process_eligible_issues",
    "restart_closed_sessions",
    "handle_pr_created_issues",
    # Status
    "get_issue_current_status",
    "is_issue_closed",
    "is_session_stale",
    "check_folder_dirty",
    "get_folder_git_status",
    "get_next_action",
    "display_status_table",
    # Cleanup
    "get_stale_sessions",
    "delete_session_folder",
    "cleanup_stale_sessions",
]
