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

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

### Step 1 — Tests: `_try_delete_empty_directory` retry behaviour
See [step_1.md](./steps/step_1.md)

- [x] Implement Step 1: add 3 new test methods for `_try_delete_empty_directory` in `tests/utils/test_folder_deletion.py` (`TestHelperFunctions` class), and patch `time.sleep` in the 2 existing tests
- [x] Quality checks: run pylint, pytest, mypy — fix all issues found
- [x] Prepare git commit message for Step 1

### Step 2 — Implementation: `_try_delete_empty_directory` retry loop
See [step_2.md](./steps/step_2.md)

- [x] Implement Step 2: add `import time` and replace single `rmdir` attempt with 3-attempt retry loop in `_try_delete_empty_directory()` in `src/mcp_coder/utils/folder_deletion.py`
- [x] Quality checks: run pylint, pytest, mypy — fix all issues found
- [x] Prepare git commit message for Step 2

### Step 3 — Tests: empty "No Git" / "Error" folder deletion in `cleanup_stale_sessions`
See [step_3.md](./steps/step_3.md)

- [ ] Implement Step 3: update 2 existing tests to use non-empty folders, and add 4 new empty-folder test methods in `tests/workflows/vscodeclaude/test_cleanup.py` (`TestCleanup` class)
- [ ] Quality checks: run pylint, pytest, mypy — fix all issues found
- [ ] Prepare git commit message for Step 3

### Step 4 — Implementation: empty-folder gate in `cleanup_stale_sessions`
See [step_4.md](./steps/step_4.md)

- [ ] Implement Step 4: replace unconditional skip in the `else` branch of `cleanup_stale_sessions()` in `src/mcp_coder/workflows/vscodeclaude/cleanup.py` with an emptiness check that deletes empty folders and skips non-empty ones
- [ ] Quality checks: run pylint, pytest, mypy — fix all issues found
- [ ] Prepare git commit message for Step 4

---

## Pull Request

- [ ] Review all changes across the 4 steps for correctness and completeness
- [ ] Verify all tests pass and quality checks are clean
- [ ] Write PR summary covering both bug fixes (retry loop in `folder_deletion.py` and empty-folder gate in `cleanup.py`)
