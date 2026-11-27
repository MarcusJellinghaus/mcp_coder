# Step 3 — pylint findings in `tools/`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_3.md`), then implement
> step 3 only. No behaviour change. Run the checks listed below and commit (one commit).

## Tests

None new. These are lint fixes with no behaviour change; pylint is the test. The existing
`tests/tools/` suite must still pass.

## WHERE / WHAT / HOW

| File | Line | Finding | Change |
|---|---|---|---|
| `tools/jenkins_download_log.py` | 18 | E0401 `jenkins_builds` | `from jenkins_builds import (  # type: ignore[import-not-found]  # pylint: disable=import-error` (append to the existing comment; keep the bare import) |
| `tools/jenkins_download_logs.py` | 20 | E0401 `jenkins_builds` | same as above |
| `tools/safe_delete_folder.py` | 560 | E1123 `onexc` | `shutil.rmtree(path, onexc=_rmtree_remove_readonly)  # pylint: disable=unexpected-keyword-arg`, the same way the `onerror` branch has its disable. If the formatter splits the call, keep the disable on the line pylint reports. |
| `tools/safe_delete_folder.py` | 498 | W0612 `move_result` | `moved, _ = _move_file_to_temp(path)` |
| `tools/safe_delete_folder.py` | 596 | W0612 `result` | `moved, _ = _move_file_to_temp(locked_path)`. Before renaming, confirm that `result` isn't read later in that `except` block. |
| `tools/test_profiler_plugin/generate_report.py` | 185 | W1514 | `open(DURATIONS_FILE, encoding="utf-8")` |
| `tools/test_profiler_plugin/__init__.py` | 127 | W1514 | `open(durations_path, "w", encoding="utf-8")` |
| `tools/test_profiler_plugin/__init__.py` | 57 | W0107 | delete the `pass` |

Don't change pylint's path (`init-hook` / `source-roots`), and don't rewrite imports as
`tools.jenkins_builds`.

## ALGORITHM

None.

## DATA

Unchanged.

## Checks before commit

1. `run_format_code(target_directories=["src", "tests", "tools"])`
2. `run_ruff_check(target_directories=["src", "tests", "tools"])`: clean
3. `run_pylint_check(target_directories=["src", "tests", "tools"])`: **clean**
4. `run_mypy_check(target_directories=["src", "tests", "tools"])`: clean. The combined
   comment must keep `import-not-found` working.
5. Fast unit-test run from `.claude/CLAUDE.md` (with `-n auto`): pass

If pylint on `src tests tools` reports any finding not listed here, write one line to
`pr_info/.blocked.txt` naming it and stop.

Commit message: `fix(tools): pass pylint`
