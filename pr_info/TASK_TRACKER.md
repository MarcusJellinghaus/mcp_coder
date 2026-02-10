# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Add `status_requires_linked_branch()` Helper
- [x] Implement `status_requires_linked_branch()` function in `issues.py` ([step_1.md](./steps/step_1.md))
- [x] Add tests for `status_requires_linked_branch()` in `test_issues.py`
- [x] Run pylint and fix any issues
- [x] Run pytest and verify all tests pass
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 1

### Step 2: Add `skip_reason` Parameter to `get_next_action()`
- [x] Add `skip_reason` parameter to `get_next_action()` in `status.py` ([step_2.md](./steps/step_2.md))
- [x] Add tests for `skip_reason` parameter in `test_next_action.py`
- [x] Run pylint and fix any issues
- [x] Run pytest and verify all tests pass
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 2

### Step 3: Add `_prepare_restart_branch()` Helper
- [x] Implement `BranchPrepResult` NamedTuple in `orchestrator.py` ([step_3.md](./steps/step_3.md))
- [x] Implement `_prepare_restart_branch()` function in `orchestrator.py`
- [x] Add tests for `_prepare_restart_branch()` in `test_orchestrator_sessions.py`
- [x] Run pylint and fix any issues
- [x] Run pytest and verify all tests pass
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 3

### Step 4: Modify `process_eligible_issues()` for Branch-Aware Launch
- [x] Modify `process_eligible_issues()` to enforce linked branch requirements ([step_4.md](./steps/step_4.md))
- [x] Add tests for branch requirement enforcement in `test_orchestrator_launch.py`
- [x] Run pylint and fix any issues
- [x] Run pytest and verify all tests pass
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 4

### Step 5: Modify `restart_closed_sessions()` for Branch-Aware Restart
- [x] Modify `restart_closed_sessions()` to use `_prepare_restart_branch()` ([step_5.md](./steps/step_5.md))
- [x] Add tests for branch handling in restart in `test_orchestrator_sessions.py`
- [x] Run pylint and fix any issues
- [x] Run pytest and verify all tests pass
- [x] Run mypy and fix any type errors
- [x] Prepare git commit message for Step 5

### Step 6: Update `display_status_table()` for New Indicators
- [ ] Add `issues_without_branch` parameter to `display_status_table()` ([step_6.md](./steps/step_6.md))
- [ ] Update display logic to show `→ Needs branch` indicator
- [ ] Refactor CLI to use `display_status_table()` from `status.py`
- [ ] Add tests for branch-related indicators in `test_status_display.py`
- [ ] Run pylint and fix any issues
- [ ] Run pytest and verify all tests pass
- [ ] Run mypy and fix any type errors
- [ ] Prepare git commit message for Step 6

### Step 7: Update Module Docstring and Integration Testing
- [ ] Update `orchestrator.py` module docstring with branch handling documentation ([step_7.md](./steps/step_7.md))
- [ ] Add integration tests for full session lifecycle
- [ ] Run pylint and fix any issues
- [ ] Run pytest and verify all tests pass
- [ ] Run mypy and fix any type errors
- [ ] Prepare git commit message for Step 7

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Run full test suite (`pytest tests/workflows/vscodeclaude/ -v`)
- [ ] Run all quality checks (pylint, pytest, mypy)
- [ ] Verify all acceptance criteria from summary.md are met
- [ ] Create pull request with summary of changes
