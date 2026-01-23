# MCP Coder Task Tracker

## Overview

This tracks **Feature Implementation** consisting of multiple **Implementation Steps**.

- **Feature**: A complete user-facing capability
- **Implementation Step**: A self-contained unit of work (tests + implementation)

## Status Legend

- [x] = Implementation step complete
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Add Tests for Clean Working Directory Check (TDD)
**Reference**: [pr_info/steps/step_1.md](steps/step_1.md)

- [x] Add `mock_is_working_directory_clean` fixture to `tests/cli/commands/test_set_status.py`
- [x] Implement `test_execute_set_status_dirty_directory_fails` test
- [x] Implement `test_execute_set_status_dirty_directory_with_force_succeeds` test
- [ ] Implement `test_execute_set_status_clean_directory_succeeds` test
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 1

### Step 2: Implement Clean Working Directory Check
**Reference**: [pr_info/steps/step_2.md](steps/step_2.md)

- [ ] Add `--force` argument to `set-status` subparser in `src/mcp_coder/cli/main.py`
- [ ] Add imports (`DEFAULT_IGNORED_BUILD_ARTIFACTS`, `is_working_directory_clean`) to `src/mcp_coder/cli/commands/set_status.py`
- [ ] Implement working directory check logic in `execute_set_status()` function
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 2

### Step 3: Update Slash Command Documentation
**Reference**: [pr_info/steps/step_3.md](steps/step_3.md)

- [ ] Add error handling note to `.claude/commands/plan_approve.md`
- [ ] Add error handling note to `.claude/commands/implementation_needs_rework.md`
- [ ] Add error handling note to `.claude/commands/implementation_approve.md`
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 3

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Verify all tests pass
- [ ] Prepare PR summary with overview of changes
- [ ] Create pull request
