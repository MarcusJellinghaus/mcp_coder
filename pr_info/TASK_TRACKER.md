# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** for Issue #75: Base Branch Support for Issues.

---

## Tasks

### Step 1: Dependencies & Configuration Types
[x] Add psutil dependency to pyproject.toml
[x] Create src/mcp_coder/cli/commands/coordinator/vscodeclaude.py with TypedDict definitions
[x] Create tests/cli/commands/coordinator/test_vscodeclaude.py with type tests
[x] Run pylint on Step 1 code and fix all issues
[x] Run pytest on Step 1 tests and ensure all pass
[x] Run mypy on Step 1 code and fix all type issues
[x] Prepare git commit message for Step 1

### Step 2: Template Strings
[x] Create src/mcp_coder/cli/commands/coordinator/vscodeclaude_templates.py
[x] Add template tests to test_vscodeclaude.py
[x] Run pylint on Step 2 code and fix all issues
[x] Run pytest on Step 2 tests and ensure all pass
[x] Run mypy on Step 2 code and fix all type issues
[x] Prepare git commit message for Step 2

### Step 3: Session Management
[x] Add session management functions to vscodeclaude.py
[x] Add session management tests to test_vscodeclaude.py
[x] Run pylint on Step 3 code and fix all issues
[x] Run pytest on Step 3 tests and ensure all pass
[x] Run mypy on Step 3 code and fix all type issues
[x] Prepare git commit message for Step 3

### Step 4: Issue Selection & Configuration
[x] Add configuration and issue filtering functions to vscodeclaude.py
[x] Add configuration and filtering tests to test_vscodeclaude.py
[x] Run pylint on Step 4 code and fix all issues
[x] Run pytest on Step 4 tests and ensure all pass
[x] Run mypy on Step 4 code and fix all type issues
[x] Prepare git commit message for Step 4

### Step 5: Workspace Setup
[x] Add workspace setup functions to vscodeclaude.py
[x] Add workspace setup tests to test_vscodeclaude.py
[x] Run pylint on Step 5 code and fix all issues
[x] Run pytest on Step 5 tests and ensure all pass
[x] Run mypy on Step 5 code and fix all type issues
[x] Prepare git commit message for Step 5

### Step 6: VSCode Launch & Session Orchestration
[x] Add launch and orchestration functions to vscodeclaude.py
[x] Add launch tests to test_vscodeclaude.py
[x] Run pylint on Step 6 code and fix all issues
[x] Run pytest on Step 6 tests and ensure all pass
[x] Run mypy on Step 6 code and fix all type issues
[x] Prepare git commit message for Step 6

### Step 7: CLI Integration
[x] Add vscodeclaude parser to src/mcp_coder/cli/main.py
[x] Add command handlers to src/mcp_coder/cli/commands/coordinator/commands.py
[x] Update src/mcp_coder/cli/commands/coordinator/__init__.py exports
[x] Add CLI tests to test_vscodeclaude.py
[x] Run pylint on Step 7 code and fix all issues
[x] Run pytest on Step 7 tests and ensure all pass
[x] Run mypy on Step 7 code and fix all type issues
[x] Prepare git commit message for Step 7

### Step 8: Status Display & Cleanup
[x] Add status and cleanup functions to vscodeclaude.py
[x] Add status and cleanup tests to test_vscodeclaude.py
[x] Run pylint on Step 8 code and fix all issues
[x] Run pytest on Step 8 tests and ensure all pass
[x] Run mypy on Step 8 code and fix all type issues
[x] Prepare git commit message for Step 8

### Step 9: Code Review Fixes (Round 1)
[x] Fix IssueManager/IssueBranchManager instantiation (use repo_url keyword argument)
[x] Remove duplicated _cleanup_stale_sessions() from commands.py
[x] Replace module-wide mypy override with specific type ignore comments
[x] Run pylint on Step 9 code and fix all issues
[x] Run pytest on Step 9 tests and ensure all pass
[x] Run mypy on Step 9 code and fix all type issues
[x] Prepare git commit message for Step 9

