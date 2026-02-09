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

### Step 1: Create folder_deletion.py Module with Tests
See [step_1.md](./steps/step_1.md) for details.

- [ ] Create `src/mcp_coder/utils/folder_deletion.py` with all helper functions and main `safe_delete_folder()` function
- [ ] Create `tests/utils/test_folder_deletion.py` with mock-based test suite
- [ ] Run pylint and fix any issues
- [ ] Run pytest and verify all tests pass
- [ ] Run mypy and fix any type errors
- [ ] Prepare git commit message for Step 1

### Step 2: Update cleanup.py and Module Exports
See [step_2.md](./steps/step_2.md) for details.

- [ ] Update `src/mcp_coder/utils/__init__.py` to export `safe_delete_folder` from Layer 1
- [ ] Update `src/mcp_coder/workflows/vscodeclaude/cleanup.py` to use `safe_delete_folder()`
- [ ] Add integration test to `tests/workflows/vscodeclaude/test_cleanup.py`
- [ ] Add comments to `tools/safe_delete_folder.py` pointing to library functions
- [ ] Run pylint and fix any issues
- [ ] Run pytest and verify all tests pass
- [ ] Run mypy and fix any type errors
- [ ] Prepare git commit message for Step 2

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Verify all quality checks pass (pylint, pytest, mypy)
- [ ] Create PR summary with changes overview
- [ ] Final review of code changes
