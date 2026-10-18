# Step 1 — shared exception classifier + `GithubException` shim re-export

Part of issue #1183. Read `pr_info/steps/summary.md` first for the full
design rationale.

## Precondition

`GithubException` must be importable as
`from mcp_workspace.github_operations import GithubException` in this
environment's installed `mcp_workspace` package. If it is not (e.g. the
symbol has been renamed/removed upstream), write one line to
`pr_info/.blocked.txt` describing the missing symbol and stop.

## Goal

Add one pure, shared helper — `_classify_ci_exception` — that turns a raised
exception into a human-readable classification string (GitHub rate limit /
auth-permission / generic unexpected error), without changing any control
flow yet. This step only adds the helper and its tests; wiring it into the
two call sites is Steps 2 and 4.

## TDD order

1. Write the shim test first (`tests/test_mcp_workspace_github_smoke.py`).
2. Write `tests/workflow_steps/test_ci.py::TestClassifyCiException` (new
   class) — all cases below, named individually.
3. Implement `GithubException` re-export, then `_classify_ci_exception`,
   until all new tests pass.

## WHERE

- `src/mcp_coder/mcp_workspace_github.py` — add `GithubException` to the
  existing `from mcp_workspace.github_operations import (...)` block
  (alphabetical: after `CIStatusData`, before `LabelData`) and to `__all__`
  in the same place, with a one-line comment explaining why it's re-exported
  here (no direct `github` import allowed by the `github_library_isolation`
  import-linter contract).
- `src/mcp_coder/workflow_steps/ci.py` — add imports:
  `from datetime import datetime, timezone` and add `GithubException` to the
  existing `from mcp_coder.mcp_workspace_github import (CIResultsManager,
  CIStatusData)` block. Add the new private function near the top of the
  module, just above `_poll_for_ci_completion` (so both of its future callers
  are close by).

## WHAT

```python
def _classify_ci_exception(exc: Exception) -> str:
    """Classify a raised CI-lookup exception for the INFO diagnostic line."""
```

Signature: takes the raw exception, returns a plain string (no logging side
effect — callers do the `logger.info(...)` themselves so the `CI_API_ERROR`
prefix stays visible at the call site, not buried in this helper).

## HOW

- Not a decorator, not a class — a plain module-level function, imported
  nowhere else outside `ci.py` in this step (Steps 2 and 4 call it from the
  same module).
- No new dependency: classification is by `exc.status` (an `int`) and
  `exc.headers` (a `dict[str, str] | None`), both already on `GithubException`
  — no PyGithub subclass check (`RateLimitExceededException` cannot be
  imported per the summary's rationale).

## ALGORITHM

```
if exc is not a GithubException:
    return "unexpected error: {exc}"
normalize exc.headers (or {}) to a lowercase-keyed dict
is_rate_limit = exc.status in (403, 429) and
                ("retry-after" in headers or headers.get("x-ratelimit-remaining") == "0")
if is_rate_limit:
    describe reset time from "retry-after" (seconds) or "x-ratelimit-reset"
    (epoch -> readable UTC time via datetime.fromtimestamp(..., tz=timezone.utc))
    falling back to "reset time unknown" if neither header is present
    return "GitHub rate limit hit (status {status}, {when}): {exc}"
return "GitHub auth/permission error (status {status}): {exc}"
```

Header lookup must be case-insensitive and defensive: `getattr(exc,
"headers", None) or {}`, then `{k.lower(): v for k, v in that_dict.items()}`.
Missing/`None` headers must not raise — they just produce the "reset time
unknown" / no-rate-limit branch.

## DATA

Returns a single `str`. No new data structures. Example outputs:

- `"GitHub rate limit hit (status 403, resets at 2026-10-18T12:00:00+00:00): 403 ..."`
- `"GitHub rate limit hit (status 403, retry after 30s): 403 ..."`
- `"GitHub rate limit hit (status 403, reset time unknown): 403 ..."` (headers present but neither usable key)
- `"GitHub auth/permission error (status 401): 401 ..."`
- `"unexpected error: <ValueError message>"`

## Tests to add

`tests/test_mcp_workspace_github_smoke.py`:
- Bump the `__all__` length assertion in `test_all_exports_defined` by 1.
- Add `GithubException` to the import list in `test_key_symbols_importable`
  and assert `GithubException is not None`.

`tests/workflow_steps/test_ci.py` — new `TestClassifyCiException` class,
constructing `GithubException(status=..., data=None, headers=...)` directly
(imported from `mcp_coder.mcp_workspace_github`):

- `test_rate_limit_with_retry_after_header` — status 403,
  `headers={"Retry-After": "30"}` → result contains `"rate limit"` and
  `"30"`.
- `test_rate_limit_with_remaining_zero_and_reset_header` — status 429,
  `headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1700000000"}`
  → result contains `"rate limit"` and an ISO-formatted UTC timestamp (don't
  hardcode the exact string across machines — assert on `"resets at"` plus a
  `T` and `+00:00` substring, or compute the expected ISO string from the
  same epoch in the test).
- `test_rate_limit_status_without_matching_headers_is_not_rate_limit` —
  status 403, `headers={}` (or `None`) → result contains `"auth/permission"`,
  NOT `"rate limit"`.
- `test_auth_status_without_headers` — status 401, `headers=None` → result
  contains `"auth/permission"`, does not raise.
- `test_non_github_exception_is_generic` — `ValueError("boom")` → result
  equals `"unexpected error: boom"` (or contains `"unexpected error"` and
  `"boom"`), never contains `"auth/permission"` or `"rate limit"`.

## Commit

One commit: shim re-export + `_classify_ci_exception` + all tests above,
passing pylint/pytest/mypy.

## LLM prompt

> Implement Step 1 of `pr_info/steps/summary.md` (issue #1183) exactly as
> described in `pr_info/steps/step_1.md`. Follow TDD: write the listed tests
> first (they must fail), then add the `GithubException` re-export and the
> `_classify_ci_exception` helper until they pass. Do not wire the helper
> into `_poll_for_ci_completion` or `_wait_for_new_ci_run` yet — that is
> Steps 2 and 4. Run pylint, pytest (`-n auto` with the standard
> integration-marker exclusions), and mypy; all must pass. Make exactly one
> commit.
