# Step 6: Rebase checks through bindings, architecture cleanup

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **step 6** as described in
> `pr_info/steps/step_6.md`. Steps 1–5 are done. Update the tests first, then change
> `workflows/rebase_checks.py`, `workflows/rebase.py`, `workflows/rebase_automated.py`,
> `tach.toml` and the architecture doc. Run pylint, mypy, pytest (fast unit tests),
> lint-imports, tach, vulture and format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/rebase_checks.py`
- `src/mcp_coder/workflows/rebase.py`
- `src/mcp_coder/workflows/rebase_automated.py`
- `tach.toml` (drop `mcp_coder.mcp_tools_py` from `mcp_coder.workflows` `depends_on`)
- `docs/architecture/architecture.md` (the sentence on line ~60 naming the
  `mcp_tools_py` shim: mypy and the formatter now run through the configured toolkit's
  bindings)
- Tests: `tests/workflows/rebase/test_checks.py`, `test_llm_steps.py`,
  `test_rebase_automated.py`, `test_workflow_regression.py`,
  `test_workflow_branch_moved.py`, `conftest.py`

## WHAT

`rebase_checks.py`:

```python
FailureKey = str
"""``"<action>: <Finding.key>"``, e.g. ``"test: tests/test_a.py::test_x"``.
Finding keys are line-insensitive; the action prefix avoids collisions."""

def _run_all_checks(project_dir: Path, automated: bool = False) -> set[FailureKey]
```
Remove `_pytest_failure_keys`, `_pylint_failure_keys`, `_mypy_failure_keys`,
`_PYTEST_NON_FAILING_OUTCOMES`, `REBASE_PYTEST_TIMEOUT_SECONDS` (the toolkit owns the
1800 s budget) and the `mcp_coder.mcp_tools_py` import. Keep `CheckRunError`.

`rebase.py`:

```python
def _marker_filter_text(project_dir: Path, automated: bool) -> str
def _build_regression_fix_prompt(regression_text: str, filter_text: str = "") -> str
def _format_failure_keys(keys: set[FailureKey]) -> str      # "\n".join(sorted(keys))
def run_rebase_workflow(project_dir, provider, base_branch=None, mcp_config=None,
                        settings_file=None, automated: bool = False) -> RebaseRunResult
```

`rebase_automated.py`: delete `AUTOMATED_EXCLUDED_MARKERS`; call
`run_rebase_workflow(..., automated=True)`.

## ALGORITHM

`_run_all_checks`:
```
entry = "rebase_automated" if automated else "rebase"
try: results = run_binding(load_toolkit(project_dir), project_dir, entry)
except Exception as exc: raise CheckRunError(f"toolkit: {exc}") from exc
keys = set()
for request, result in results:
    if result.status == "error": raise CheckRunError(f"{request}: {result.summary}")
    if result.status == "skipped": logger.info("%s skipped: %s", request, result.summary)
    keys |= {f"{request.split('@')[0]}: {f.key}" for f in result.findings}
return keys
```

`_marker_filter_text`: `""` when not automated, else
`get_fragment(load_toolkit(project_dir), "check_instructions.unattended")` (a toolkit
without the fragment leaves it empty).

`_build_regression_fix_prompt`: `template.replace("[regression_output]", text).replace("[pytest_marker_filter]", filter_text)`.
Drop `import json` if unused.

`run_rebase_workflow`: replace `markers` with `automated` in the signature, docstring and
the three `_run_all_checks(project_dir, markers)` calls; build the fix prompt with
`_build_regression_fix_prompt(text, _marker_filter_text(project_dir, automated))`
(inside the existing `try`, so a failure is handled like any other mid-rebase error).
Change the log line `"Running baseline checks (pytest, pylint, mypy)..."` to
`"Running baseline checks..."` (the checks now come from the binding).

## DATA

- `_run_all_checks` → set of `"action: key"` strings; raises `CheckRunError` on an
  `error` result or a toolkit/config failure; `skipped` adds no keys.
- `_format_failure_keys` → sorted, newline-joined keys (also the stall-guard value).
  Regression prompt text changes shape (`check: path|code|message`) — accepted by the issue.

## HOW

- Imports in `rebase_checks.py` / `rebase.py`:
  `from mcp_coder.utils.toolkit_runner import get_fragment, load_toolkit, run_binding`.
- After this step `workflows/` and `workflow_steps/` must not import
  `mcp_coder.mcp_tools_py` nor name any pytest marker: search both packages for
  `mcp_tools_py`, `_integration` and `markers` and fix any leftover.
- `cli/commands/rebase.py` needs no change (it never passed `markers`).

## Tests (update first)

`tests/workflows/rebase/test_checks.py` — rewrite around `ActionResult` (drop the
`mcp_tools_py` result-model imports and the reducer tests); patch
`rebase_checks.load_toolkit` and `rebase_checks.run_binding`:
- `ok` + `findings` results → keys `{"check: a.py|E1|msg", "test: tests/t.py::test_x"}`.
- `automated=False` → entry `"rebase"`; `automated=True` → entry `"rebase_automated"`.
- `error` result → `CheckRunError` naming the request; `skipped` → no keys, logged.
- `load_toolkit` raising `ValueError` → `CheckRunError`.
- Same finding key from `check` and `test` → two distinct keys.
- Real toolkit result: a tmp project with `pyproject.toml` containing
  `[tool.mcp-coder.toolkit.bindings] rebase = ["test@standard"]` and one failing test;
  patch `rebase_checks.load_toolkit` to return a `LoadedToolkit` built from
  `PythonToolkit()` constructed directly (no entry-point assertion) and the real
  `load_toolkit_config(tmp_path)`; assert `_run_all_checks(tmp_path)` returns
  `{"test: test_fail.py::test_fail"}` (adjust to the actual node id).

`test_llm_steps.py`:
- `_build_regression_fix_prompt(text, "FILTER")` → contains `FILTER`, no placeholder;
  without filter text → no placeholder, no `markers=`.
- `_format_failure_keys` expectations use the new string keys.
- New: `_marker_filter_text(tmp_path, False) == ""`; with `automated=True` and a patched
  `load_toolkit`/`get_fragment` returns the fragment.

`test_workflow_regression.py`: `test_markers_reach_every_check_run_and_fix_prompt` →
`automated=True` reaches every `_run_all_checks` call and the fragment reaches the fix
prompt (patch `rebase_module._marker_filter_text`).

`test_rebase_automated.py`: drop the `AUTOMATED_EXCLUDED_MARKERS` import; assert
`kwargs["automated"] is True`.

`conftest.py` / `test_workflow_branch_moved.py`: rename the `_markers` lambda
parameters to `_automated`; the `_build_regression_fix_prompt` stub becomes
`lambda text, _filter_text="": "FIX:" + text`.

Any test asserting `"Running baseline checks (pytest, pylint, mypy)"` → new text.
