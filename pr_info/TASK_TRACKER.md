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

### Step 1: TokenUsage Dataclass + format_token_count()
- [x] Implementation: `TokenUsage` dataclass, `format_token_count()` in `types.py` + tests in `test_types.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Wire TokenUsage into AppCore
- [x] Implementation: `_token_usage` field, `token_usage` property, usage extraction in `stream_llm()` + tests in `test_app_core.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Three-Zone Status Bar UI + CSS
- [x] Implementation: replace `#input-hint` with `#status-bar` (3 zones), `_update_token_display()`, remove `on_text_area_changed()`, update CSS + snapshot tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Documentation — `docs/icoder/icoder.md`
- [x] Implementation: create `docs/icoder/icoder.md` with TUI reference (status line, commands, busy indicator, input)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request
- [x] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
