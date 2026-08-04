# Step 1 — `assess_ci` policy helper + CLI delegation

**Read first:** `pr_info/steps/summary.md` (§ "Architectural / design changes",
§ Behaviour matrix). This step creates the single source of truth for the CI
status→verdict policy and routes the three existing predicate copies through it.
**CLI exit codes must stay byte-identical.**

## WHERE

- **New:** `src/mcp_coder/checks/ci_policy.py`
- **New test:** `tests/checks/test_ci_policy.py`
- **Modified:** `src/mcp_coder/cli/commands/check_branch_status.py`
- **Modified test:** `tests/cli/commands/test_check_branch_status_exit_code.py`

## WHAT

```python
# src/mcp_coder/checks/ci_policy.py
from typing import Literal
from mcp_coder.checks.branch_status import CIStatus

def assess_ci(
    status: CIStatus, *, require_proven: bool
) -> Literal["ok", "failed", "undeterminable"]:
    ...
```

## HOW / integration points

- `ci_policy.py` imports `CIStatus` from `mcp_coder.checks.branch_status` (the
  existing re-export shim). No `tach.toml` change — both files are under the
  `mcp_coder.checks` module (`exact = false`).
- In `check_branch_status.py`, add `from ...checks.ci_policy import assess_ci`.
- Rewrite `_exit_code` so the **CI comparisons** delegate to `assess_ci(...,
  require_proven=False)`; keep the two `fail_on_reviews` branches at their current
  precedence (2 wins over 1 wins over 0).
- Replace the pre-`--fix` bail-out condition
  `if report.ci_status in (CIStatus.UNAVAILABLE, CIStatus.UNKNOWN):`
  with `if assess_ci(report.ci_status, require_proven=False) == "undeterminable":`
  (byte-identical: only `UNAVAILABLE`/`UNKNOWN` are undeterminable when
  `require_proven=False`).

## ALGORITHM (assess_ci)

```
if status is PASSED:  return "ok"
if status is FAILED:  return "failed"
if status in (UNKNOWN, UNAVAILABLE): return "undeterminable"
# PENDING, NOT_CONFIGURED, and any future member:
return "undeterminable" if require_proven else "ok"
```

New `_exit_code` body (review branches unchanged):

```
verdict = assess_ci(report.ci_status, require_proven=False)
if verdict == "undeterminable": return 2
if fail_on_reviews and report.pr_feedback_undeterminable: return 2
if verdict == "failed": return 1
if fail_on_reviews and report.pr_feedback_blocks_merge: return 1
return 0
```

## DATA

- `assess_ci` → `Literal["ok", "failed", "undeterminable"]`.
- `_exit_code` → `int` (2 / 1 / 0), unchanged for every input.

## TDD

1. **`tests/checks/test_ci_policy.py`** — parametrize all six `CIStatus` members ×
   `require_proven` ∈ {False, True}:
   - `PASSED → "ok"`, `FAILED → "failed"` (both `require_proven`).
   - `UNKNOWN`, `UNAVAILABLE → "undeterminable"` (both).
   - `PENDING`, `NOT_CONFIGURED → "ok"` when `False`, `"undeterminable"` when `True`.
2. **`tests/cli/commands/test_check_branch_status_exit_code.py`** — the existing
   `TestExitCodeContract` already covers the 2→1→0 table for both `flag` values;
   confirm it still passes unchanged after the refactor (regression). Add explicit
   cases if missing: `PENDING`/`NOT_CONFIGURED` → 0 for both flags (proves the
   `require_proven=False` mapping keeps them clean).

## Checks

Run pylint / pytest (`-n auto` + unit exclusions) / mypy. All green.

## Commit

`Add assess_ci CI-status policy helper and route CLI exit-code through it`
