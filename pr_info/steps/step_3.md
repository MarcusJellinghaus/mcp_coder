# Step 3: Update tests

## LLM Prompt

```
See pr_info/steps/summary.md for full context.
Steps 1 and 2 are complete: get_stale_sessions returns 3-tuples and
cleanup_stale_sessions uses the reason in warnings.

Implement Step 3: update `tests/workflows/vscodeclaude/test_cleanup.py` to:
1. Fix all existing tests that unpack 2-tuples or pass 2-tuple mocks
2. Add new tests covering each reason value and combined reasons
3. Extend two existing warning tests to assert the reason appears in output

All new tests must use monkeypatch to avoid real I/O.
Follow the patterns already established in the file.
```

---

## WHERE

**File:** `tests/workflows/vscodeclaude/test_cleanup.py`

---

## WHAT

### A. Fix existing tests (mechanical updates)

#### 1. Mock lambdas that return 2-tuples → 3-tuples

Every `monkeypatch.setattr` for `get_stale_sessions` currently returns
`[(session, "Clean")]` etc. Add a dummy reason string:

```python
# Before
lambda cached_issues_by_repo=None: [(session, "Clean")]
# After
lambda cached_issues_by_repo=None: [(session, "Clean", "closed")]
```

Affected tests in `TestCleanup`:
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

#### 2. Unpack sites in `TestGetStaleSessions`

```python
# Before
session, git_status = result[0]
# After
session, git_status, reason = result[0]
```

Affected tests:
- `test_includes_blocked_sessions`
- `test_includes_closed_issue_sessions`
- `test_includes_bot_pickup_status_sessions`
- `test_includes_bot_busy_status_sessions`
- `test_includes_pr_created_status_sessions`
- `test_does_not_skip_zombie_vscode_session` — unpack `session, git_status, reason = result[0]`
- `test_get_stale_sessions_returns_stale` (in `TestCleanup`) uses index access
  `result[0][1]` — add `result[0][2]` assertion

---

### B. New tests — reason values (add to `TestGetStaleSessions`)

#### `test_reason_closed`
- Issue state `"closed"`, not blocked, not ineligible
- Assert `reason == "closed"`

#### `test_reason_blocked`
- Issue open, has `"blocked"` label, eligible status
- Mock `is_session_stale` → `False`
- Assert `reason == "blocked"`

#### `test_reason_bot_status`
- Issue open, no blocked label, ineligible status (`"status-02:awaiting-planning"`)
- Mock `is_session_stale` → `False`
- Assert `reason == "bot status"`

#### `test_reason_stale_with_cache`
- Issue open, eligible status in session, different eligible status in cache:
  session has `"status": "status-01:created"`, cached issue has label `"status-04:plan-review"`
- Do NOT mock `is_session_stale` — let it compute from the real session/cache data
- Assert `reason == "stale → status-04:plan-review"`

#### `test_reason_stale_no_cache`
- No `cached_issues_by_repo` passed
- Mock `is_session_stale` → `True`
- Assert `reason == "stale"`

#### `test_reason_combined_closed_blocked`
- Issue state `"closed"`, also has `"blocked"` label
- Assert `reason == "closed, blocked"`

---

### C. Extend two existing warning tests (add `capsys`)

#### `test_cleanup_skips_no_git_folder` (in `TestCleanup`)
- Add `capsys: pytest.CaptureFixture[str]` parameter
- Change mock to return `(no_git_session, "No Git", "closed")`
- After `cleanup_stale_sessions`, assert:
  ```python
  assert "no git, closed" in capsys.readouterr().out
  ```

#### `test_cleanup_skips_error_folder` (in `TestCleanup`)
- Same pattern with `"Error"` and `"blocked"` as reason

---

## HOW

- All new tests follow the `monkeypatch` pattern already in the file
- `is_session_stale` is patched at `mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale`
- Sessions file is written via `sessions_file.write_text(json.dumps(...))`
- No real filesystem or GitHub API calls

---

## ALGORITHM

Each new reason test follows this pattern:

```
1. Write sessions JSON with one session
2. Write cached_issues_by_repo with the appropriate issue data
3. Patch is_session_active → False, _get_configured_repos → {"owner/repo"}
4. Patch get_folder_git_status → "Clean"
5. Patch is_session_stale as needed
6. Call get_stale_sessions(cached_issues_by_repo=...)
7. Unpack: session, git_status, reason = result[0]
8. Assert reason == expected
```

---

## DATA

No new return types. All assertions are on the `reason` string element of the 3-tuple.
