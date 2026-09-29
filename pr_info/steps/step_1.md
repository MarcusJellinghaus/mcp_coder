# Step 1 — Round cap on the task loop

See [summary.md](./summary.md). Independent of the other steps, and deliberately first: it is
the backstop for the one risk the progress predicate (Step 4) cannot cover — the count is
written by the agent, so deleting or regenerating tracker lines also lowers it — and it bounds
the loop while Steps 2–4 land, so no intermediate commit can leave an unbounded run.

## WHERE

- `src/mcp_coder/workflows/implement/core.py` (Step 4 loop, `:146`)
- `tests/workflows/implement/test_core_failure_routing.py`

## WHAT

No new function, no new reason, no new label. The `while True:` loop becomes bounded.

## HOW

- `progress.total` is already computed just above the loop (`:137-141`) from
  `get_step_progress`, inside a bare `except Exception: pass`. If that read fails, `total` stays
  0 and the cap falls back to 20 — which is the intended backstop behaviour, so that bare except
  is left alone.
- `progress.total` is **not** a count of remaining tasks: it sums every checkbox under a `### `
  header, completed ones and meta-tasks included. Since one round can complete a whole step,
  rounds ≈ number of steps ≪ `progress.total`. The cap is deliberately slack — a backstop, not a
  bound.
- Use `for ... else` rather than a manual counter: the loop already `break`s on `no_tasks`, so the
  `else` clause fires exactly when the cap is exhausted without that break, and the cap cannot be
  bypassed by a later edit that adds a `continue`.
- Reuse `fail("general", ...)`, which maps to the existing `implementing_failed` label.

## ALGORITHM

```
round_cap = max(progress.total + 10, 20)
for _ in range(round_cap):
    ... existing loop body, entirely unchanged ...
else:
    return fail("general", stage="Task implementation",
                message=f"Stopped after {round_cap} rounds without completing all tasks")
```

The body is not modified: the `break` on `no_tasks`, every `return fail(...)`, the
`progress.completed += 1` and the `log_progress_summary` call all stay as they are. Only the
`while True:` header and the new `else:` clause change.

## DATA

| Situation | Result |
|-----------|--------|
| `no_tasks` before the cap | `break` → the post-loop phases run, as today |
| any failure reason | that `fail(...)`, as today |
| cap exhausted | `fail("general", …)` → `implementing_failed`, exit 1 |

`round_cap` is `max(progress.total + 10, 20)`: 20 when the step-progress read fails or the
tracker is small.

## Tests (write first)

In `test_core_failure_routing.py`, patching `process_task_with_retry`, `get_step_progress`,
the prerequisites and the deliberate failure handler:

1. `get_step_progress` returning `{}` (so `total == 0`, cap 20) and `process_task_with_retry`
   returning `TaskOutcome(True, "completed")` forever → exit 1, `failure.category ==
   "implementing_failed"`, `failure.stage == "Task implementation"`, the message names the cap,
   and `process_task_with_retry.call_count == 20`.
2. A step progress of 100 checkboxes → the cap is 110, not 20 (assert via the message, or via a
   `side_effect` of 109 successes then `no_tasks`, which must still reach the post-loop phases and
   return 0).
3. 19 successes then `no_tasks` under a cap of 20 → exit 0 and no failure handler call: the cap
   does not fire one round early.

Existing tests need no change: every multi-round core test uses a `side_effect` list ending in a
terminal outcome, and every `return_value` in those files is already terminal — verified across
`test_core.py`, `test_core_workflow.py` and `test_core_failure_routing.py`.

## Checks

`run_format_code`, then pylint / pytest / mypy.

## LLM prompt

> Implement Step 1 of `pr_info/steps/step_1.md`, with `pr_info/steps/summary.md` for context.
> Write the tests first, then the implementation.
> Bound the `while True:` loop in `core.py` Step 4 with `round_cap = max(progress.total + 10, 20)`,
> using `for _ in range(round_cap): ... else: return fail("general", ...)` so the cap is structural
> rather than a counter someone can forget. Leave the loop body completely unchanged, including the
> `break` on `no_tasks`. The failure message must name the cap. Do not add a new reason string or a
> new label — reuse `fail("general", ...)`.
> Leave the bare `except Exception: pass` around the `get_step_progress` read above the loop alone:
> the 20-round fallback it produces is intended.
> Run `run_format_code`, then pylint, pytest and mypy; fix everything before finishing.
