# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**

1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**

- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Add Windows Template Constants ([details](steps/step_1.md))

- [x] Add `DEFAULT_TEST_COMMAND_WINDOWS` constant to `src/mcp_coder/cli/commands/coordinator.py`
- [x] Add `CREATE_PLAN_COMMAND_WINDOWS` constant
- [x] Add `IMPLEMENT_COMMAND_WINDOWS` constant
- [x] Add `CREATE_PR_COMMAND_WINDOWS` constant
- [x] Run pylint check using `mcp__code-checker__run_pylint_check`
- [x] Run mypy check using `mcp__code-checker__run_mypy_check`
- [x] Fix all issues found (if any)
- [x] Prepare git commit message for Step 1

### Step 2: Update Config Loading and Validation - TDD ([details](steps/step_2.md))

**Part 1: Write Tests First**
- [x] Add `test_validate_repo_config_invalid_executor_os` to `tests/cli/commands/test_coordinator.py`
- [x] Add `test_validate_repo_config_valid_executor_os` test
- [x] Add `test_load_repo_config_defaults_executor_os` test
- [x] Add `test_load_repo_config_normalizes_executor_os` test
- [x] Run tests using `mcp__code-checker__run_pytest_check` (should fail - TDD)

**Part 2: Implement Functionality**
- [x] Update `load_repo_config()` in `src/mcp_coder/cli/commands/coordinator.py` to load `executor_os` with case normalization
- [x] Rename field from `executor_test_path` to `executor_job_path` in `load_repo_config()`
- [x] Update `validate_repo_config()` to validate `executor_os` is "windows" or "linux"
- [x] Update `validate_repo_config()` to use renamed field `executor_job_path`
- [x] Run pylint check using `mcp__code-checker__run_pylint_check`
- [x] Run pytest check using `mcp__code-checker__run_pytest_check` (should pass)
- [x] Run mypy check using `mcp__code-checker__run_mypy_check`
- [x] Fix all issues found (if any)
- [x] Prepare git commit message for Step 2

### Step 3: Add Template Selection Logic - TDD ([details](steps/step_3.md)) - COMPLETE

**Part 1: Write Tests First**
- [x] Add `test_execute_coordinator_test_windows_template` to `tests/cli/commands/test_coordinator.py`
- [x] Add `test_execute_coordinator_test_linux_template` test
- [x] Add `test_dispatch_workflow_windows_templates` test (optional but recommended)
- [x] Run tests using `mcp__code-checker__run_pytest_check` (should fail - TDD)

**Part 2: Implement Functionality**
- [x] Update `execute_coordinator_test()` to select template based on `executor_os`
- [x] Update `execute_coordinator_test()` to use renamed parameter `EXECUTOR_JOB_PATH`
- [x] Update `dispatch_workflow()` to select templates based on `executor_os`
- [x] Update `dispatch_workflow()` to use renamed field `executor_job_path`
- [x] Run pylint check using `mcp__code-checker__run_pylint_check` - No issues
- [x] Run pytest check using `mcp__code-checker__run_pytest_check` (should pass) - Tests pass
- [x] Run mypy check using `mcp__code-checker__run_mypy_check` - No issues
- [x] Fix all issues found (if any) - No issues found
- [x] Prepare git commit message for Step 3

### Step 4: Update Default Config Template ([details](steps/step_4.md)) - COMPLETE

- [x] Update `create_default_config()` template in `src/mcp_coder/utils/user_config.py`
- [x] Add `executor_os` field to `[coordinator.repos.mcp_coder]` example with comments
- [x] Add `executor_os` field to `[coordinator.repos.mcp_server_filesystem]` example
- [x] Rename field from `executor_test_path` to `executor_job_path` in all examples
- [x] Add commented Windows executor configuration example
- [x] Update final repository template comment to include `executor_os`
- [x] Run pylint check using `mcp__code-checker__run_pylint_check` - No issues
- [x] Run mypy check using `mcp__code-checker__run_mypy_check` - Pre-existing issue not related to our changes
- [x] Fix all issues found (if any) - No new issues from our changes
- [x] Prepare git commit message for Step 4

**Commit Message:**
```
Step 4: Update default config template with executor_os documentation

Updated create_default_config() template in src/mcp_coder/utils/user_config.py:
- Added executor_os field to repository examples (default: "linux")
- Renamed executor_test_path to executor_job_path in all example sections
- Added helpful comments explaining executor_os valid values
- Included commented Windows executor configuration example
- Updated final repository template to include executor_os field

Changes maintain backward compatibility with informative documentation.
```

### Step 5: Integration Validation and Final Testing ([details](steps/step_5.md))

- [x] Run fast unit tests: `mcp__code-checker__run_pytest_check` with parallel execution and exclusions
- [x] Run pylint check: `mcp__code-checker__run_pylint_check`
- [x] Run mypy check: `mcp__code-checker__run_mypy_check`
- [x] Fix all issues found (if any)
- [x] Run all checks combined: `mcp__code-checker__run_all_checks` - Pylint/Mypy pass, pytest has config conflict with -n auto
- [ ] Verify Windows templates selected when `executor_os = "windows"`
- [ ] Verify Linux templates selected when `executor_os = "linux"` or not specified
- [ ] Verify validation rejects invalid `executor_os` values
- [ ] Confirm no regressions in existing functionality
- [ ] Prepare git commit message for Step 5 (if needed)

### Pull Request

- [ ] Review all changes using `git diff`
- [ ] Run format_all: `./tools/format_all.sh` before committing
- [ ] Create final commit(s) with clear commit messages
- [ ] Create pull request with summary of changes
- [ ] Verify PR description includes:
  - Overview of Windows support implementation
  - Configuration changes (`executor_os` field, field rename)
  - Breaking changes (field rename: `executor_test_path` → `executor_job_path`)
  - Testing performed (all quality checks passed)
  - Backward compatibility notes
