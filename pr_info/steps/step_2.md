# Step 2 — Look up exit codes by range, unlisted `0` is `ok`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`.
> Step 1 is already done (`ExitCodes` alias and range keys exist in
> `config.py`). If `config.py` has no `ExitCodes` alias, write one line to
> `pr_info/.blocked.txt` and stop. Follow TDD: write the tests first, then add
> `exit_code_status` and use it in `toolkit.py`. Run pylint, pytest (`-n auto`,
> unit markers as in CLAUDE.md) and mypy; all must pass. Run the formatter,
> then make exactly one commit.

## WHERE

- `src/mcp_coder/toolkits/command/config.py` — add `exit_code_status`
- `src/mcp_coder/toolkits/command/toolkit.py` — `_run_step` uses it
- `tests/toolkits/command/test_config.py` (class `TestExitCodes`)
- `tests/toolkits/command/test_toolkit_run.py` (class `TestExitCodes`)

## WHAT

```python
def exit_code_status(table: ExitCodes, code: int) -> str:
    """Return the status the table maps `code` to.

    Keys never overlap, so the first match is the only one. A code no key
    matches is `ok` when it is 0 and `error` otherwise.
    """
```

## HOW

- `toolkit.py`: extend the import
  `from mcp_coder.toolkits.command.config import Step, exit_code_status, parse_config`
  and replace `status = step.exit_codes.get(res.return_code, "error")` with
  `status = exit_code_status(step.exit_codes, res.return_code)`.
  Nothing else in `toolkit.py` changes.

## ALGORITHM

```
for key, status in table.items():
    lo, hi = key if isinstance(key, tuple) else (key, key)
    if lo <= code <= hi:
        return status
return "ok" if code == 0 else "error"
```

## DATA

Returns one of `STATUSES` as `str` (callers already treat it that way).
Negative codes (POSIX signals) never match a key, so they are `error`.

## Tests (write first)

`tests/toolkits/command/test_config.py::TestExitCodes` — import
`exit_code_status`; one parametrized `test_exit_code_status` over
`(table, code, expected)`:

| table | code | expected |
|---|---|---|
| `{0: "ok", (1, 125): "findings"}` | 7 | `findings` |
| `{0: "ok", (1, 125): "findings"}` | 126 | `error` |
| `{1: "findings"}` | 0 | `ok` |
| `{0: "findings"}` | 0 | `findings` |
| `{(0, 5): "skipped"}` | 0 | `skipped` |
| `DEFAULT_EXIT_CODES` | 1 | `findings` |
| `DEFAULT_EXIT_CODES` | -1 | `error` |

`tests/toolkits/command/test_toolkit_run.py::TestExitCodes` — real runs via
the existing `fake_npm` / `_exit_script` / `_run` helpers:

1. `test_range_exit_codes`: scripts `lint` exiting 7 and `crash` exiting 126;
   steps with `exit_codes = {"0": "ok", "1-125": "findings"}` → `findings` for
   `lint`, `error` for `crash` (two depths, as in `test_custom_exit_codes`).
2. `test_unlisted_zero_is_ok`: script exiting 0 with
   `exit_codes = {"1": "findings"}` → `ok`.

Existing `test_unmapped_exit_code_is_error` and `test_custom_exit_codes` keep
passing unchanged.

## Done when

Tests pass, pylint/pytest/mypy clean, one commit, e.g.
`feat(toolkit): match exit codes against ranges; unlisted 0 is ok`.
