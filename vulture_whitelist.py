"""Vulture whitelist - false positives and intentionally kept code.

This file tells Vulture to ignore certain items that appear unused but are
intentionally kept for:
- API completeness (GitHub operations methods)
- Future use (base class attributes, convenience functions)
- False positives (TypedDict fields, pytest fixtures, argparse patterns)

Format: _.attribute_name (Vulture's attribute-style whitelist syntax)

Review this list periodically - items may become used or truly dead over time.
"""

# =============================================================================
# API COMPLETENESS - GitHub Operations
# =============================================================================
# These methods are tested but not called internally. Kept for complete API.

# issue_manager.py - Issue operations
_.get_issue_events
_.add_comment
_.edit_comment
_.delete_comment
_.close_issue
_.reopen_issue
_.get_available_labels

# pr_manager.py - Pull request operations
_.get_pull_request
_.list_pull_requests
_.close_pull_request
_.repository_name

# ci_results_manager.py - CI status operations
_.get_latest_ci_status
_.get_run_logs

# issue_branch_manager.py - Branch operations
_.delete_linked_branch

# github_utils.py - URL utilities (inverse of parse_github_url)
_.format_github_https_url

# =============================================================================
# API COMPLETENESS - IssueEventType Enum Values
# =============================================================================
# issue_manager.py lines 47-81 - GitHub API event type constants
_.LABELED
_.UNLABELED
_.CLOSED
_.REOPENED
_.ASSIGNED
_.UNASSIGNED
_.MILESTONED
_.DEMILESTONED
_.REFERENCED
_.CROSS_REFERENCED
_.COMMENTED
_.MENTIONED
_.SUBSCRIBED
_.UNSUBSCRIBED
_.RENAMED
_.LOCKED
_.UNLOCKED
_.REVIEW_REQUESTED
_.REVIEW_REQUEST_REMOVED
_.CONVERTED_TO_DRAFT
_.READY_FOR_REVIEW

# =============================================================================
# POTENTIAL FUTURE USE
# =============================================================================

# base_manager.py - Base class attributes for subclasses
_._repo_owner
_._repo_name

# mcp_code_checker.py - Convenience function for simple pass/fail checks
_.has_mypy_errors

# claude_code_api.py - Retry utility for future API retry logic
_._retry_with_backoff

# task_tracker.py - Convenience function for simple yes/no checks
_.has_incomplete_work

# =============================================================================
# FALSE POSITIVES - TypedDict Fields
# =============================================================================
# workflow_constants.py - WorkflowConfig TypedDict fields
_.workflow
_.branch_strategy
_.next_label

# workflows/vscodeclaude/types.py - VSCodeClaudeSessionStore field
_.last_updated

# workflows/vscodeclaude/types.py - RepoVSCodeClaudeConfig fields
_.setup_commands_windows
_.setup_commands_linux

# =============================================================================
# FALSE POSITIVES - Argparse Pattern
# =============================================================================
# main.py - Standard argparse subparser pattern
_.help_parser
_.verify_parser

# =============================================================================
# FALSE POSITIVES - Pytest Fixtures
# =============================================================================
# test_execution_dir_integration.py - Fixture triggers skip logic
_.require_claude_cli

# test_issue_manager_label_update.py - Fixture used for side effect (patching)
_._mock_git_repo

# =============================================================================
# API COMPLETENESS - CommandResult Dataclass Fields
# =============================================================================
# subprocess_runner.py - Fields set but not read; kept for complete result API
_.execution_error
_.runner_type

# =============================================================================
# FALSE POSITIVES - Mock Framework Attributes
# =============================================================================
# unittest.mock sets side_effect to configure mock behavior; framework uses it internally
_.side_effect

# =============================================================================
# FALSE POSITIVES - Additional Test Patterns
# =============================================================================
# Test fixtures, helper functions, and test data that appear unused but are used by pytest
_.temp_log_file
_.isolated_temp_dir
_.session_temp_dir
_.reset_logging
_.cleanup_test_artifacts
_.mock_labels_config
_.git_repo_with_files
_.verify_git_state
_.mock_zip_content
_.mock_label_config
_.mock_git_operations
_.ask_function
_.set_response
_.fake_path
_.ALREADY_FORMATTED_CODE
_.ALREADY_SORTED_IMPORTS
_.some_attr
_.some_attribute
_.custom_field
_.user_id
_.request_id

# =============================================================================
# FALSE POSITIVES - Lazy Import Pattern
# =============================================================================
# workflow_utils/__init__.py - __getattr__ used for lazy imports to avoid circular imports
_.__getattr__

# =============================================================================
# FALSE POSITIVES - Git Operations
# =============================================================================
# repository.py - Variable used in git status parsing
_.index_status
