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

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

### Step 1: Update `get_stale_sessions` to return a reason string

See [step_1.md](./steps/step_1.md) for full details.

- [x] Implement Step 1: update `get_stale_sessions` in `src/mcp_coder/workflows/vscodeclaude/cleanup.py`
  - Change return type from `list[tuple[VSCodeClaudeSession, str]]` to `list[tuple[VSCodeClaudeSession, str, str]]`
  - Add `status_labels: list[str] = []` initialisation before the `if cached_issues_by_repo:` block
  - Break short-circuit `or` condition into explicit `is_stale` bool
  - Build `reasons` list from `is_closed`, `is_blocked`, `is_ineligible`, `is_stale` flags
  - Append `(session, git_status, reason)` instead of `(session, git_status)`
- [x] Quality checks for Step 1
  - [x] Run pylint and fix all issues found
  - [x] Run pytest and fix all failing tests
  - [x] Run mypy and fix all type errors
- [x] Prepare git commit message for Step 1

---

### Step 2: Update `cleanup_stale_sessions` to use the reason in warnings

See [step_2.md](./steps/step_2.md) for full details.

- [x] Implement Step 2: update `cleanup_stale_sessions` in `src/mcp_coder/workflows/vscodeclaude/cleanup.py`
  - Change `for session, git_status in stale_sessions:` to `for session, git_status, reason in stale_sessions:`
  - Update non-empty No Git / Error warning messages to include `reason`:
    - `logger.warning("Skipping folder (%s, %s): %s", git_status.lower(), reason, folder)`
    - `print(f"[WARN] Skipping ({git_status.lower()}, {reason}): {folder}")`
  - Leave dirty-folder warnings unchanged
- [x] Quality checks for Step 2
  - [x] Run pylint and fix all issues found
  - [x] Run pytest and fix all failing tests
  - [x] Run mypy and fix all type errors
- [x] Prepare git commit message for Step 2

---

### Step 3: Update tests

See [step_3.md](./steps/step_3.md) for full details.

- [ ] Implement Step 3: update `tests/workflows/vscodeclaude/test_cleanup.py`
  - **Fix existing tests (2-tuple → 3-tuple mocks):** Add dummy reason string to all `monkeypatch.setattr` lambdas returning `get_stale_sessions` results in `TestCleanup`:
    - `test_cleanup_stale_sessions_dry_run`
    - `test_cleanup_stale_sessions_skips_dirty`
    - `test_cleanup_stale_sessions_deletes_clean`
    - `test_cleanup_stale_sessions_empty`
    - `test_cleanup_handles_missing_folder`
    - `test_cleanup_skips_no_git_folder`
    - `test_cleanup_skips_error_folder`
    - `test_cleanup_deletes_empty_no_git_folder`
    - `test_cleanup_dry_run_reports_empty_no_git_folder`
    - `test_cleanup_deletes_empty_error_folder`
    - `test_cleanup_dry_run_reports_empty_error_folder`
  - **Fix existing unpack sites in `TestGetStaleSessions`:** Change `session, git_status = result[0]` to `session, git_status, reason = result[0]` in:
    - `test_includes_blocked_sessions`
    - `test_includes_closed_issue_sessions`
    - `test_includes_bot_pickup_status_sessions`
    - `test_includes_bot_busy_status_sessions`
    - `test_includes_pr_created_status_sessions`
    - `test_does_not_skip_zombie_vscode_session`
    - `test_get_stale_sessions_returns_stale` (add `result[0][2]` assertion)
  - **Add new reason tests to `TestGetStaleSessions`:**
    - `test_reason_closed` — assert `reason == "closed"`
    - `test_reason_blocked` — assert `reason == "blocked"`
    - `test_reason_bot_status` — assert `reason == "bot status"`
    - `test_reason_stale_with_cache` — assert `reason == "stale → status-04:plan-review"` (no mock of `is_session_stale`)
    - `test_reason_stale_no_cache` — assert `reason == "stale"` (mock `is_session_stale → True`)
    - `test_reason_combined_closed_blocked` — assert `reason == "closed, blocked"`
  - **Extend two warning tests with `capsys`:**
    - `test_cleanup_skips_no_git_folder` — add `capsys`, assert `"no git, closed"` in stdout
    - `test_cleanup_skips_error_folder` — add `capsys`, assert `"error, blocked"` in stdout
- [ ] Quality checks for Step 3
  - [ ] Run pylint and fix all issues found
  - [ ] Run pytest and fix all failing tests
  - [ ] Run mypy and fix all type errors
- [ ] Prepare git commit message for Step 3

---

## Pull Request

- [ ] Review all changes across `src/mcp_coder/workflows/vscodeclaude/cleanup.py` and `tests/workflows/vscodeclaude/test_cleanup.py`
- [ ] Verify PR summary accurately describes: return-type change, reason-building logic, warning message improvement, and test coverage
- [ ] Confirm no unintended files modified (no changes to `__init__.py`, no new modules)
- [ ] Prepare PR title and description referencing issue #452
