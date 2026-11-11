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

### Step 1: Label renames
See [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 2: Row model and per-section width formula in `verify_formatting`
See [step_2.md](./steps/step_2.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 3: Renderer and `SectionBuilder` (new `verify_render.py`) + shared test helpers
See [step_3.md](./steps/step_3.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, lint-imports, vulture) — fix all issues
- [x] Commit message prepared

### Step 4: Formatters return rows; `execute_verify` drives a `SectionBuilder`
See [step_4.md](./steps/step_4.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, lint-imports) — fix all issues
- [x] Commit message prepared

### Step 5: `verify_sections` helpers write through the builder; drop `_VALUE_COLUMN_INDENT`
See [step_5.md](./steps/step_5.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, vulture) — fix all issues
- [x] Commit message prepared

### Step 6: `verify.py` inline sections write through the builder; smoke test returns `Row`; drop `label_width` from `_format_row`
See [step_6.md](./steps/step_6.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks (pylint, pytest, mypy, vulture) — fix all issues
- [ ] Commit message prepared

### Step 7: New `=== LLM TEST` section + docs + streaming test
See [step_7.md](./steps/step_7.md)

- [ ] Implementation (tests + production code + `docs/cli-reference.md`)
- [ ] Quality checks (pylint, pytest, mypy) — fix all issues
- [ ] Commit message prepared

### Step 8: Per-section alignment tests, including indent 6
See [step_8.md](./steps/step_8.md)

- [ ] Implementation (tests + any production fix they expose)
- [ ] Quality checks (pylint, pytest, mypy) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against base branch, address findings
- [ ] PR summary prepared
