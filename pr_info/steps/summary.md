# Summary: Workflow failure banner logged at ERROR (Issue #738)

## Problem

When a workflow fails, the final **"WORKFLOW FAILED"** summary banner is logged at
`INFO` instead of `ERROR`. The most visible "this failed" message is therefore not
highlighted as an error, even though the underlying failure *causes* are already
logged at `ERROR` by each workflow's `core.py`.

`handle_workflow_failure()` in `src/mcp_coder/workflow_utils/failure_handling.py`
is the shared handler used by all three workflows (`implement`, `create_plan`,
`create_pr`). It logs the six-line banner via `logger.info(...)`. The banner exists
**only** here, so a single edit corrects the highlighting everywhere.

## Fix

1. **Banner → ERROR.** Change the six banner lines (two `===` separators +
   `WORKFLOW FAILED` / `Category` / `Stage` / `Error`) from `logger.info(...)` to
   `logger.error(...)`. Keep them as six separate calls (one log record per line) so
   the output format is unchanged — only the level differs.
2. **IssueManager-creation fallback → ERROR.** This branch does an early `return`,
   abandoning both the label update and the comment, so it aborts the handler's
   remaining work.
3. **Leave the other three fallbacks at `WARNING`** — branch-extraction, label update,
   and comment posting each degrade one step but let the handler continue.
4. **Harden the test** so the level cannot silently regress.

### Fallback level rule

> **Error** if the fallback aborts the handler's remaining work (`return`);
> **warning** if the handler continues.

| Log site | Before | After | Reason |
|----------|--------|-------|--------|
| Six banner lines | `info` | `error` | The workflow failed |
| Failed to create IssueManager | `warning` | `error` | Early `return` — aborts handler |
| Failed to extract issue number from branch | `warning` | `warning` | Continues; label update still runs |
| Failed to update issue label | `warning` | `warning` | Continues to comment step |
| Failed to post failure comment | `warning` | `warning` | Last step; handler finishes |

## Architectural / design changes

**None.** This is a logging-severity alignment only. No new modules, functions,
signatures, control flow, or public API. The banner remains six separate log records;
`handle_workflow_failure()` keeps its exact signature and behavior. The fallbacks still
fire only on the already-failed path and only report whether the best-effort GitHub
side-effects (relabel / comment) succeeded.

## Scope / non-goals

- **Log levels only.** Exit codes are out of scope and must **not** change. They are
  determined solely by `return 0` / `return 1` in each workflow's `core.py`
  (e.g. `implement/core.py:811`), never by `handle_workflow_failure()`, which only
  logs, labels, and posts comments. The failing-CI case already exits with code 1.
- The genuine failure *causes* are already logged at `ERROR` in the workflow core;
  this change only aligns the shared summary banner with that.

## Files created / modified

| Path | Action | Notes |
|------|--------|-------|
| `pr_info/steps/summary.md` | created | This document |
| `pr_info/steps/step_1.md` | created | Implementation step |
| `src/mcp_coder/workflow_utils/failure_handling.py` | modified | 6 banner lines + 1 fallback: `info`/`warning` → `error` |
| `tests/workflow_utils/test_failure_handling.py` | modified | Harden `test_logs_failure_banner` with a level assertion |

No folders or modules are created; no files are deleted or moved.
