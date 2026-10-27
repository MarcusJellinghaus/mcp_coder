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

### Step 1: Move the six approval helpers → `tests/icoder/_app_pilot_approval_helpers.py`
See [step_1.md](./steps/step_1.md)

- [x] Implementation: baseline counts, move `_APPROVAL_TOOL`, `_approval_event`, `_RecordingEngine`, `_isolate_user_layer`, `_author_project_ask`, `_open_modal_and_press` verbatim (hand-moved after `move_symbol` rewrote bodies), repoint both approval imports, drop unused imports in test_app_pilot.py, verify collect counts (tests/icoder 1062; 19 / 22 / 11)
- [x] Quality checks: pylint, pytest, mypy (plus ruff, lint-imports, tach, vulture, file size, compact diff review) — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review full diff against base branch — only moved blocks, import changes, new-file header
- [ ] PR summary prepared
