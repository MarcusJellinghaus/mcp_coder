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

### Step 1: Always-on endpoint-shape heuristic in `verify`

See [step_1.md](./steps/step_1.md).

- [x] Implementation: add `_check_endpoint_shape` helper + wiring in `verification.py`, `_LABEL_MAP` entry in `verify.py`, config docs note, and unit + integration tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: `--check-models` live-probe 404 messaging

See [step_2.md](./steps/step_2.md).

- [x] Implementation: reword generic `except` branch of `_list_models_for_backend` for endpoint 404s + unit tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Shared prompt-path 404 hint helper

See [step_3.md](./steps/step_3.md).

- [x] Implementation: add `_is_404_error` + `_format_404_hint` helpers, wire into `_ask_text`/`_ask_text_stream`, add provider + streaming tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [x] PR review: verify all steps implemented and checks pass
- [ ] PR summary prepared
