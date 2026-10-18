# Implementation plan — issue #1183

Harden `review-implementation`'s CI poll against GitHub lookup failures, and
make the `check_ci_proven_gate` failure message name the actual observed
`CIStatus` instead of one generic "check the token" message.

## Problem recap

- `_poll_for_ci_completion` treats **every** raised exception from
  `get_latest_ci_status` as "CI passed" (`return None, True`). A transient
  GitHub rate-limit/auth error mid-poll is silently swallowed as a pass, and
  the gate's own single follow-up call then hits the same failure mode and
  reports a misleading, generic `ci_unknown` message.
- Since upstream `mcp-workspace#318`, a swallowed lookup failure (5xx,
  network, repo-lookup failure) can surface as an otherwise-empty `run` dict
  carrying `lookup_failed=True` — the poll does not look at that flag at all,
  so it either spins for the full ~12.5 minute cap or (depending on dict
  shape) never recognises the condition.
- `check_ci_proven_gate` has one canned message for every non-`PASSED`,
  non-`FAILED` status, always telling the user to "check the token", even
  when the real status is `PENDING` or a transient `UNKNOWN`.

## Architectural / design changes

1. **One shared, pure classifier function** — `_classify_ci_exception(exc) ->
   str` in `workflow_steps/ci.py`. Both exception sites (`_poll_for_
   ci_completion`'s existing `except Exception` branch and
   `_wait_for_new_ci_run`'s) call it to build the same kind of INFO log
   detail, instead of duplicating status/header inspection twice. It never
   changes control flow — a raised exception always exits immediately
   without retry, exactly as it does today; only the log line's content
   becomes specific (GitHub rate limit w/ reset time, auth/permission, or a
   generic "unexpected error" for a non-`GithubException`).
2. **`GithubException` becomes a shim re-export**, alongside the existing
   `CIResultsManager`/`CIStatusData` symbols in `mcp_workspace_github.py`. No
   direct `github` (PyGithub) import is added anywhere in `mcp_coder` — the
   import-linter contract `github_library_isolation` keeps forbidding that.
   Classification is done by `exc.status` + headers, not by catching a PyGithub
   subclass, because `RateLimitExceededException` itself cannot be
   re-exported (mcp-workspace's `github_operations` package doesn't export it).
3. **`lookup_failed` gets its own small, bounded retry budget inside the
   existing poll loop**, not a separate code path. The poll already has one
   "keep waiting, bounded by a sub-budget" branch (for the "run belongs to
   another commit" case); `lookup_failed` is folded into that same branch
   with its own counter (`CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS = 3`, reusing the
   existing 15s poll interval — no new API load). The counter resets on any
   non-`lookup_failed` read and is local to one `_poll_for_ci_completion`
   call. **Correctness detail that drives the implementation:** once a
   lookup-failure run carries `{"lookup_failed": True}`, the run dict is no
   longer *empty* (`len(run_info) == 0` is `False`), so `lookup_failed` must
   be checked as its own top-level condition — not nested inside the
   existing `len(run_info) == 0` branch — or the new flag would silently fall
   through into the unrelated "CI run in progress" branch and poll for the
   full cap anyway.
4. **`check_ci_proven_gate` message becomes a per-`CIStatus` lookup** —
   `dict[CIStatus, str]` with `.get(status, <generic fallback>)` — rather than
   an if/elif chain. Only `UNAVAILABLE`'s message mentions the GitHub token;
   `PENDING`/`UNKNOWN`/`NOT_CONFIGURED` get their own hedged wording, and any
   future `CIStatus` member falls through to the generic fallback for free.
5. **Round log fidelity**: the dismiss-gate failure call site in `core.py`
   passes `changes=details or reason` to `write_round_log` instead of the
   bare reason code, so the committed round log carries the same
   human-readable detail the failure comment does. `escalate_reason=reason`
   is unchanged (the machine-readable code still drives the failure label).

## Non-goals (explicitly out of scope)

- No change to `CIResultsManager`'s constructor or its `check_and_fix_ci`
  call site (~L582) — no API call there, failures are deterministic
  `ValueError`s, nothing to classify.
- No change to `check_branch_status.py` or anything about carrying a
  swallowed error's *cause* (`lookup_error`) — tracked separately in
  mcp-workspace#327, non-blocking.
- No retry loop added to the gate itself — it stays a single, instant call;
  robustness lives entirely in the poll.

## Folders / modules / files touched

| Path | Change |
|---|---|
| `src/mcp_coder/mcp_workspace_github.py` | Add `GithubException` to the re-export list and `__all__`. |
| `src/mcp_coder/workflow_steps/constants.py` | Add `CI_LOOKUP_FAILED_MAX_POLL_ATTEMPTS = 3`. |
| `src/mcp_coder/workflow_steps/ci.py` | Add `_classify_ci_exception`; wire it into `_poll_for_ci_completion`'s exception branch and `_wait_for_new_ci_run`; add the `lookup_failed` counter/branch to `_poll_for_ci_completion`. |
| `src/mcp_coder/workflows/review/gates.py` | Replace the single `ci_unknown` message with a per-`CIStatus` dict + generic fallback; update the docstring. |
| `src/mcp_coder/workflows/review/core.py` | `changes=details or reason` at the dismiss-gate-failure `write_round_log` call. |
| `tests/test_mcp_workspace_github_smoke.py` | Bump `__all__` count; assert `GithubException` importable. |
| `tests/workflow_steps/test_ci.py` | New tests: classifier (rate-limit w/ and w/o headers, auth, non-`GithubException`); poll exception-branch wiring; `lookup_failed` counter increment/reset/exhaustion + pre-#318 (no-key) regression; `_wait_for_new_ci_run` no-retry-on-exception. |
| `tests/workflows/review/test_gates.py` | Split the 4-status parametrized test into one assertion per status; add a generic-fallback test. |
| `tests/workflows/review/test_core_gates.py` | New test: `details` reaches `write_round_log`'s `changes`; a separate after-steps-originated failure falls back to the bare `reason`. |

## Step order

1. `_classify_ci_exception` helper + `GithubException` shim re-export (pure function, TDD in isolation).
2. Wire the classifier into `_poll_for_ci_completion`'s existing exception branch.
3. `lookup_failed` counter + new constant, folded into the poll's existing waiting branch.
4. Wire the classifier + immediate no-retry exit into `_wait_for_new_ci_run`.
5. Per-`CIStatus` gate messages in `check_ci_proven_gate`.
6. `core.py` round-log `changes=details or reason`.

Each step is one commit: tests first, then the implementation that makes them
pass, then the repo's quality checks (pylint, pytest, mypy).
