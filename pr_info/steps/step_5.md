# Step 5 — Rate-limit helper module and shim exports

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_5.md`).
> Implement only Step 5. Tests first, then code.
> Run pylint, pytest (fast unit marker set, `-n auto`) and mypy; all must pass.
> Produce exactly one commit.

## WHERE
- `src/mcp_coder/mcp_workspace_github.py`
- `src/mcp_coder/workflow_utils/rate_limit.py` (new)
- `tests/workflow_utils/test_rate_limit.py` (new)

## WHAT
Shim re-exports (add to `__all__`):
- `GitHubRateLimitError` from `mcp_workspace.github_operations`
- `to_rate_limit_error` from `mcp_workspace.github_operations.caching.errors`

`workflow_utils/rate_limit.py`:
```python
def as_rate_limit(exc: BaseException) -> GitHubRateLimitError | None: ...
def raise_if_rate_limited(exc: BaseException) -> None: ...
def log_rate_limit_stop(exc: GitHubRateLimitError) -> None: ...
```

## ALGORITHM
```
as_rate_limit(exc):
    if isinstance(exc, GitHubRateLimitError): return exc
    rl = to_rate_limit_error(exc)
    if rl is None and exc.__cause__ is not None: rl = to_rate_limit_error(exc.__cause__)
    return rl
raise_if_rate_limited(exc):
    rl = as_rate_limit(exc); if rl is exc: raise exc; if rl is not None: raise rl from exc
log_rate_limit_stop(exc):
    when = f"reset at {exc.reset_at:%Y-%m-%d %H:%M:%S %Z}" if exc.reset_at else "reset time unknown"
    logger.log(OUTPUT, "GitHub rate limit hit, stopping GitHub work: %s", when)
```

## HOW
- Import `OUTPUT` from `mcp_coder.utils.log_utils`; GitHub names from
  `mcp_coder.mcp_workspace_github`.
- Do not hand-roll status/header checks; `to_rate_limit_error` already covers
  403/429 with rate-limit headers, `RetryError` and GraphQL `RATE_LIMITED`.
- Tests (TDD), build real `GithubException` objects:
  - `GitHubRateLimitError` → returned unchanged;
  - `GithubException(403, {"message": "API rate limit exceeded"}, headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "<epoch>"})`
    → `GitHubRateLimitError` with `reset_at` set (adjust the construction to what
    `format_rate_limit_error` recognises — check it with `get_library_source`);
  - GraphQL: `GithubException(400, {"errors": [{"type": "RATE_LIMITED"}]})` → match, `reset_at is None`;
  - `ValueError("…")` raised `from` a rate-limit `GithubException` → match;
  - `GithubException(404, …)`, plain `ValueError` → `None`;
  - `raise_if_rate_limited` raises `GitHubRateLimitError` with `__cause__` set; no-op otherwise;
  - `log_rate_limit_stop` with and without `reset_at` (caplog: "reset at" / "reset time unknown").

## DATA
`GitHubRateLimitError` has `.message: str`, `.reset_at: datetime | None` (UTC).
