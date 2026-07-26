# Step 1 — Shared check wrappers: `run_pytest_check` + `run_pylint_check`

Extend the thin `mcp_coder.mcp_tools_py` wrapper with pytest and pylint runners next to
the existing `run_mypy_check`, so baseline and verification in the rebase workflow use
identical invocations by construction. See [summary.md](./summary.md).

## WHERE

- Modify: `src/mcp_coder/mcp_tools_py.py`
- Create: `tests/test_mcp_tools_py.py` (unit tests; the existing
  `tests/test_mcp_tools_py_integration.py` stays untouched)

## WHAT

```python
def run_pytest_check(project_dir: Union[str, Path]) -> dict[str, Any]:
    """Run pytest with project defaults (no marker filter, library timeouts)."""

def run_pylint_check(project_dir: Union[str, Path]) -> PylintResult:
    """Run pylint on the project's resolved target directories."""
```

## HOW

- `run_pytest_check` calls `mcp_tools_py.code_checker_pytest.check_code_with_pytest`
  with only `project_dir=str(project_dir)` and `python_executable=sys.executable`.
  **No** `markers`, **no** `timeout_seconds`, **no** `extra_args` — library defaults
  (300s timeout) are the decided behavior.
- `run_pylint_check` calls `mcp_tools_py.code_checker_pylint.get_pylint_results` with
  `python_executable=sys.executable` and `target_directories` resolved via
  `mcp_tools_py.utils.project_config.resolve_target_directories(str(project_root), None)`
  — same pattern as the existing `run_format_code` in this file, including
  `raise RuntimeError(target_dirs)` when resolution returns an error string.
- Match the existing file's style: module-level imports where the existing code has
  them, lazy imports where it uses lazy imports; keep wrappers dumb (no result
  interpretation — that belongs to `workflows/rebase.py`, Step 2).

## DATA

- `run_pytest_check` returns the library dict unchanged: keys `success`, `summary`,
  `failed_tests_prompt`, `test_results` (a `PytestReport`), `error_info`.
- `run_pylint_check` returns the library `PylintResult` unchanged
  (`return_code`, `messages: list[PylintMessage]`, `error`, `raw_output`).

## TDD

Write `tests/test_mcp_tools_py.py` first:

1. `run_pytest_check` — mock `check_code_with_pytest`; assert it is called with
   `project_dir` as str, `python_executable=sys.executable`, and that no `markers` /
   `timeout_seconds` / `extra_args` kwargs are passed (defaults preserved); assert the
   dict is returned unchanged.
2. `run_pylint_check` — mock `get_pylint_results` + `resolve_target_directories`;
   assert resolved dirs are forwarded; assert `RuntimeError` when resolution returns a
   str; assert the `PylintResult` is returned unchanged.

No git, no subprocess, no markers needed — plain fast unit tests.

## Commit

One commit: tests + implementation, all three checks green
(`run_pylint_check`, `run_pytest_check` with the standard not-integration exclusion,
`run_mypy_check` via the MCP tools).

Suggested message: `feat: add run_pytest_check and run_pylint_check to mcp_tools_py wrapper`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement `pr_info/steps/step_1.md`
> exactly: add `run_pytest_check` and `run_pylint_check` to
> `src/mcp_coder/mcp_tools_py.py` as thin pass-throughs to the `mcp_tools_py` library
> (project defaults, no marker filter, library-default timeouts), following the style of
> the existing `run_mypy_check` / `run_format_code` in that file. Write the unit tests in
> `tests/test_mcp_tools_py.py` first (TDD). Do not touch any other file. Run pylint,
> pytest, and mypy via the MCP check tools and fix any findings before finishing.
