# Step 1: Add `all_cached_issues` Optional Parameter to `process_eligible_issues` + Unit Test

## Context
See [summary.md](summary.md) for the full problem description.

This step implements the core fix inside `session_launch.py` and validates it with a unit test
**before** the caller is updated in Step 2. The test is written first (TDD).

---

## WHERE

| File | Role |
|---|---|
| `tests/workflows/vscodeclaude/test_orchestrator_launch.py` | New test class (write first) |
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | Add optional parameter |

---

## WHAT

### Test (write first)

New class `TestProcessEligibleIssuesPrefetchedIssues` with one test:

```python
def test_pre_fetched_issues_bypasses_get_all_cached_issues(
    self, monkeypatch: pytest.MonkeyPatch
) -> None:
```

**What it verifies (combined requirement — single test is stronger):**
- When `all_cached_issues` is passed as a non-None list, `get_all_cached_issues` is **not** called
  (mock raises `AssertionError` if invoked — a test failure is immediate and obvious).
- The passed list is used: a session is started for the issue it contains.

### Production change

New optional parameter on `process_eligible_issues`:

```python
def process_eligible_issues(
    repo_name: str,
    repo_config: dict[str, str],
    vscodeclaude_config: VSCodeClaudeConfig,
    max_sessions: int,
    repo_filter: str | None = None,
    all_cached_issues: list[IssueData] | None = None,   # ← new
) -> list[VSCodeClaudeSession]:
```

---

## HOW

### Test setup (mirrors existing tests in the same file)

- Mock `IssueManager` and `IssueBranchManager` constructors (avoid token validation).
- Replace `get_all_cached_issues` with a lambda that raises `AssertionError("should not be called")`.
- Mock `_filter_eligible_vscodeclaude_issues` to return the same pre-fetched issue.
- Mock `get_linked_branch_for_issue` → `None`, `get_session_for_issue` → `None`,
  `get_active_session_count` → `0`, `get_github_username` → `"testuser"`,
  `load_repo_vscodeclaude_config` → `{}`.
- Mock `prepare_and_launch_session` as `MagicMock()`.

### Production change

Replace the unconditional `get_all_cached_issues(...)` call with:

```python
if all_cached_issues is None:
    logger.debug(
        "process_eligible_issues: no pre-fetched issues provided, fetching from cache"
    )
    all_cached_issues = get_all_cached_issues(
        repo_full_name=repo_full_name,
        issue_manager=issue_manager,
        force_refresh=False,
        cache_refresh_minutes=get_cache_refresh_minutes(),
    )
```

No other logic in the function changes.

---

## ALGORITHM

```
# process_eligible_issues (core change only)
if all_cached_issues is None:
    log debug "fetching from cache"
    all_cached_issues = get_all_cached_issues(...)   # existing call, unchanged

eligible = _filter_eligible_vscodeclaude_issues(all_cached_issues, github_username)
# ... rest of function unchanged ...
```

---

## DATA

`all_cached_issues` type: `list[IssueData] | None`

- `None` (default) → function fetches independently, same as before (backward-compatible).
- `list[IssueData]` → used directly, `get_all_cached_issues` is not called.

`IssueData` is already imported in `session_launch.py`; no new imports needed.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Your task is to implement Step 1 of issue #468.

Files to change:
  1. tests/workflows/vscodeclaude/test_orchestrator_launch.py
  2. src/mcp_coder/workflows/vscodeclaude/session_launch.py

Instructions:
  1. Read both files in full before making any changes.
  2. Add the test class TestProcessEligibleIssuesPrefetchedIssues to the test file.
     Add a single test: test_pre_fetched_issues_bypasses_get_all_cached_issues.
     The mock for get_all_cached_issues must raise AssertionError if called.
     The test must also assert that prepare_and_launch_session was called once
     (proving the pre-fetched issue was used).
     Follow the exact mock style used by the existing test classes in the file.
  3. Add the all_cached_issues optional parameter to process_eligible_issues in session_launch.py.
     Replace the unconditional get_all_cached_issues call with the conditional guard described in
     step_1.md. Do not change any other logic in the function.
  4. Run the tests and confirm the new test passes and no existing tests are broken.
```
