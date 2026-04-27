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

# github_operations - verification (re-exported via shim)
_.verify_github
_.CheckResult

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

# mcp_tools_py.py - Convenience function for simple pass/fail checks
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

# ci_results_manager.py - RunData TypedDict fields
_.workflow_path
_.commit_sha

# workflows/vscodeclaude/types.py - VSCodeClaudeSessionStore field
_.last_updated

# workflows/vscodeclaude/types.py - RepoVSCodeClaudeConfig fields
_.setup_commands_windows
_.setup_commands_linux

# llm/types.py - UsageInfo TypedDict field (captured in raw_response but not
# displayed; see pr_info/steps/Decisions.md D9). Only referenced as a kwarg in
# _usage.py, which vulture cannot detect at 60% confidence.
_.cache_creation_input_tokens

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

# test_copilot_integration.py - Fixture triggers skip logic
_.require_copilot_cli

# test_copilot_cli.py - @patch decorator requires accepting the mock parameter
_.mock_settings

# test_commit.py - @patch decorator parameters for push/clipboard tests
_.mock_has_tracking
_.mock_parse_msg
_.mock_clipboard

# test_issue_manager_label_update.py - Fixture used for side effect (patching)
_._mock_git_repo

# test_workspace.py - Fixture used for side effect (monkeypatching get_vscodeclaude_config)
_.mock_vscodeclaude_config

# test_git_tool.py - Fixture used for side effect (patching get_git_diff_for_commit)
_.mock_get_git_diff_for_commit

# conftest.py - Autouse fixture to isolate MLflow artifacts from project root
_.isolate_mlflow_artifacts

# cli/commands/conftest.py - Autouse fixture to mock verify_config
_._mock_verify_config

# cli/commands/conftest.py - Autouse fixture to mock verify_github
_._mock_verify_github

# test_verify_orchestration.py - Autouse fixture to mock verify_github per class
_._mock_github

# test_verify_*.py - Autouse fixture to mock resolve_mcp_config_path
_._mock_resolve_mcp

# test_langchain_integration.py - Module-level pytest marker assignment
_.pytestmark

# langchain/conftest.py - Autouse session fixture for mocking langchain modules
_._mock_langchain_modules

# test_crash_logging.py - Autouse fixture to reset crash_logging module state
_._isolate_crash_logging_state

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

# Exception attribute set on PermissionError for testing - code under test reads this
_.filename

# Mock attribute assignment - simulating Path.rmdir behavior
_.rmdir

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
# FALSE POSITIVES - GitPython Mock Patterns
# =============================================================================
# test_base_branch.py - Mock attributes for GitPython's IterableList dual-access pattern
# These are set on MagicMock objects to simulate repo.heads iteration and indexing
_.__iter__
_.__getitem__
_.__setitem__
_.__enter__
_.__exit__
_.__aenter__
_.__aexit__

# =============================================================================
# FALSE POSITIVES - iCoder TUI (Textual Framework)
# =============================================================================
# Textual framework calls these methods via its component lifecycle and message system.
# They are registered/discovered by the framework, not called directly.

# icoder/core/commands/*.py - Command handlers registered in CommandRegistry
_.handle_clear
_.handle_help
_.handle_info
_.handle_quit
_.handle_color

# icoder/ui/app.py - Textual styles set programmatically
_.border

# icoder/ui/app.py - Textual lifecycle, message handlers, and bindings
_.compose
_.on_mount
_.on_input_area_input_submitted
_.on_text_area_changed
_.BINDINGS
_.action_cancel_stream
_.action_noop

# tests/icoder/test_command_registry.py - Test command handler
_.handle_test

# tests/icoder/test_env_setup.py - Autouse fixtures for env isolation and mocking
_._clear_mcp_env
_._mock_externals

# tests/icoder/conftest.py - Autouse fixture to prevent store_session disk writes
_._no_store_session

# conftest.py - Fixtures for GitHub integration test setup
_.github_test_setup
_.create_github_manager

# workflows/vscodeclaude/types.py - TypedDict field
_.started_at

# test_session_restart_branch_integration.py - Unpacked but unused in test assertion
_.user

