# Task Status Tracker

## Issue: #357 - Add architectural constraint - subprocess should only get started from subprocess wrapper

## Instructions for LLM

Read `pr_info/steps/summary.md` for architectural context before implementing any step.
Each step file contains detailed WHERE/WHAT/HOW specifications.

---

## Tasks

### Step 1: Re-export Exceptions and Migrate Production Code
- [ ] Task 1.1: Add exception re-exports to `subprocess_runner.py`
- [ ] Task 1.2: Migrate `commits.py` to use `execute_command()`
- [ ] Task 1.3: Remove fallback subprocess calls from `claude_executable_finder.py`
- [ ] Task 1.4: Change exception imports in `task_processing.py`
- [ ] Task 1.5: Change exception imports in `claude_code_api.py`
- [ ] Task 1.6: Change exception imports in `claude_code_cli.py`
- [ ] Task 1.7: Change exception imports in `black_formatter.py`
- [ ] Task 1.8: Change exception imports in `isort_formatter.py`
- [ ] Run tests for affected modules

### Step 2: Migrate Test Files and Add Import-Linter Contract
- [ ] Task 2.1: Migrate `test_issue_manager_label_update.py` to use `execute_command()`
- [ ] Task 2.2: Remove unused subprocess import from `test_create_pr_integration.py`
- [ ] Task 2.2b: Remove unused subprocess import from `test_main.py`
- [ ] Task 2.3: Delete `test_subprocess_encoding_directly` test
- [ ] Task 2.4: Change exception imports in `test_claude_code_api.py`
- [ ] Task 2.5: Change exception imports in `test_claude_code_api_error_handling.py`
- [ ] Task 2.6: Change exception imports in `test_claude_code_cli.py`
- [ ] Task 2.7: Add subprocess isolation contract to `.importlinter`
- [ ] Run `lint-imports` to verify contract
- [ ] Run full test suite
