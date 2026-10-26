# Step 4 — Move group C (`TestRestartClosedSessionsLifecycle`) to `test_session_restart_lifecycle.py`

## LLM prompt
> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_4.md`) exactly.
> This is a pure refactoring: move the class with `move_symbol` (dry run first). The only hand edits allowed are import lines.
> The new file temporarily imports `_make_assessment` from `tests.workflows.vscodeclaude.test_session_restart`. That is expected; step 5 rewrites it.
> Use MCP tools only. Finish with the standard checks from the summary, then make one commit.

## WHERE
- Source: `tests/workflows/vscodeclaude/test_session_restart.py`
- Destination: `tests/workflows/vscodeclaude/test_session_restart_lifecycle.py` (**new**, no module docstring)

## WHAT
- `mcp__mcp-tools-py__move_symbol(source_file=".../test_session_restart.py", symbol_names=["TestRestartClosedSessionsLifecycle"], dest_file=".../test_session_restart_lifecycle.py")`
- The class holds 5 tests:
  - `test_restart_closed_sessions_removes_orphans`
  - `test_restart_closed_sessions_skips_unconfigured_repos`
  - `test_restart_closed_sessions_relaunches`
  - `test_restart_closed_sessions_skips_running`
  - `test_restart_closed_sessions_skips_zombie`

## HOW
- **Imports the new file needs** (from the original's modules):
  - `json`, `Path`, `Any`, `pytest`
  - `IssueData` (`mcp_coder.mcp_workspace_github`)
  - `BranchPrepResult` and `restart_closed_sessions` (`...session_restart`)
  - `load_sessions` (`...sessions`)
  - `SessionAction` (`...types`)
  - `make_issue_data` (`tests.github_factories`)
  - `_make_assessment` (temporarily from `tests.workflows.vscodeclaude.test_session_restart`)

  Ruff `F401`/`F821` decides the final set.
- **The source keeps** the imports that `_make_assessment` and group D still use. Remove only the ones ruff flags as unused.
- **Zombie test:** the method-local `import logging` in `test_restart_closed_sessions_skips_zombie` must stay inside that method.

## ALGORITHM
```
move_symbol dry run -> must list only the source and the destination file
move_symbol (real)
check: calls are bare `_make_assessment(`; `import logging` still inside the zombie test
fix imports (ruff clean) in both files; run_format_code
gate: pytest -v destination -> 5 passed; directory collect -> recorded baseline (step 1)
standard checks; commit
```

## DATA / gates
- **Dry run** touches files other than the two named → write one line to `pr_info/.blocked.txt` and stop.
- **`search_files(pattern="test_session_restart\\._make_assessment\\(", glob="tests/**/*.py")`** → **0** hits.
- **`run_pytest_check(extra_args=["-v", "tests/workflows/vscodeclaude/test_session_restart_lifecycle.py"])`** → **5 passed**.
- **`run_pytest_check(extra_args=["-v", "tests/workflows/vscodeclaude/test_session_restart.py"])`** → **7 passed**.
- **Directory collect-only** → the directory baseline recorded in step 1.
- **On any gate failure, including a qualified call site or a hoisted or dropped `import logging`:** move the class back with `move_symbol`, write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(vscodeclaude): move restart lifecycle tests to test_session_restart_lifecycle.py`
