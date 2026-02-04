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

### Step 1: Config Update and Ignore-Label Helper Functions
- [ ] Update `labels.json` - add `blocked` and `wait` to `ignore_labels` array
- [ ] Implement `get_ignore_labels()` function in `issues.py`
- [ ] Implement `get_matching_ignore_label()` function in `issues.py`
- [ ] Write tests for `get_ignore_labels()` in `test_issues.py`
- [ ] Write tests for `get_matching_ignore_label()` in `test_issues.py`
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 1

### Step 2: Session Status Update Helper
- [ ] Implement `update_session_status()` function in `sessions.py`
- [ ] Write tests for `update_session_status()` in `test_sessions.py`
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 2

### Step 3: Add Blocked Label Support to get_next_action()
- [ ] Modify `get_next_action()` signature to add `blocked_label` parameter in `status.py`
- [ ] Implement blocked label logic in `get_next_action()`
- [ ] Write tests for blocked label behavior in `test_status.py`
- [ ] Verify existing tests still pass (backward compatibility)
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 3

### Step 4: Fix Cleanup Order and Include Blocked Sessions
- [ ] Reorder cleanup and restart operations in `commands.py` (cleanup before restart)
- [ ] Update `cleanup_stale_sessions()` to accept cache parameter in `cleanup.py`
- [ ] Update `get_stale_sessions()` to include blocked sessions in `cleanup.py`
- [ ] Update dry-run message format in `cleanup_stale_sessions()`
- [ ] Write tests for blocked session cleanup in `test_cleanup.py`
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 4

### Step 5: Skip Blocked Issues in Restart and Update Status
- [ ] Modify `restart_closed_sessions()` to skip blocked issues in `orchestrator.py`
- [ ] Add status update logic when restarting in `orchestrator.py`
- [ ] Write tests for blocked issue skip in `test_orchestrator_sessions.py`
- [ ] Write tests for status update on restart in `test_orchestrator_sessions.py`
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 5

### Step 6: Fix Status Command Display
- [ ] Modify `_build_cached_issues_by_repo()` to return failed repos in `commands.py`
- [ ] Update `execute_coordinator_vscodeclaude_status()` to use current GitHub status
- [ ] Add `(?)` indicator for API failures (per-repo)
- [ ] Add session status update when changed
- [ ] Add blocked label support to status display
- [ ] Write tests for current GitHub status display in `test_commands.py`
- [ ] Write tests for API failure handling in `test_commands.py`
- [ ] Write tests for blocked display in `test_commands.py`
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 6

### Step 7: Cleanup - Remove Duplicate _get_issue_status()
- [ ] Add import for `get_issue_status` from `helpers.py` in `status.py`
- [ ] Replace usage of `_get_issue_status()` with `get_issue_status()`
- [ ] Remove `_get_issue_status()` function from `status.py`
- [ ] Verify tests still pass
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 7

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Run full test suite and verify all tests pass
- [ ] Run final quality checks (pylint, pytest, mypy)
- [ ] Create PR summary with all changes
- [ ] Submit PR for review
