# Step 2 — Move group A (`TestPrepareAndLaunchSession`) to `test_session_launch_prepare.py`

## LLM prompt
> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_2.md`) exactly.
> This is a pure refactoring: move the class with `move_symbol` (dry run first). The only hand edits allowed are import lines.
> Use MCP tools only. Finish with the standard checks from the summary, then make one commit.

## WHERE
- Source: `tests/workflows/vscodeclaude/test_session_restart.py`
- Destination: `tests/workflows/vscodeclaude/test_session_launch_prepare.py` (**new**; needs no module docstring, because `D` rules are ignored for `tests/**`)

## WHAT
- `mcp__mcp-tools-py__move_symbol(source_file=".../test_session_restart.py", symbol_names=["TestPrepareAndLaunchSession"], dest_file=".../test_session_launch_prepare.py")`
- The class holds 3 tests:
  - `test_prepare_and_launch_session_success`
  - `test_prepare_and_launch_aborts_on_git_failure`
  - `test_prepare_and_launch_aborts_on_setup_failure`

## HOW
- **Imports the new file needs** (each from the same module the original file used):
  - `Path` (`pathlib`) and `Any` (`typing`)
  - `pytest`
  - `CalledProcessError` (`mcp_coder.utils.subprocess_runner`)
  - `prepare_and_launch_session` (`mcp_coder.workflows.vscodeclaude.session_launch`)
  - `RepoVSCodeClaudeConfig` and `VSCodeClaudeConfig` (`mcp_coder.workflows.vscodeclaude.types`)
  - `make_issue_data` (`tests.github_factories`)

  Ruff `F401`/`F821` decides the final set.
- **In the source,** remove imports that are now unused (for example `prepare_and_launch_session`, `CalledProcessError`). Ruff `F401` decides which are unused. `Path` stays, because groups C and D still use `tmp_path: Path`. Use `run_ruff_fix(select=["F401"])` as described in the summary.
- If rope imported a name from a different module than the original did, rewrite only that import line.

## ALGORITHM
```
move_symbol dry run -> must list only the source and the destination file
move_symbol (real)
fix imports (ruff F401/F821 clean) in both files
run_format_code
gate: pytest -v on destination -> 3 passed; directory collect -> recorded baseline (step 1)
standard checks; commit
```

## DATA / gates
- **Dry run** touches files other than the two named → write one line to `pr_info/.blocked.txt` and stop.
- **`run_pytest_check(extra_args=["-v", "tests/workflows/vscodeclaude/test_session_launch_prepare.py"])`** → **3 passed**.
- **`run_pytest_check(extra_args=["-v", "tests/workflows/vscodeclaude/test_session_restart.py"])`** → **13 passed**.
- **Directory collect-only** → the directory baseline recorded in step 1.
- **Compact diff:** a new file header, the moved block (suppressed), and import changes only. A changed method body or indentation, or a gate failure, means: move the class back with `move_symbol`, write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(vscodeclaude): move prepare_and_launch_session tests to test_session_launch_prepare.py`
