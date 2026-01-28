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
[ ] Add stale check to restart_closed_sessions() - skip sessions where issue status changed
[ ] Add validation to _get_repo_full_name() - raise ValueError if repo URL cannot be parsed
[ ] Remove unused issue_manager parameter from handle_pr_created_issues()
[ ] Remove redundant import json from test method
[ ] Remove empty TestIntegration class from tests
[ ] Standardize type hints to modern Python 3.9+ syntax
[ ] Run pylint on Step 10 code and fix all issues
[ ] Run pytest on Step 10 tests and ensure all pass
[ ] Run mypy on Step 10 code and fix all type issues
[ ] Prepare git commit message for Step 10

## Pull Request
[x] Review all implementation steps for completeness
[ ] Run full test suite and ensure all tests pass
[ ] Run full linting suite and ensure no issues
[ ] Prepare comprehensive PR summary
[ ] Create pull request
