# Step 6 — Gate 2: exit guard (CI proven green)

**Read first:** `pr_info/steps/summary.md` (§ Behaviour matrix, § "Gate 2").
**Depends on Steps 1–5** (`assess_ci`, `ci_unknown` label + failure entry,
`enforce_implementation_gates`, `_fail` `details`, and `gates.py` from Step 5).
One vertical slice: gate function + wiring into the dismiss cascade + tests.

## WHERE

- **Modified:** `src/mcp_coder/workflows/review/gates.py` (add second function)
- **Modified test:** `tests/workflows/review/test_gates.py`
- **Modified:** `src/mcp_coder/workflows/review/core.py`

## WHAT

```python
# gates.py — new function
from mcp_coder.checks.branch_status import CIStatus, collect_branch_status
from mcp_coder.checks.ci_policy import assess_ci

def check_ci_proven_gate(project_dir: Path) -> tuple[str | None, str | None]:
    """Return (reason, details): (None, None) if CI proven green,
    ("ci", <msg>) if determinably red, ("ci_unknown", <msg>) otherwise."""
```

## HOW / integration points

- **Exactly one** `collect_branch_status(project_dir)` call — no retry loop.
- Caller gates on `config.enforce_implementation_gates`, so `check_ci_proven_gate`
  itself takes only `project_dir` (keeps it pure/testable).
- **Wire into `core.py`** in the `verdict.decision == "dismiss"` branch, right
  after `_after_steps(..., is_dismiss=True)` and **before** the existing
  `if reason == "rebase":` / `if reason:` handling:

```python
reason = _after_steps(config, project_dir, ..., is_dismiss=True)
details: str | None = None
if reason is None and config.enforce_implementation_gates:
    reason, details = check_ci_proven_gate(project_dir)
if reason == "rebase":
    ...  # unchanged
if reason:
    write_round_log(...)      # unchanged
    _flush_round_log(project_dir)
    return _fail(config, project_dir, reason, ..., details=details, ...)  # add details=details
```

  Add `details=details` to that existing dismiss-branch `_fail(...)` call only.
  For non-gate-2 reasons (`"ci"`/`"timeout"`/`"general"` from `_after_steps`)
  `details` is `None`, so their comments are unchanged. Add
  `from .gates import check_ci_proven_gate` to imports (extend Step 5's import).

## ALGORITHM (check_ci_proven_gate)

```
status = collect_branch_status(project_dir).ci_status
verdict = assess_ci(status, require_proven=True)
if verdict == "ok":     return None, None
detail = (f"CI status is `{status.value}` — could not prove CI ran green. "
          f"Check the GitHub token and whether this repo has a CI workflow.")
if verdict == "failed": return "ci", detail        # determinably red → existing 17f-ci
return "ci_unknown", detail                          # PENDING/NOT_CONFIGURED/UNKNOWN/UNAVAILABLE
```

## DATA

- Returns `(None, None)` | `("ci", details)` | `("ci_unknown", details)`.
- `"ci"` → `status-17f-ci` (unchanged label); `"ci_unknown"` → `status-17f-ci-unknown`.
- Both non-clean outcomes are terminal, RC=1.

## TDD — `tests/workflows/review/test_gates.py`

Patch `mcp_coder.workflows.review.gates.collect_branch_status` to return a report
with each `ci_status`:

- `PASSED` → `(None, None)`; assert `collect_branch_status` called **once**.
- `FAILED` → `("ci", details)`.
- `PENDING`, `NOT_CONFIGURED`, `UNKNOWN`, `UNAVAILABLE` → each `("ci_unknown", …)`,
  details naming the observed status.

`core`-level tests (extend `tests/workflows/review/test_core.py` or a dismiss-path
test): drive a dismiss verdict with `_after_steps` returning `None` and
`collect_branch_status` stubbed:

- `PASSED` → success label applied, RC=0.
- `NOT_CONFIGURED`/`PENDING`/`UNKNOWN`/`UNAVAILABLE` → RC=1, `code_review_ci_unknown`
  label, and `_flush_round_log` ran before `_fail` (guard runs before the push).
- `FAILED` → RC=1, `code_review_ci` (not conflated with ci_unknown).
- `REVIEW_PLAN` dismiss path → gate skipped, success unchanged.

## Checks

pylint / pytest / mypy green. Confirm `core.py` still < 600 lines.

## Commit

`Add CI-proven exit guard to review-implementation dismiss gate`
