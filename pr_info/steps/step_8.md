# Step 8 — Composition tests (Scenarios A and B)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_8.md`) in
> full. All prior steps (1–7) must already be merged. This step adds two
> cross-item integration-style tests. No production code changes — only
> tests. One commit.

## Goal

Verify that the cross-item flows in the acceptance criteria work end-to-end:

- **Scenario A** (Items 5 + 8): orphan workspace file + optional
  `.to_be_deleted` entry → both self-clean in one command pass.
- **Scenario B** (Items 1 + 8): live VSCode with folder in cmdline + stale
  `.to_be_deleted` entry → reconciliation removes the entry, no delete
  attempted, idempotent on replay.

## WHERE

- `tests/workflows/vscodeclaude/test_cleanup.py` (add two new tests; no
  production code changes)
- `tests/workflows/vscodeclaude/test_status_display.py` (Scenario A's
  cross-module assertion — see "Cross-module assertion" below)

### Cross-module assertion (Scenario A)

Scenario A asserts that `display_status_table` no longer lists the
cleaned-up session. **Decision (engineer's call): split that assertion into
a separate test in `test_status_display.py`** that consumes the same
fixtures as the cleanup test. Rationale: keeps `test_cleanup.py` focused on
cleanup semantics and avoids a cross-module import dependency in a cleanup
test. The new test in `test_status_display.py` re-runs the Scenario A setup
(or shares fixtures via a `conftest.py` helper) and asserts the post-cleanup
sessions list renders without the removed session.

## WHAT — function signatures

No new code. Two new test functions:

```python
def test_orphan_workspace_file_end_to_end(tmp_path, monkeypatch) -> None: ...
def test_false_negative_reconciliation(tmp_path, monkeypatch) -> None: ...
```

## HOW — integration points

Both tests wire together real `is_session_active` (via
`build_active_session_set`) and `cleanup_stale_sessions` against a `tmp_path`
workspace base. Mock only the boundary:

- Mock `is_vscode_open_for_folder` / `_get_vscode_processes` so VSCode
  process discovery is deterministic.
- Mock `is_issue_closed` / `cached_issues_by_repo` for scenario A (so the
  closed-issue branch fires).

`safe_delete_folder` should be patched (or its real implementation allowed
to run against `tmp_path`) so the assertions on "not called" / "called with
X" are explicit.

## ALGORITHM — Scenario A

```
setup:
    create tmp workspace_base
    create folder mcp_coder_188 — then delete it (folder absent)
    create workspace_base/mcp_coder_188.code-workspace
    write session record with closed issue + folder=…/mcp_coder_188
    optionally add mcp_coder_188 to .to_be_deleted

run:
    active_set = build_active_session_set(sessions)
    cleanup_stale_sessions(workspace_base, active_set, dry_run=False, cached_issues_by_repo=...)

assert (in test_cleanup.py):
    session record removed from sessions.json
    workspace_base/mcp_coder_188.code-workspace does NOT exist
    if .to_be_deleted entry existed: entry removed

assert (in test_status_display.py, separate test):
    subsequent display_status_table does not list session
```

## ALGORITHM — Scenario B

```
setup:
    create tmp workspace_base
    create folder mcp_coder_937 (real directory)
    add mcp_coder_937 to .to_be_deleted
    mock is_vscode_open_for_folder("…/mcp_coder_937") -> (True, 12345)
    patch safe_delete_folder so we can assert_not_called

run:
    cleanup_stale_sessions(workspace_base, active_set={}, dry_run=False, cached_issues_by_repo={})

assert:
    .to_be_deleted no longer contains mcp_coder_937
    reconciliation warning emitted (caplog)
    safe_delete_folder not called
    folder still exists on disk

replay (idempotence):
    cleanup_stale_sessions(...)
    no new warning
    no .to_be_deleted retry
```

## DATA

- Both tests use `tmp_path` for the workspace base.
- `caplog` (pytest fixture) for warning-message assertions.
- `monkeypatch` for `psutil` / `is_vscode_open_for_folder` boundaries.
- No new production data structures.

## Tests (this step IS the tests)

Two pytest functions as above. Place them next to the per-item Item #8 tests
from Step 4 for discoverability.

## Done when

- Both composition tests pass.
- All previously-passing tests still pass.
- mypy, pylint clean (test files included in the relevant target dirs).
- One commit: tests only.
