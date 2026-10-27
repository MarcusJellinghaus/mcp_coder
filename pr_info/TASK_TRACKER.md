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

### Step 1: Move `TestGetStaleSessions` → `test_cleanup_get_stale_sessions.py`
See [step_1.md](./steps/step_1.md)

- [x] Implementation: baseline counts, move `TestGetStaleSessions` with `move_symbol`, fix imports to end state
- [x] Quality checks: pylint, pytest, mypy (plus ruff F401, collect counts 23/6/N, 30 passed) — fix all issues
- [x] Commit message prepared

### Step 2: Move `TestSoftDeleteAndRetry` → `test_cleanup_retry.py`; drop the allowlist entry
See [step_2.md](./steps/step_2.md)

- [x] Implementation: move `TestSoftDeleteAndRetry` with `move_symbol` (keep method-local `helpers` imports), fix imports, remove `.large-files-allowlist` line
- [x] Quality checks: pylint, pytest, mypy (plus ruff, lint-imports, tach, vulture, check_file_size, collect counts 14/6/9/N) — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: compact `git diff` against base branch shows only import changes, new file headers, moved blocks, and the allowlist line
- [ ] PR summary prepared
