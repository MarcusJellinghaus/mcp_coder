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

### Step 1: Add `get_folder_git_status()` Function with Tests
See [step_1.md](./steps/step_1.md) for details.

- [x] Write tests for `get_folder_git_status()` in `tests/workflows/vscodeclaude/test_status.py`
- [x] Implement `get_folder_git_status()` function in `src/mcp_coder/workflows/vscodeclaude/status.py`
- [x] Export function in `src/mcp_coder/workflows/vscodeclaude/__init__.py`
- [x] Run quality checks (pylint, pytest, mypy) and fix any issues
- [x] Prepare git commit message for Step 1

### Step 2: Update Status Display and `check_folder_dirty()`
See [step_2.md](./steps/step_2.md) for details.

- [ ] Update `check_folder_dirty()` to use `get_folder_git_status()` internally
- [ ] Update import in `src/mcp_coder/cli/commands/coordinator/commands.py`
- [ ] Update status display in `execute_coordinator_vscodeclaude_status()` to use `get_folder_git_status()`
- [ ] Verify existing `check_folder_dirty()` tests still pass
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 2

### Step 3: Update Cleanup Logic for All Status Cases
See [step_3.md](./steps/step_3.md) for details.

- [ ] Update `get_stale_sessions()` return type to include status string
- [ ] Update `cleanup_stale_sessions()` to handle all status cases (Clean, Dirty, Missing, No Git, Error)
- [ ] Update import in `src/mcp_coder/workflows/vscodeclaude/cleanup.py`
- [ ] Update existing cleanup tests for new string-based status
- [ ] Add new tests: `test_cleanup_handles_missing_folder`, `test_cleanup_skips_no_git_folder`, `test_cleanup_skips_error_folder`
- [ ] Run quality checks (pylint, pytest, mypy) and fix any issues
- [ ] Prepare git commit message for Step 3

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Run full test suite to verify all tests pass
- [ ] Run final quality checks (pylint, pytest, mypy)
- [ ] Prepare PR summary with changes overview
- [ ] Create Pull Request
