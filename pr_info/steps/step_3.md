# Step 3 — Split `tests/cli/test_main.py`

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement **only** this step
> (`pr_info/steps/step_3.md`). Steps 1 and 2 are done. It is a pure test move: use
> `move_symbol` (dry run first), edit only import lines and `.large-files-allowlist`.
> Finish with every check under **Verification** green and exactly one commit.

## WHERE
- `tests/cli/test_main.py` (source, shrinks to ~462 lines)
- `tests/cli/test_main_coordinator.py` (**new**)
- `tests/cli/test_parsers.py` (existing destination)
- `.large-files-allowlist` (remove the line `tests/cli/test_main.py`)

## WHAT (moved verbatim)
- → `test_main_coordinator.py`: `TestCoordinatorCommand` (6), `TestCoordinatorRunCommand` (4)
- → `test_parsers.py`: `test_execution_dir_flag_rejected` (module-level function,
  10 parametrized cases; the decorator is at `test_main.py:447-461`),
  `TestCheckBranchStatusCommand` (12)
- These stay in `test_main.py`: `TestCreateParser`, `TestLogLevelResolution`,
  `TestNoCommandShowsHelp`, `TestMain`, `TestCLIEntryPoint`, `TestHelpHintIntegration`,
  `TestFaulthandlerSafetyNet`

## HOW (expected end state of imports)
- `test_main.py`: **unchanged** (`argparse`, `logging`, `sys`, `Mock`, `patch`, `pytest`,
  `_resolve_log_level`, `create_parser`, `main`, `execute_subprocess`).
- `test_main_coordinator.py`: `from unittest.mock import Mock, patch`, `pytest`,
  `from mcp_coder.cli.main import create_parser, main`. No `argparse`, `logging` or `sys`.
- `test_parsers.py`: keeps `from __future__ import annotations`, `argparse`, `pytest`,
  `HelpHintArgumentParser`. Adds `logging` and `from unittest.mock import Mock, patch`,
  and extends the existing import to `from mcp_coder.cli.main import create_parser, main`.
  There must be exactly one `mcp_coder.cli.main` import line (the formatter merges them).
- No other lines are added and classes aren't reordered.

## ALGORITHM
```
assert collect_only(test_main.py) == 71 and collect_only(test_parsers.py) == 12
record collect_only("tests/cli/")
move_symbol(test_main.py, [TestCoordinatorCommand, TestCoordinatorRunCommand],
            test_main_coordinator.py, dry_run) -> check, then run
move_symbol(test_main.py, [test_execution_dir_flag_rejected, TestCheckBranchStatusCommand],
            test_parsers.py, dry_run) -> check, then run
check that @pytest.mark.parametrize sits directly above test_execution_dir_flag_rejected in test_parsers.py
format -> ruff fix F401 -> compare imports to HOW -> remove the allowlist line -> run checks -> compare counts
```
If the decorator didn't travel: revert both files with `edit_file`, restoring what the
move removed and added, then re-run `move_symbol` with `test_execution_dir_flag_rejected`
alone. Never re-add the decorator by hand.

## DATA
Expected `--collect-only -q` counts: `test_main.py` 39, `test_main_coordinator.py` 10,
`test_parsers.py` 32, `test_workflow_parsers.py` 10, `test_interactive_parsers.py` 7,
`test_gh_parsers.py` 7; `tests/cli/` equals the recorded baseline (and the step 1 baseline).

## Preconditions (if one fails: write one line to `pr_info/.blocked.txt` and stop)
- `test_main.py` collects 71 and `test_parsers.py` collects 12 before the move.
- Each dry run would modify only `test_main.py` and its destination file.
- After the single-symbol retry, the parametrize decorator is attached to
  `test_execution_dir_flag_rejected`, and the function collects 10 tests.

## Verification
- `run_format_code`; `run_ruff_fix(select=["F401"])`; `run_ruff_check`
- `run_pylint_check`, `run_mypy_check`, `run_lint_imports_check`, `run_tach_check`,
  `run_vulture_check`
- `run_pytest_check` fast unit run (`-n auto` + marker exclusion from `CLAUDE.md`).
  The moved tests carry no markers.
- Counts from **DATA** match. This check is required.
- `check_file_size`: passes; every touched file is < 750 lines and no stale allowlist entries
  are reported.
- `git diff` (compact) over the whole branch versus `main`: only the non-move hunks listed
  in the issue's Verification section.

## Commit
`test(cli): split test_main.py into coordinator and parser test files`
