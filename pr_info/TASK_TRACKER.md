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

### Step 1: Add tests for new `is_session_active()` behavior — [step_1.md](./steps/step_1.md)

- [x] Implementation: add `TestIsSessionActiveWindowPriority` test class with 3 test methods to `tests/workflows/vscodeclaude/test_sessions.py`
- [x] Quality checks: pylint, mypy pass (pytest skipped — tests expected to fail until Step 2)
- [x] Commit: `test: add tests for window-title-priority in is_session_active #547`

### Step 2: Implement the fix and update existing test — [step_2.md](./steps/step_2.md)

- [x] Implementation: modify `is_session_active()` in `sessions.py` to prioritize window title check; update `test_get_active_session_count_with_mocked_pid_check` mock setup
- [x] Quality checks: pylint, pytest, mypy all pass
- [x] Commit: `fix: prioritize window title over PID in is_session_active #547`

## Pull Request

- [ ] Review all changes across both steps for correctness and consistency
- [ ] Create PR with summary of issue #547 fix
