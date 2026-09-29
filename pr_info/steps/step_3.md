# Step 3 — Failure surface for `no_progress_after_retries`

See [summary.md](./summary.md). Depends on Step 2, which produces the reason. Gives it a label,
a comment category and a route in `core.py`, and fixes the neighbouring `error` branch that
throws away its detail.

## WHERE

- `src/mcp_coder/workflows/implement/failure_reporting.py`
- `src/mcp_coder/workflows/implement/core.py`
- `tests/workflows/implement/test_failure_reporting.py`
- `tests/workflows/implement/test_core_failure_routing.py`

## WHAT

Two dict entries in `failure_reporting.py`:

```python
FAILURE_LABELS["no_progress_after_retries"] = "no_changes_after_retries"   # existing label id
CATEGORY_DISPLAY["no_progress_after_retries"] = "No Progress After Retries"
```

Two edits in `core.py`'s failure chain (`:156-205`).

## HOW

- **Reuse the existing label.** `labels.json`, `define_labels.py`, `test_define_labels.py`, the
  docs table and the workflow-matrix HTML are **not** touched: the operator action is identical
  for both reasons. `tests/config/test_label_config.py:172` already lists the label id and needs
  no change.
- There is no exhaustive key-set test over `FAILURE_LABELS` / `CATEGORY_DISPLAY`, so adding a
  reason touches only the two dicts plus one new assertion.
- **The failure chain has no `else`.** `core.py:156-205` is a chain of `if`s; an unrouted reason
  falls through to `progress.completed += 1` at `:207` and loops again. `no_progress_after_retries`
  must be routed or it becomes a silent loop.
- Place the new branch immediately next to the `no_changes_after_retries` branch at `:189`.

## ALGORITHM

New branch in `core.py`, beside `:189`:

```
if outcome.reason == "no_progress_after_retries":
    msg = (f"No task was completed after {MAX_NO_CHANGE_RETRIES} attempts"
           f" (files changed, but no checkbox in pr_info/TASK_TRACKER.md was ticked)")
    if outcome.detail:
        msg += f" — last task: {outcome.detail}"
    return fail("no_progress_after_retries", stage="Task implementation", message=msg)
```

The `error` branch at `:199-205` currently hardcodes `message="Task processing failed"` and drops
`outcome.detail`, which would discard Step 1's tracker message:

```
return fail("general", stage="Task implementation",
            message=outcome.detail or "Task processing failed")
```

Plain fallback, not `append_detail`: `append_detail` renders "(agent reported: …)", which is the
wrong framing for a tracker read error. Every other `error` producer returns an empty detail, so
the old message survives for them and the existing routing test keeps passing unchanged.

## DATA

| Reason | Label id | Category line |
|--------|----------|---------------|
| `no_progress_after_retries` | `no_changes_after_retries` | `No Progress After Retries` |
| `error` with detail | `implementing_failed` | `General`, message = the detail |
| `error` without detail | `implementing_failed` | `General`, message = `Task processing failed` |

Exit code 1 in every case, via the existing `_fail`.

## Tests (write first)

`test_failure_reporting.py`:

1. `FAILURE_LABELS["no_progress_after_retries"] == "no_changes_after_retries"` — the two reasons
   deliberately share one label.
2. `CATEGORY_DISPLAY["no_progress_after_retries"] == "No Progress After Retries"`.
3. `format_failure_comment("no_progress_after_retries", ...)` renders that category text — i.e.
   it does not fall back to `General`.

`test_core_failure_routing.py`, following the `test_no_changes_after_retries_routes_to_failure`
pattern at `:105`:

4. `TaskOutcome(False, "no_progress_after_retries", "Step 2: …")` → exit 1, `failure.category ==
   "no_changes_after_retries"`, `failure.stage == "Task implementation"`, and the task name
   appears in the posted comment body.
5. `TaskOutcome(False, "error", "Cannot read pr_info/TASK_TRACKER.md: …")` → category
   `implementing_failed` and `"TASK_TRACKER.md"` in the message.
6. `TaskOutcome(False, "error")` with no detail → message is still `"Task processing failed"`
   (regression guard for the existing test at `:157`).

## Checks

`run_format_code`, then pylint / pytest / mypy.

## LLM prompt

> Implement Step 3 of `pr_info/steps/step_3.md`, with `pr_info/steps/summary.md` for context.
> Steps 1 and 2 must be complete first. Write the tests first, then the implementation.
> Add `no_progress_after_retries` to `FAILURE_LABELS` (mapped to the **existing**
> `no_changes_after_retries` label id) and to `CATEGORY_DISPLAY`. Do not create a new label and do
> not touch `labels.json`, `define_labels.py`, the docs table or the workflow-matrix HTML.
> Route the new reason in `core.py`'s failure chain next to the `no_changes_after_retries` branch —
> the chain has no `else`, so an unrouted reason silently loops. Include the retry count and the
> task name from `outcome.detail` in the message.
> Change the neighbouring `error` branch to use `outcome.detail or "Task processing failed"` so
> Step 1's tracker message reaches the failure comment; use a plain fallback, not `append_detail`.
> Run `run_format_code`, then pylint, pytest and mypy; fix everything before finishing.
