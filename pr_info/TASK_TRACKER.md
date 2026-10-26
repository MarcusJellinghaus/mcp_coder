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

### Step 1: Split `test_sessions.py` into six files (tests only)
See [step_1.md](./steps/step_1.md)

- [x] Implementation: record baseline counts, move test classes via `move_symbol` into the 5 new files, fix imports (ruff F401), remove `test_sessions.py` from `.large-files-allowlist`, verify collect counts
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Move the VSCode probes from `sessions.py` into `detection.py`
See [step_2.md](./steps/step_2.md)

- [x] Implementation: move the 14 probe symbols + `HAS_WIN32GUI` guard to `detection.py`, fix src imports/call sites, re-point test imports and patch targets, update `test_detection.py` docstrings, run audits
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `main` for pure-refactoring compliance
- [ ] PR summary prepared
