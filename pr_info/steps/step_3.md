# Step 3 — The check loop logs each request with status, duration and summary (INFO)

Read `pr_info/steps/summary.md` first.

## WHERE

- `src/mcp_coder/workflows/implement/check_loop.py`: `_run_group`, plus the new
  `_one_line` and `_SUMMARY_MAX`
- `docs/architecture/toolkit-interface.md`: the "Implement fix loop" bullet
  "An `error` result aborts the run. `skipped` is logged and ignored."
- `tests/workflows/implement/test_check_loop.py`: new class `TestRequestLogging`

## WHAT

```python
_SUMMARY_MAX = 200

def _one_line(summary: str) -> str:
    """Put a result summary on one line, capped at ``_SUMMARY_MAX`` characters."""
```

`_run_group(loaded, project_dir, requests) -> str | None` keeps its signature
and return value.

## HOW

Add `import time` to `check_loop.py`. Restructure the loop body of `_run_group`:

```python
for request in requests:
    start = time.perf_counter()
    result = run_request(loaded, project_dir, request)
    if result.status == "skipped":
        logger.info("%s skipped: %s", request, result.summary)
        continue
    logger.info(
        "%s: %s (%.1f s): %s",
        request, result.status, time.perf_counter() - start, _one_line(result.summary),
    )
    if result.status == "error":
        raise _CheckAbort(f"{request}: {result.summary}")
    if result.status == "findings":
        texts.append(result.fix_text or result.summary)
```

- The INFO line is written before `_CheckAbort` is raised.
- `check_and_fix` keeps its ERROR line `Check run failed: …`.
- `skipped` keeps exactly its current line.

## ALGORITHM

```
text = summary.replace("\n", ", ")
if len(text) <= _SUMMARY_MAX: return text
return text[: _SUMMARY_MAX - 1] + "…"
```

## DATA

An example INFO message:
`check@standard: findings (12.4 s): npm run typecheck: ok, npm run lint: findings`.

## Docs

In `docs/architecture/toolkit-interface.md`, replace the bullet with:

> - Each request logs one INFO line, `<request>: <status> (<s> s): <summary>`,
>   with the summary on one line and capped at 200 characters. `skipped` logs
>   `<request> skipped: <summary>` and is ignored. An `error` result aborts the
>   run.

## Tests (write first)

Add `class TestRequestLogging` to `tests/workflows/implement/test_check_loop.py`.
It uses the `env` fixture and `caplog.at_level("INFO", logger=_CL)`.

1. `test_one_info_line_per_request`, parametrized over `ok`, `findings` and
   `error`:
   - The result has `summary="a: ok\nb: " + status`.
   - `env.binding("check@quick")`, and `env.run.return_value` is that result.
     For `findings`, also give it a `Finding`, as `_findings` does.
   - Exactly one INFO record matches the regex
     `^check@quick: <status> \(\d+\.\d s\): a: ok, b: <status>$`.
   - For `error`, there is also an ERROR record containing
     `Check run failed: check@quick`.
2. `test_long_summary_capped`: a summary of `"x" * 500` gives a message that ends
   with `"…"`. The summary part is exactly 200 characters long; import
   `_SUMMARY_MAX` from the module and compare against it.
3. `test_skipped_keeps_its_line`: a `skipped` result with summary `"not set up"`
   logs `check@quick skipped: not set up`, and no record matches the
   `(\d+\.\d s)` pattern.

Keep `test_check_loop.py` under 750 lines (it is about 367 now).

## LLM prompt

> Implement Step 3 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_3.md`.
>
> 1. Write `TestRequestLogging` in
>    `tests/workflows/implement/test_check_loop.py` and see it fail.
> 2. Add `_SUMMARY_MAX` and `_one_line` to
>    `src/mcp_coder/workflows/implement/check_loop.py` and restructure the loop
>    in `_run_group` so every non-skipped request logs one INFO line before an
>    `error` aborts.
> 3. Update the fix-loop bullet in `docs/architecture/toolkit-interface.md`.
> 4. Run `run_format_code`, then pylint, mypy and pytest (fast unit set with
>    `-n auto`), and fix any findings.
> 5. Commit as one commit: `feat(implement): log each check request with status, duration and summary`.
