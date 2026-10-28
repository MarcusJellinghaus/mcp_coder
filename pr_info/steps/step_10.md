# Step 10 — `status.py`: a failed live issue fetch is "unknown", never "closed"

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_10.md`).
> Implement only Step 10. Tests first, then code.
> Run pylint, pytest (fast unit marker set, `-n auto`) and mypy; all must pass.
> Produce exactly one commit.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/status.py`
  (`get_issue_current_status`, `is_issue_closed`, `is_session_stale`)
- tests: `tests/workflows/vscodeclaude/test_cache_aware.py` (or a new
  `test_status_unknown.py` next to it)

## WHAT
```python
def get_issue_current_status(
    issue_number: int,
    cached_issues: dict[int, IssueData] | None = None,
    issue_manager: IssueManager | None = None,
) -> tuple[str | None, bool | None]:
    """... is_open: True open, False closed, None unknown (live fetch failed)."""
```
Live fallback branch:
```
try:   issue = issue_manager.get_issue(issue_number)
except Exception as e: raise_if_rate_limited(e); WARNING; return None, None
if issue["number"] == 0: WARNING "could not fetch issue #N"; return None, None   # empty IssueData
<existing label scan, is_open = issue["state"] == "open">
```
- `is_issue_closed`: `if is_open is None: WARNING; return False`; else `return not is_open`.
- `is_session_stale`: before the closed check, `if is_open is None: WARNING
  "state of issue #N unknown, not marking stale"; return False`.
  Keep `if not is_open` for the real "closed" case.

## HOW
- Import `raise_if_rate_limited` from `...workflow_utils.rate_limit`.
- Cache path (cached_issues hit) unchanged: always `bool`.
- Tests (TDD), with a mocked `IssueManager`:
  - `get_issue` raises `GithubException(401, …)` → `(None, None)`;
    `is_session_stale` → `False`; `is_issue_closed` → `False`.
  - `get_issue` returns `create_empty_issue_data()` → same results.
  - `get_issue` raises a rate-limit `GithubException` → `GitHubRateLimitError` propagates
    from `get_issue_current_status` and `is_session_stale`.
  - existing open/closed cases unchanged.
  - Through `_issue_facts` (session missing from cache, `_fetch_issue_individually`
    returns `None`, live fetch fails) → `IssueFacts.is_stale is False`.

## DATA
`tuple[str | None, bool | None]`.
