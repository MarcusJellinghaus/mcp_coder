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

### Step 1: Add `format_status_labels()` and unify label formatting

> [Detail](./steps/step_1.md) — Extract `format_status_labels()`, refactor `build_set_status_epilog()` and `validate_status_label()` to use it. No behavior change.

- [x] Implementation: tests (`test_format_status_labels_output`, `test_format_status_labels_dynamic_width`, update `validate_status_label` tests) + production code (`format_status_labels`, refactor callers)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Make `status_label` optional and add no-args label listing

> [Detail](./steps/step_2.md) — Make `status_label` argument optional (`nargs="?"`), add no-args early return printing available labels, update docstring.

- [x] Implementation: tests (`test_execute_set_status_no_args_shows_labels`, `test_execute_set_status_no_args_fallback_config`) + production code (parser change, no-args path in `execute_set_status`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: verify all steps integrated correctly, no regressions
- [ ] PR summary prepared