### Step 10: Code Review Fixes (Round 2)
[x] Add stale check to restart_closed_sessions() - skip sessions where issue status changed
[x] Add validation to _get_repo_full_name() - raise ValueError if repo URL cannot be parsed
[x] Remove unused issue_manager parameter from handle_pr_created_issues()
[x] Remove redundant import json from test method
[x] Remove empty TestIntegration class from tests
[x] Standardize type hints to modern Python 3.9+ syntax
[x] Run pylint on Step 10 code and fix all issues
[x] Run pytest on Step 10 tests and ensure all pass
[x] Run mypy on Step 10 code and fix all type issues
[x] Prepare git commit message for Step 10

### Step 11: Test Refactoring
[x] Create tests/utils/vscodeclaude/ directory structure
[x] Split test_vscodeclaude.py into module-specific test files
[x] Update imports to new utils module paths
[x] Fix monkeypatch path in test_process_eligible_issues_respects_max_sessions
[x] Delete original monolithic test file
[x] Run pylint on Step 11 code and fix all issues
[x] Run pytest on Step 11 tests and ensure all pass
[x] Run mypy on Step 11 code and fix all type issues
[x] Prepare git commit message for Step 11

### Step 12: Cache Integration (Performance Optimization)
[x] Add `_filter_eligible_vscodeclaude_issues()` helper to issues.py
[x] Add `get_cached_eligible_vscodeclaude_issues()` wrapper to issues.py
[x] Update process_eligible_issues() to use cache
[x] Update execute_coordinator_vscodeclaude() to fetch cache once per repo
[x] Update __init__.py exports
[x] Add tests for cache integration
[x] Run pylint on Step 12 code and fix all issues
[x] Run pytest on Step 12 tests and ensure all pass
[x] Run mypy on Step 12 code and fix all type issues
[x] Prepare git commit message for Step 12

### Step 13: Pass Cached Issues to Staleness Checks
[x] Refactor get_issue_current_status() to accept cached_issues parameter
[x] Refactor is_session_stale() to accept cached_issues parameter
[x] Refactor is_issue_closed() to accept cached_issues parameter
[x] Refactor restart_closed_sessions() to accept cached_issues_by_repo parameter
[x] Update display_status_table() to pass cached issues
[x] Update callers in commands.py to pass cache
[x] Add tests for cache-aware functions
[x] Run pylint on Step 13 code and fix all issues
[x] Run pytest on Step 13 tests and ensure all pass
[x] Run mypy on Step 13 code and fix all type issues
[x] Prepare git commit message for Step 13

### Step 14: Add `--output-format session-id` to Prompt Command
[x] Add session-id output format to prompt.py execute_prompt()
[x] Update help text in main.py for output-format argument
[x] Add tests for session-id format in test_prompt.py
[x] Run pylint on Step 14 code and fix all issues
[x] Run pytest on Step 14 tests and ensure all pass
[x] Run mypy on Step 14 code and fix all type issues
[x] Prepare git commit message for Step 14

### Step 15: Update VSCodeClaude Templates V2 (Windows)
[x] Add VENV_SECTION_WINDOWS template
[x] Add AUTOMATED_SECTION_WINDOWS_V2 template (mcp-coder prompt)
[x] Add DISCUSSION_SECTION_WINDOWS template
[x] Add INTERACTIVE_SECTION_WINDOWS_V2 template
[x] Add STARTUP_SCRIPT_WINDOWS_V2 template
[x] Add INTERVENTION_SCRIPT_WINDOWS_V2 template
[x] Add tests for V2 templates in test_vscodeclaude_cli.py
[x] Run pylint on Step 15 code and fix all issues
[x] Run pytest on Step 15 tests and ensure all pass
[x] Run mypy on Step 15 code and fix all type issues
[x] Prepare git commit message for Step 15

### Step 16: Update Workspace Setup for V2 Templates
[ ] Add DEFAULT_PROMPT_TIMEOUT constant to types.py
[ ] Update create_startup_script() to use V2 templates
[ ] Add timeout parameter to create_startup_script()
[ ] Update callers in orchestrator.py to pass timeout
[ ] Add tests for V2 script generation in test_workspace.py
[ ] Run pylint on Step 16 code and fix all issues
[ ] Run pytest on Step 16 tests and ensure all pass
[ ] Run mypy on Step 16 code and fix all type issues
[ ] Prepare git commit message for Step 16

## Pull Request
[x] Review all implementation steps for completeness
[ ] Run full test suite and ensure all tests pass
[ ] Run full linting suite and ensure no issues
[ ] Prepare comprehensive PR summary
[ ] Create pull request
