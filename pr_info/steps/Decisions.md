# Plan Decisions (Issue #713)

Round-2 review findings applied to the implementation plan.

## Step 1 — `--from-status` flag

- **Replace `parser.error(...)` with `logger.error` + `return 2`.** `execute_set_status` has no `parser` in scope; the pseudocode was unreachable. Error-path style matches existing error returns in the function.
- **Test #8 asserts exit code 2 via `caplog`.** Existing error-path tests in `test_set_status.py` use `caplog` (not `capsys` / stderr), so the new test follows that pattern and asserts the exact message `"--from-status requires a positional status_label"`.
- **Documented dirty-wd ordering invariant.** Added an `INVARIANTS` section: the dirty working directory check runs before `_update_issue_labels`, so `--from-status` callers must pass `--force` to reach the skip path. Jenkins watchdog templates already do this.
- **Inlined the skip-message f-string in DATA.** The f-string is now shown explicitly at the skip point using `current_display = current_status_label or "<none>"`, preventing accidental rendering of `None` instead of `<none>`.

## Step 2 — Coordinator template watchdog

- **Added Windows RC-safety note.** Documented that RC is captured into a variable before the watchdog runs, so `exit /b %RC%` re-emits the original captured value. The Windows template intentionally has no `|| true` analog.
- **Tightened test #10 wording.** Dropped "or clearly equivalent wording"; the test now asserts the exact strings `Recovery matrix`, `Silent death`, and `Hard kill` since the implementer copies the comment block verbatim.
- **Added test #9 rationale.** Noted that missing required placeholders raise `KeyError` and would be caught by the strict-kwargs format call.

## summary.md

- **Noted the 3-tuple return change.** The `set_status.py` row in Files Modified now flags that the return shape changes to surface skip state.
