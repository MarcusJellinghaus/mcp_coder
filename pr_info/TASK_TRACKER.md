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

### Step 1: OutputLog Wrap + Explicit Color Scheme
> [Detail](./steps/step_1.md) — Enable line wrapping in OutputLog, add explicit background/foreground colors to OutputLog and InputArea CSS.

- [ ] Implementation: add `wrap=True` to OutputLog constructor, add explicit colors in `styles.py`
- [ ] Quality checks pass: pylint, pytest, mypy — fix all issues
- [ ] Commit: `fix(icoder): enable line wrapping and explicit colors in TUI widgets`

### Step 2: InputArea Auto-Grow
> [Detail](./steps/step_2.md) — Make InputArea grow dynamically with content, capped at 1/3 screen height.

- [ ] Implementation: remove `max-height` from CSS, add `on_text_area_changed` handler in `input_area.py`, add test in `test_widgets.py`
- [ ] Quality checks pass: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat(icoder): auto-grow input area with content up to 1/3 screen height`

### Step 3: Snapshot Regeneration + Documentation
> [Detail](./steps/step_3.md) — Regenerate snapshot baselines, verify no secrets in SVGs, add documentation comments.

- [ ] Implementation: regenerate snapshots with `--snapshot-update`, verify SVGs are clean, add docstring to `test_snapshots.py` and comment in `pyproject.toml`
- [ ] Quality checks pass: pylint, pytest, mypy — fix all issues
- [ ] Commit: `test(icoder): regenerate snapshot baselines and add snapshot docs`

## Pull Request

- [ ] PR review: verify all steps implemented correctly
- [ ] PR summary prepared
