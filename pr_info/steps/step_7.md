# Step 7: New default bindings, binding validation and the test budget

Turns the gate on: `implement_task` → `check@quick`; `implement_final` → `check@standard`, `test@quick`. Both entries accept `check` and `test`; `format` is a config error. `pytest-timeout = 1800` keeps this repo's `test@quick` within budget.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_7.md`. Implement step 7 only: update the tests first, then change `DEFAULT_BINDINGS` and `_ALLOWED_ACTIONS` in `toolkit_runner.py` and add `pytest-timeout = 1800` to `[tool.mcp-tools-py]` in `pyproject.toml`. Run pylint, mypy and the fast pytest suite; all must pass. Format, then make one commit.

## WHERE
- `src/mcp_coder/utils/toolkit_runner.py`
- `pyproject.toml`
- `tests/utils/test_toolkit_config.py`, `tests/utils/test_toolkit_permissions.py`, `tests/utils/test_toolkit_runner.py`, `tests/workflows/rebase/test_command_toolkit_binding.py`

## WHAT
```python
DEFAULT_BINDINGS: dict[str, tuple[str, ...]] = {
    "implement_task": ("check@quick",),
    "implement_final": ("check@standard", "test@quick"),
    "commit": ("format@apply",),
    "rebase": ("check@standard", "test@standard"),
    "rebase_automated": ("check@standard", "test@unattended"),
}

_ALLOWED_ACTIONS: dict[str, frozenset[str]] = {
    "implement_task": frozenset({"check", "test"}),
    "implement_final": frozenset({"check", "test"}),
    ...  # rest unchanged
}
```
```toml
[tool.mcp-tools-py]
# Formatter for run_format_code and mcp-coder workflows: ruff (import sorting + ruff format)
formatter = "ruff"
# Overrides every test depth's timeout: test@quick (~170 s here) gates implement_final
pytest-timeout = 1800
```

## HOW
- Precondition: the installed `mcp_tools_py` toolkit's `describe()` declares `check` depth `standard` and `test` depth `quick`, and `prompt_fragments()` has non-empty `fix.check` and `fix.test` (search `.venv` with `mcp__mcp-tools-py__search_library_files`, scope `mcp_tools_py`). If not, write one line to `pr_info/.blocked.txt` naming what is missing, and stop.
- Precondition: mcp-tools-py reads `pytest-timeout` from `[tool.mcp-tools-py]` (search `pytest-timeout` in scope `mcp_tools_py`). If not, write one line to `pr_info/.blocked.txt` and stop.

## ALGORITHM
None.

## DATA
See WHAT.

## Tests (write first)
- `test_toolkit_config.py`:
  - defaults equal the new table (the existing `== DEFAULT_BINDINGS` tests cover the constant; add one explicit assertion on the two implement entries).
  - `implement_task = ["check@quick", "test@quick"]` and `implement_final = ["test@quick", "check@full"]` are accepted (the two parametrised rejection cases around lines 197–202 move to the accepted side).
  - `implement_task = ["format@apply"]` and `implement_final = ["format@check"]` raise `ValueError` naming "check, test".
  - `implement_task = []` is accepted (the documented opt-out).
- `test_toolkit_permissions.py`: the "implement_task binds nothing" test now expects the `check@quick` permissions of the fixture toolkit (or override the binding to `[]` in the fixture and keep the assertion — pick whichever keeps the test's intent clearer).
- `test_toolkit_runner.py` (~line 285): the empty `implement_task` run uses an explicit `implement_task = []` binding, or asserts the new default request.
- `test_command_toolkit_binding.py::test_implement_final_runs_check_quick`: rename and update to the new requests; if the fixture's command toolkit declares no `test.quick`, assert `run_binding` returns an `error` result for it (the documented undeclared-depth behaviour).
