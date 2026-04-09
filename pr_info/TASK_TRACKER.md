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

### Step 1: Backslash+Enter newline escape logic
- [x] Implementation: `_count_trailing_backslashes` helper + modified Enter handler in `input_area.py`, parametrized tests in `test_widgets.py`
- [x] Quality checks pass (pylint, pytest, mypy)
- [x] Commit: `feat(icoder): backslash+Enter inserts newline (#754)`

### Step 2: Status hint widget below InputArea
- [x] Implementation: `Static` hint widget in `app.py`, `on_text_area_changed` handler, CSS in `styles.py`, hint visibility tests in `test_app_pilot.py`
- [x] Quality checks pass (pylint, pytest, mypy)
- [x] Commit: `feat(icoder): add newline hint below input area (#754)`

### Step 3: /help keyboard shortcuts section
- [x] Implementation: append keyboard shortcuts to `/help` output in `help.py`, test in `test_app_core.py`
- [x] Quality checks pass (pylint, pytest, mypy)
- [x] Commit: `feat(icoder): add keyboard shortcuts to /help (#754)`

### Step 4: docs/iCoder.md user guide
- [x] Implementation: create `docs/iCoder.md` covering overview, startup, commands, autocomplete, streaming, keyboard shortcuts, backslash escape
- [x] Quality checks pass (pylint, pytest, mypy)
- [x] Commit: `docs: add iCoder user guide (#754)`

### Step 5: Snapshot updates
- [ ] Implementation: regenerate Textual SVG snapshots via `pytest tests/icoder/test_snapshots.py --snapshot-update`, verify correctness
- [ ] Quality checks pass (pylint, pytest, mypy)
- [ ] Commit: `test(icoder): update snapshots for input hint widget (#754)`

## Pull Request
- [ ] PR review: verify all steps implemented correctly
- [ ] PR summary prepared
