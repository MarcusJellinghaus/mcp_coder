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

### Step 1: Create Unit Tests for `set_status` Command
**Reference:** [step_1.md](steps/step_1.md)

- [x] Create `tests/cli/commands/test_set_status.py` with unit tests
- [x] Implement `TestSetStatusHelpers` test class (validation, config loading)
- [x] Implement `TestComputeNewLabels` test class (label computation logic)
- [x] Implement `TestExecuteSetStatus` test class (CLI execute function)
- [x] Run pylint and fix any issues
- [x] Run pytest and verify tests are discoverable (expected to fail until Step 2)
- [x] Run mypy and fix any type issues
- [x] Prepare git commit message for Step 1

---

### Step 2: Implement `set_status` Command Module
**Reference:** [step_2.md](steps/step_2.md)

- [x] Create `src/mcp_coder/cli/commands/set_status.py`
- [x] Implement `get_status_labels_from_config()` function
- [x] Implement `validate_status_label()` function
- [x] Implement `compute_new_labels()` function
- [x] Implement `execute_set_status()` function with error handling
- [x] Run pylint and fix any issues
- [x] Run pytest and verify all Step 1 tests pass
- [x] Run mypy and fix any type issues
- [x] Prepare git commit message for Step 2

---

### Step 3: Register Command in CLI Main
**Reference:** [step_3.md](steps/step_3.md)

- [x] Add import for `execute_set_status` in `src/mcp_coder/cli/main.py`
- [x] Implement `_build_set_status_epilog()` helper function
- [x] Add `set-status` subparser with arguments in `create_parser()`
- [x] Add command routing in `main()` function
- [x] Run pylint and fix any issues
- [x] Run pytest and verify all tests pass
- [x] Run mypy and fix any type issues
- [x] Verify `mcp-coder set-status --help` displays correctly
- [x] Prepare git commit message for Step 3

---

### Step 4: Create Slash Command Files
**Reference:** [step_4.md](steps/step_4.md)

- [x] Create `.claude/commands/plan_approve.md`
- [x] Create `.claude/commands/implementation_approve.md`
- [x] Create `.claude/commands/implementation_needs_rework.md`
- [x] Run pylint and fix any issues (if applicable)
- [x] Run pytest and verify all tests pass
- [x] Run mypy and fix any type issues (if applicable)
- [x] Prepare git commit message for Step 4

---

### Step 5: Code Review Refactoring
**Reference:** [step_5.md](steps/step_5.md)

- [x] Remove commented-out imports and move imports to top of `test_set_status.py`
- [x] Simplify `full_labels_config` fixture to load from `labels_config_path`
- [x] Move `_build_set_status_epilog()` from `main.py` to `set_status.py`
- [x] Remove unused imports from `main.py`
- [x] Update `main.py` to import `build_set_status_epilog` from `set_status`
- [x] Update `/implementation_needs_rework.md` description with workflow context
- [x] Rename `implementation_tasks.md` to `implementation_new_tasks.md`
- [x] Run pylint and fix any issues
- [x] Run pytest and verify all tests pass
- [x] Run mypy and fix any type issues
- [x] Prepare git commit message for Step 5

---

### Step 6: Update DEVELOPMENT_PROCESS.md
**Reference:** [step_6.md](steps/step_6.md)

- [ ] Add `/plan_approve` to Plan Review workflow section
- [ ] Add `/implementation_approve` to Code Review workflow section
- [ ] Update "Major Issues Found" section with full rework workflow
- [ ] Add Slash Command Quick Reference table
- [ ] Update all references from `/implementation_tasks` to `/implementation_new_tasks`
- [ ] Verify all slash command links are valid
- [ ] Prepare git commit message for Step 6

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Run full test suite and verify all tests pass
- [ ] Run full quality checks (pylint, mypy)
- [ ] Verify CLI command works end-to-end
- [ ] Verify slash commands are recognized
- [ ] Prepare PR summary with changes overview
- [ ] Create pull request
