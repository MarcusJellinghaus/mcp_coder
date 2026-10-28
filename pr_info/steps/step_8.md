# Step 8 — vscodeclaude entry points: `launch` and `status` under a rate limit

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_8.md`).
> Implement only Step 8. Tests first, then code.
> Run pylint, pytest (fast unit marker set, `-n auto`) and mypy; all must pass.
> Produce exactly one commit.

## WHERE
- `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py`
- `src/mcp_coder/workflows/vscodeclaude/assessment.py` (`build_assessments`, ~lines 274-279)
- tests: `tests/cli/commands/coordinator/test_vscodeclaude_cli.py`,
  `tests/workflows/vscodeclaude/test_explain.py`, `tests/workflows/vscodeclaude/test_assessment_orchestration.py`

## WHAT
1. `_build_cached_issues_by_repo`: first line of the broad `except` (~146) is
   `raise_if_rate_limited(e)`.
2. `build_assessments`: move the `get_github_username()` try/except inside the
   `if cached_issues_by_repo:` branch (computed once, lazily, before the loop is
   fine: `github_username = _username() if cached_issues_by_repo else None`).
   With no cache it makes no GitHub call at all.
3. `execute_coordinator_vscodeclaude` — one local variable, no other new state:

## ALGORITHM (launch)
```
rate_limited: GitHubRateLimitError | None = None
try:   cached = _build_cached_issues_by_repo(...)[0]; assessments = build_assessments(sessions_list, cached)
except Exception as exc: rate_limited = _rate_limit_or_raise(exc); cached = {}; assessments = build_assessments(sessions_list, None)
cleanup_stale_sessions(...)                       # unchanged, disk only
restarted = []
if rate_limited is None:
    try: restarted = restart_closed_sessions(...)
    except Exception as exc: rate_limited = _rate_limit_or_raise(exc)
log restarted; apply_assessments(assessments, sessions_list, write_audit=True)   # always
if rate_limited: log_rate_limit_stop(rate_limited); return 0
try: <existing repo loop: check_pr_health + process_eligible_issues> + summary
except Exception as exc: log_rate_limit_stop(_rate_limit_or_raise(exc)); return 0
```
Module-private helper:
```python
def _rate_limit_or_raise(exc: Exception) -> GitHubRateLimitError:
    """Return the rate limit behind exc; re-raise exc if it is not one."""
```
(`rl = as_rate_limit(exc); if rl is None: raise exc; return rl`). Keep the
existing outer `try/except ValueError/Exception` unchanged.

## ALGORITHM (status)
```
try:
    cached = _build_cached_issues_by_repo(...)[0]; assessments = build_assessments(sessions, cached)
    if explain: log render_explain; return 0
    eligible, without_branch = build_eligible_issues_with_branch_check(...)
except Exception as exc:
    log_rate_limit_stop(_rate_limit_or_raise(exc)); return 0     # only this line, no table
display_status_table(...); return 0
```

## HOW
- Imports from `....workflow_utils.rate_limit` and `....mcp_workspace_github`.
- `as_rate_limit` checks `__cause__`, so the `ValueError` from `GET /user`
  (e.g. `session_launch.py:377`) is recognised here.
- Tests (TDD), mocking the workflow functions in the `commands_vscodeclaude` module:
  - launch, `_build_cached_issues_by_repo` raises `GitHubRateLimitError`:
    `build_assessments` called with `None`, `cleanup_stale_sessions` and
    `apply_assessments` called, `restart_closed_sessions`, `check_pr_health`,
    `process_eligible_issues` not called, exit 0, one reset log line.
  - launch, `restart_closed_sessions` raises → `apply_assessments` still called,
    PR health/launch skipped, exit 0.
  - launch, `check_pr_health` raises on repo 1 → repo 2 not processed, exit 0.
  - launch, `process_eligible_issues` raises `ValueError` wrapping a rate limit → exit 0.
  - launch, non-rate-limit `RuntimeError` keeps today's behaviour (re-raised).
  - status / `status --explain` under a rate limit: output contains only the
    rate-limit line (no table / no explain text), exit 0.
  - `build_assessments(sessions, None)` does not call `get_github_username`
    (acceptance: no GitHub call after a phase-1 limit).

## DATA
Exit codes unchanged except: rate limit → 0.
