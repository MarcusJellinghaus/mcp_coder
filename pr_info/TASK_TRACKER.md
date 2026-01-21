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

- [ ] Create `tests/cli/commands/test_set_status.py` with unit tests
- [ ] Implement `TestSetStatusHelpers` test class (validation, config loading)
- [ ] Implement `TestComputeNewLabels` test class (label computation logic)
- [ ] Implement `TestExecuteSetStatus` test class (CLI execute function)
- [ ] Run pylint and fix any issues
- [ ] Run pytest and verify tests are discoverable (expected to fail until Step 2)
- [ ] Run mypy and fix any type issues
- [ ] Prepare git commit message for Step 1

---

### Step 2: Implement `set_status` Command Module
**Reference:** [step_2.md](steps/step_2.md)

- [ ] Create `src/mcp_coder/cli/commands/set_status.py`
- [ ] Implement `get_status_labels_from_config()` function
- [ ] Implement `validate_status_label()` function
- [ ] Implement `compute_new_labels()` function
- [ ] Implement `execute_set_status()` function with error handling
- [ ] Run pylint and fix any issues
- [ ] Run pytest and verify all Step 1 tests pass
- [ ] Run mypy and fix any type issues
- [ ] Prepare git commit message for Step 2

---

### Step 3: Register Command in CLI Main
**Reference:** [step_3.md](steps/step_3.md)

- [ ] Add import for `execute_set_status` in `src/mcp_coder/cli/main.py`
- [ ] Implement `_build_set_status_epilog()` helper function
- [ ] Add `set-status` subparser with arguments in `create_parser()`
- [ ] Add command routing in `main()` function
- [ ] Run pylint and fix any issues
- [ ] Run pytest and verify all tests pass
- [ ] Run mypy and fix any type issues
- [ ] Verify `mcp-coder set-status --help` displays correctly
- [ ] Prepare git commit message for Step 3

---

### Step 4: Create Slash Command Files
**Reference:** [step_4.md](steps/step_4.md)

- [ ] Create `.claude/commands/plan_approve.md`
- [ ] Create `.claude/commands/implementation_approve.md`
- [ ] Create `.claude/commands/implementation_needs_rework.md`
- [ ] Run pylint and fix any issues (if applicable)
- [ ] Run pytest and verify all tests pass
- [ ] Run mypy and fix any type issues (if applicable)
- [ ] Prepare git commit message for Step 4

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Run full test suite and verify all tests pass
- [ ] Run full quality checks (pylint, mypy)
- [ ] Verify CLI command works end-to-end
- [ ] Verify slash commands are recognized
- [ ] Prepare PR summary with changes overview
- [ ] Create pull request
