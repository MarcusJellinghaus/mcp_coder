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

### Step 1: Rename the conftest builder to `make_assessment`
See [step_1.md](./steps/step_1.md)

- [x] Implementation: rename `_make_assessment` → `make_assessment` in `conftest.py` (move to shared builders section); update imports/calls in `test_session_restart_lifecycle.py` and `test_session_restart_issue_status.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues (collect-only and pass counts unchanged)
- [x] Commit message prepared

### Step 2: Replace the four identical local copies with `make_assessment`
See [step_2.md](./steps/step_2.md)

- [x] Implementation: delete local `_make_assessment` in `test_session_restart_cache.py`, `test_session_restart_closed_sessions.py`, `test_session_restart_branch_integration.py`, `test_closed_issues_integration.py`; import shared `make_assessment`; ruff fix F401 and verify `types` imports
- [x] Quality checks: pylint, pytest, mypy — fix all issues (collect-only and pass counts unchanged)
- [x] Commit message prepared

### Step 3: Replace the SKIP-action copies with `make_assessment(..., action=SKIP)`
See [step_3.md](./steps/step_3.md)

- [x] Implementation: delete local builders in `test_sessions.py` and `test_active_set_invariant.py`; call `make_assessment(..., action=SessionAction.SKIP)`; ruff fix F401 and verify `types` imports
- [x] Quality checks: pylint, pytest, mypy — fix all issues (collect-only and pass counts unchanged)
- [x] Commit message prepared

### Step 4: Add `make_sample_assessment` and use it in explain and types tests
See [step_4.md](./steps/step_4.md)

- [ ] Implementation: add `make_sample_assessment` to `conftest.py`; replace local builders in `test_explain.py` and `test_types.py` (use `make_signals` / `make_sample_assessment`); ruff fix F401 and verify `types` imports
- [ ] Quality checks: pylint, pytest, mypy — fix all issues (collect-only and pass counts unchanged)
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `main` and address findings
- [ ] PR summary prepared
