# Step 2 — Split `tests/cli/test_parsers.py` to mirror the parser modules

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement **only** this step
> (`pr_info/steps/step_2.md`). Step 1 is done. It is a pure test move: use
> `move_symbol` (dry run first), edit only import lines, add no docstrings or other
> lines. Finish with every check under **Verification** green and exactly one commit.

## WHERE
- `tests/cli/test_parsers.py` (source)
- `tests/cli/test_workflow_parsers.py` (**new**)
- `tests/cli/test_interactive_parsers.py` (**new**)
- `tests/cli/test_gh_parsers.py` (**new**)

## WHAT (classes moved verbatim, including their `_parse` helpers)
- → `test_workflow_parsers.py`: `TestBooleanOptionalFlags` (8), `TestFixConflictParser` (1),
  `TestFixCiParser` (1)
- → `test_interactive_parsers.py`: `TestICoderSessionArgs` (7)
- → `test_gh_parsers.py`: `TestDefineLabelsParser` (7)
- These stay in `test_parsers.py`: `TestHelpHintArgumentParser` (5),
  `TestCommitPushFlag` (2), `TestLlmMethodCopilotChoice` (3)

## HOW (expected end state of imports; all absolute, as `move_symbol` writes them)
- `test_parsers.py`: unchanged. `from __future__ import annotations`, `argparse`,
  `pytest`, `from mcp_coder.cli.main import create_parser`,
  `from mcp_coder.cli.parsers import HelpHintArgumentParser`.
- `test_workflow_parsers.py`: `argparse`, `pytest`, `from mcp_coder.cli.main import create_parser`.
- `test_interactive_parsers.py`: `argparse`, `pytest`, `from mcp_coder.cli.main import create_parser`.
- `test_gh_parsers.py`: `argparse`, `from mcp_coder.cli.main import create_parser` (no `pytest`).
- Keep `from __future__ import annotations` in a new file if `move_symbol` writes it.
  Don't add or remove it by hand.
- No module docstrings (`D` is ignored for `tests/**`). No `conftest.py` changes: there
  are no fixtures besides the built-in `capsys`.

## ALGORITHM
```
assert collect_only(test_parsers.py) == 34; record collect_only("tests/cli/")
move_symbol(test_parsers.py, [TestBooleanOptionalFlags, TestFixConflictParser, TestFixCiParser],
            test_workflow_parsers.py, dry_run) -> check, then run
move_symbol(test_parsers.py, [TestICoderSessionArgs], test_interactive_parsers.py, dry_run) -> check, then run
move_symbol(test_parsers.py, [TestDefineLabelsParser], test_gh_parsers.py, dry_run) -> check, then run
format -> ruff fix F401 -> compare imports to HOW -> run checks -> compare counts
```

## DATA
Expected `--collect-only -q` counts: `test_parsers.py` 10, `test_workflow_parsers.py` 10,
`test_interactive_parsers.py` 7, `test_gh_parsers.py` 7; `tests/cli/` equals the recorded
baseline.

## Preconditions (if one fails: write one line to `pr_info/.blocked.txt` and stop)
- `test_parsers.py` collects exactly 34 tests before the move.
- Each dry run would modify only `test_parsers.py` and its destination file.

## Verification
- `run_format_code`; `run_ruff_fix(select=["F401"])`; `run_ruff_check`
- `run_pylint_check`, `run_mypy_check`, `run_vulture_check`
- `run_pytest_check` fast unit run (`-n auto` + marker exclusion from `CLAUDE.md`).
  The moved tests carry no markers.
- Counts from **DATA** match.
- `git diff` (compact): only import hunks, new-file headers and moved-block previews.

## Commit
`test(cli): split test_parsers.py to mirror parser modules`
