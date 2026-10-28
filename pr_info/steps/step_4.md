# Step 4 — CI gate: log the exception and return a comment-ready detail

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md` only
> (Steps 1–3 are done). TDD: adapt/write the tests first, then the code. Run
> pylint, mypy, pytest (`-n auto`, fast unit markers) and lint-imports; all must
> pass. Format, then make exactly one commit.

## Precondition

If `mcp_coder.workflow_utils.failure_handling.exception_summary` does not exist,
write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/workflows/review/steps.py` — `_after_steps`
- `src/mcp_coder/workflows/review/core.py` — dismiss caller (~305) and mid-loop
  caller (~545)
- `tests/workflows/review/test_steps.py`
- `tests/workflows/review/test_core_after_steps.py`
- `tests/workflows/review/test_core_failure_detail.py`

## WHAT

```python
def _after_steps(...) -> tuple[str | None, RebaseOutcome | None, str | None]:
```

Third element: comment-ready failure detail, set only when the CI call raised.
Update the docstring's Returns section.

## HOW

- `steps.py`: extend the `failure_handling` import with `exception_summary`; import
  `comment_safe` from `mcp_coder.llm.error_summary`.
- Every return point returns a 3-tuple (`None, None, None`; `"rebase", outcome, None`;
  `None, outcome, None`; `"ci", outcome, None`).
- The rebase gate stays **outside** the `try` (pinned by
  `test_broadened_ci_except_does_not_swallow_rebase` and the #1266 source check).
- core.py dismiss path:
  `reason, rebase_outcome, ci_detail = _after_steps(...)`; keep `details = None` /
  Gate 2 as is; `write_round_log(changes=details or reason, ...)` unchanged; the
  `_fail` call gets `details=details or ci_detail`. Do **not** assign `ci_detail`
  into `details`.
- core.py mid-loop path: `reason, rebase_outcome, ci_detail = _after_steps(...)`;
  in the `elif reason:` branch keep `changes=reason` and add `details=ci_detail` to
  `_fail`.
- Never pass `exc=` on these paths — the traceback is logged once, in `steps.py`.

## ALGORITHM (`except` in `_after_steps`)

```
except Exception as exc:
    logger.error("CI gate raised; failing the review", exc_info=True)
    reason = llm_failure_reason(exc) or "general"
    return reason, outcome, comment_safe(exception_summary(exc))
```

## DATA

`(reason, outcome, detail)` — `detail` is `str` (≤ 300 chars, no stream-file path)
only on the CI exception path, else `None`.

## Tests

- `test_steps.py` (~34): expect `("rebase", outcome, None)`.
- `test_core_after_steps.py`:
  - `test_dismiss_ci_generic_exception_fails_general` (~287): also assert
    `"RuntimeError: ci boom"` in `env.handle_workflow_failure.call_args.args[1]`
  - `test_tasks_after_steps_general_writes_and_flushes_round_log` (~576): same
    assertion; the existing `"general" in log` stays
- `test_core_failure_detail.py` (default `REVIEW_IMPLEMENTATION` lane):
  - dismiss path, `check_and_fix_ci.side_effect = RuntimeError("ci boom")`: round log
    Changes value is exactly `"general"` (summary not in the committed log)
  - `caplog.at_level(logging.ERROR)` across both loggers: exactly one record with
    `exc_info` set, logged by `steps.__name__`
  - `CalledProcessError(1, "gh", stderr="ci err Stream file: /p")` from
    `check_and_fix_ci`: comment contains `"ci err"`, not `"Stream file"`
- `test_core_gates.py::test_after_steps_failure_falls_back_to_bare_reason` must keep
  passing unchanged (red CI → Changes `"ci"`).
- Keep `test_core_after_steps.py` under 750 lines.
