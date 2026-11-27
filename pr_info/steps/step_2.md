# Step 2 — remaining mypy `--strict` findings in `tools/`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`), then implement
> step 2 only. Typing-only changes: no behaviour change. Run the checks listed below and
> commit (one commit).

## Tests

None new. These are type-level fixes with no behaviour change; mypy is the test. The
existing `tests/tools/` suite must still pass.

## WHERE / WHAT / HOW

| File | Line | Finding | Change |
|---|---|---|---|
| `tools/test_profiler_plugin/generate_report.py` | 64, 77, 91, 103 | `"Stats" has no attribute "stream"` | Append `  # type: ignore[attr-defined]` to each `stats.stream = stream` line. Keep the one reused `stats` object; don't use `setattr` (ruff B010). |
| `tools/test_profiler_plugin/generate_report.py` | 114 | `dict` without type arguments | `durations_data: dict[str, Any]` (import `Any` from `typing` if not already imported) |
| `tools/test_scroll.py` | 7 | `App` without type arguments | `class TestScrollApp(App[None]):` |
| `tools/mlflow/get_latest_mlflow_db_entries.py` | 176 | returning `Any` | typed local: `data: dict[str, Any] \| None = json.load(f)` then `return data` |
| `tools/mlflow/extract_mlflow_tool_calls.py` | 73 | returning `Any` | typed local: `messages: list[dict[str, Any]] = data.get(...)...` then `return messages` |
| `tools/mlflow/get_recent_mlflow_runs.py` | 17–25 | `tomllib` redefined | Replace the nested `try: import tomllib / except ImportError: try: import tomli as tomllib ...` with a plain `import tomllib`. The fallback is dead code (`requires-python >= 3.11`). Keep the rest of the outer `try` as it is. |

Leave `tools/mlflow/get_mlflow_config.py` (its own `import tomli`) untouched.

### Cross-platform follow-up: `tools/safe_delete_folder.py`

The table above was found by running mypy on Windows only. CI runs mypy on Linux, where
`sys.platform` is a constant `"linux"`: an early return `if sys.platform != "win32": return ...`
makes the next statement `[unreachable]` under `--strict`. That hit three functions:
`_kill_detected_lockers`, `_delete_reserved_name`, `_delete_reserved_names_recursive`.

Fix (positive guard, as in `src/mcp_coder/utils/tui_preparation.py`): wrap each Windows-only
body in `if sys.platform == "win32":`. A return *after* the block is only reachable on Windows
if the block can fall through; otherwise Windows reports it as `[unreachable]`. So:

- `_kill_detected_lockers`, `_delete_reserved_names_recursive`: initialise the result list
  (`results: list[str] = []`, `deleted`) before the block and return it after the block.
- `_delete_reserved_name`: every path in the block returns, so the non-Windows return goes
  in an `else:` branch. mypy skips the branch that doesn't match on each platform.

Not `# type: ignore[unreachable]`: `warn_unused_ignores` would then fail the Windows run.
Verified with `mypy --strict --platform {linux,win32,darwin}` on the file.

## ALGORITHM

None (declarations only).

## DATA

The return values of the changed functions are unchanged (`dict[str, Any] | None` and
`list[dict[str, Any]]`).

## Checks before commit

1. `run_format_code(target_directories=["src", "tests", "tools"])`
2. `run_ruff_check(target_directories=["src", "tests", "tools"])`: clean
3. `run_mypy_check(target_directories=["src", "tests", "tools"])`: **clean** (0 issues).
   `--warn-unused-ignores` is on, so all four `attr-defined` ignores must be used.
4. `run_pylint_check()` (default scope): clean
5. Fast unit-test run from `.claude/CLAUDE.md` (with `-n auto`): pass

If mypy on `src tests tools` reports a finding not listed here (i.e. the counts changed),
fix it the same way as the listed ones (a typing change or a targeted ignore, no behaviour
change). Only if a fix would change behaviour, write one line to `pr_info/.blocked.txt`
naming the finding and stop.

Commit message: `fix(tools): pass mypy --strict`
