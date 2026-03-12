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

### Step 1 — Pure functions + updated types (TDD) ([step_1.md](./steps/step_1.md))
- [x] Implement `RunData` TypedDict, update `JobData` with `run_id`, update `CIStatusData`, add `filter_runs_by_head_sha()` and `aggregate_conclusion()` pure functions — tests first
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message

### Step 2 — Rewrite `get_latest_ci_status()` for multi-workflow support (TDD) ([step_2.md](./steps/step_2.md))
- [x] Update existing tests (`run["id"]` → `run["run_ids"]`, add `run_id` to jobs), add `TestGetLatestCIStatusMultiWorkflow` class, rewrite `get_latest_ci_status()` method
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message

### Step 3 — Update `branch_status.py` — multi-run log fetching (TDD) ([step_3.md](./steps/step_3.md))
- [x] Update `_build_ci_error_details()` test fixtures and add multi-run log fetching tests, implement per-`run_id` log fetching (up to 3 runs) and jobs_fetch_warning display
- [x] Run quality checks (pylint, pytest, mypy) and fix all issues
- [x] Prepare git commit message

### Step 4 — Update polling logic in `core.py` and `check_branch_status.py` ([step_4.md](./steps/step_4.md))
- [ ] Update polling logic: `run["id"]` → `run["run_ids"]` set comparison in `_wait_for_new_ci_run()`, `check_and_fix_ci()`, `_run_ci_analysis_and_fix()`, `_poll_for_ci_completion()`, and `_run_auto_fixes()`
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message

### Step 5 — Final validation — all tests pass, type checks clean ([step_5.md](./steps/step_5.md))
- [ ] Run full test suite across all touched files, fix any remaining test fixtures referencing `run["id"]` or missing `run_id` on `JobData`
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message

## Pull Request
- [ ] Review all changes for consistency and completeness across all 4 source files and 2 test files
- [ ] Prepare PR title, summary, and description
