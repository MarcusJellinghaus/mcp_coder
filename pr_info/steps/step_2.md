# Step 2 — pytest marker filter and explicit pytest timeout

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` only.
> Write/adjust the tests first, then the implementation. Run pylint, pytest (fast
> unit set, `-n auto`), mypy and lint-imports until they pass, run
> `run_format_code`, and make exactly one commit.

## WHERE

- `src/mcp_coder/mcp_tools_py.py`
- `src/mcp_coder/workflows/rebase_checks.py`
- `src/mcp_coder/workflows/rebase.py`
- `src/mcp_coder/prompts/prompts.md` (section "Rebase Regression Fix")
- Tests: `tests/test_mcp_tools_py.py`, `tests/workflows/rebase/test_checks.py`,
  `tests/workflows/rebase/test_llm_steps.py`, `tests/workflows/rebase/test_prompt.py`,
  `tests/workflows/rebase/conftest.py` (fake `_run_all_checks` signature)

## WHAT

```python
# mcp_tools_py.py
def run_pytest_check(
    project_dir: str | Path,
    markers: list[str] | None = None,
    timeout_seconds: int = 300,
) -> dict[str, Any]   # forwards both to check_code_with_pytest

# rebase_checks.py
REBASE_PYTEST_TIMEOUT_SECONDS = 1800
def _run_all_checks(project_dir: Path, markers: list[str] | None = None) -> set[FailureKey]

# rebase.py
def _build_regression_fix_prompt(regression_text: str, markers: list[str] | None = None) -> str
def run_rebase_workflow(..., markers: list[str] | None = None) -> RebaseRunResult
```

## HOW

- `_run_all_checks` calls `run_pytest_check(project_dir, markers=markers,
  timeout_seconds=REBASE_PYTEST_TIMEOUT_SECONDS)` — the timeout applies to the CLI too.
- `run_rebase_workflow` passes `markers` to every `_run_all_checks` call and to
  `_build_regression_fix_prompt`.
- Prompt: add a line `[pytest_marker_filter]` after the check-tool paragraph and
  list it under `Placeholders:`.
- `markers` entries are `-m` expressions (`"not claude_cli_integration"`); the
  upstream runner joins them with `and`.

## ALGORITHM

```
filter_text = ""
if markers:
    filter_text = ("When you run `mcp__mcp-tools-py__run_pytest_check`, pass "
                   f"markers={json.dumps(markers)} so tests that reach external "
                   "services are excluded.")
return template.replace("[regression_output]", text).replace("[pytest_marker_filter]", filter_text)
```

## DATA

No new types. CLI passes no markers (unfiltered run).

## Tests

- Shim forwards `markers` and `timeout_seconds` to `check_code_with_pytest`
  (defaults: `None`, 300).
- `_run_all_checks(tmp, ["not x"])` passes the markers and `REBASE_PYTEST_TIMEOUT_SECONDS`.
- Prompt: placeholder present in `prompts.md`; with markers the filter text names
  them; without markers no `[pytest_marker_filter]` and no filter text remains.
- `run_rebase_workflow(..., markers=[...])` reaches the checks (fake records the arg).
