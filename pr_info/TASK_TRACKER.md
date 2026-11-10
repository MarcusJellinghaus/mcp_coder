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

### Step 1: Move `read_and_clear_blocked` into `blocked.py` — [step_1.md](./steps/step_1.md)
- [x] Implementation: move `read_and_clear_blocked` and constants to `blocked.py`, fix imports (pure refactor)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Add the `checks_exhausted` failure reason — [step_2.md](./steps/step_2.md)
- [x] Implementation: tests in `test_failure_reporting.py`, then `FAILURE_LABELS` / `CATEGORY_DISPLAY` entries
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: New fix loop in `check_loop.py` with a shared cap — [step_3.md](./steps/step_3.md)
- [x] Implementation: tests in `test_check_loop.py` / `test_check_loop_fix_turns.py`, then `check_loop.py` (`CheckOutcome`, `check_and_fix_mypy`, `_fix_turn`, moved `_build_fix_prompt`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Both callers on the new loop; delete the old one — [step_4.md](./steps/step_4.md)
- [x] Implementation: conftest autouse fixture, `test_task_processing_checks.py`, `test_core_final_check.py`; switch `task_processing.py` / `core.py` / `__init__.py`; delete old loop and `test_task_processing_mypy.py`; update existing tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: Rescue commit and the abort rule — [step_5.md](./steps/step_5.md)
- [x] Implementation: tests in `test_check_loop_rescue.py` / `test_core_check_abort.py`, then `rescue_commit`, `TaskOutcome.checks_failed`, `abort_checks` in `core.py`; patch `rescue_commit` in existing core tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 6: Run the final check on a re-run with all tasks ticked — [step_6.md](./steps/step_6.md)
- [ ] Implementation: tests in `test_core_final_check.py`, patch `no_tasks` core tests, remove `progress.completed > 0` gate in `core.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: New default bindings, binding validation and the test budget — [step_7.md](./steps/step_7.md)
- [ ] Implementation: update toolkit tests, then `DEFAULT_BINDINGS` / `_ALLOWED_ACTIONS` in `toolkit_runner.py` and `pytest-timeout = 1800` in `pyproject.toml`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: Linux implement template exports `VIRTUAL_ENV` — [step_8.md](./steps/step_8.md)
- [ ] Implementation: tests in `test_command_templates.py`, then the `VIRTUAL_ENV` line in `IMPLEMENT_COMMAND_TEMPLATE`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 9: Migration note and doc updates — [step_9.md](./steps/step_9.md)
- [ ] Implementation: create `docs/migration/multi-language.md`, update `python.md`, `05-implementation.md`, `architecture.md`, `quality-and-security-checks.md`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: review the full branch diff against the base branch and address findings
- [ ] PR summary prepared
