# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** for Issue #75: Base Branch Support for Issues.

---

## Tasks

### Step 1: Dependencies & Configuration Types
[x] Add psutil dependency to pyproject.toml
[x] Create src/mcp_coder/cli/commands/coordinator/vscodeclaude.py with TypedDict definitions
[ ] Create tests/cli/commands/coordinator/test_vscodeclaude.py with type tests
[ ] Run pylint on Step 1 code and fix all issues
[ ] Run pytest on Step 1 tests and ensure all pass
[ ] Run mypy on Step 1 code and fix all type issues
[ ] Prepare git commit message for Step 1

### Step 2: Template Strings
[ ] Create src/mcp_coder/cli/commands/coordinator/vscodeclaude_templates.py
[ ] Add template tests to test_vscodeclaude.py
[ ] Run pylint on Step 2 code and fix all issues
[ ] Run pytest on Step 2 tests and ensure all pass
[ ] Run mypy on Step 2 code and fix all type issues
[ ] Prepare git commit message for Step 2

### Step 3: Session Management
[ ] Add session management functions to vscodeclaude.py
[ ] Add session management tests to test_vscodeclaude.py
[ ] Run pylint on Step 3 code and fix all issues
[ ] Run pytest on Step 3 tests and ensure all pass
[ ] Run mypy on Step 3 code and fix all type issues
[ ] Prepare git commit message for Step 3

### Step 4: Issue Selection & Configuration
[ ] Add configuration and issue filtering functions to vscodeclaude.py
[ ] Add configuration and filtering tests to test_vscodeclaude.py
[ ] Run pylint on Step 4 code and fix all issues
[ ] Run pytest on Step 4 tests and ensure all pass
[ ] Run mypy on Step 4 code and fix all type issues
[ ] Prepare git commit message for Step 4

### Step 5: Workspace Setup
[ ] Add workspace setup functions to vscodeclaude.py
[ ] Add workspace setup tests to test_vscodeclaude.py
[ ] Run pylint on Step 5 code and fix all issues
[ ] Run pytest on Step 5 tests and ensure all pass
[ ] Run mypy on Step 5 code and fix all type issues
[ ] Prepare git commit message for Step 5

### Step 6: VSCode Launch & Session Orchestration
[ ] Add launch and orchestration functions to vscodeclaude.py
[ ] Add launch tests to test_vscodeclaude.py
[ ] Run pylint on Step 6 code and fix all issues
[ ] Run pytest on Step 6 tests and ensure all pass
[ ] Run mypy on Step 6 code and fix all type issues
[ ] Prepare git commit message for Step 6

### Step 7: CLI Integration
[ ] Add vscodeclaude parser to src/mcp_coder/cli/main.py
[ ] Add command handlers to src/mcp_coder/cli/commands/coordinator/commands.py
[ ] Update src/mcp_coder/cli/commands/coordinator/__init__.py exports
[ ] Add CLI tests to test_vscodeclaude.py
[ ] Run pylint on Step 7 code and fix all issues
[ ] Run pytest on Step 7 tests and ensure all pass
[ ] Run mypy on Step 7 code and fix all type issues
[ ] Prepare git commit message for Step 7

### Step 8: Status Display & Cleanup
[ ] Add status and cleanup functions to vscodeclaude.py
[ ] Add status and cleanup tests to test_vscodeclaude.py
[ ] Run pylint on Step 8 code and fix all issues
[ ] Run pytest on Step 8 tests and ensure all pass
[ ] Run mypy on Step 8 code and fix all type issues
[ ] Prepare git commit message for Step 8

## Pull Request
[ ] Review all implementation steps for completeness
[ ] Run full test suite and ensure all tests pass
[ ] Run full linting suite and ensure no issues
[ ] Prepare comprehensive PR summary
[ ] Create pull request