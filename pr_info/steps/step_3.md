# Step 3: Formatting through the `commit` binding

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **step 3** as described in
> `pr_info/steps/step_3.md`. Steps 1–2 (`toolkit_runner`) are done. Update the tests
> first, then `workflow_steps/commit.py`. Run pylint, mypy, pytest (fast unit tests),
> lint-imports, tach and format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflow_steps/commit.py`
- `tach.toml` (drop `mcp_coder.mcp_tools_py` from `mcp_coder.workflow_steps` `depends_on`)
- Tests: `tests/conftest.py`, `tests/workflow_steps/test_commit.py`,
  `tests/workflows/implement/test_core.py`, `tests/workflows/fix_ci/test_core.py`,
  `tests/workflows/review/test_core_formatter_preflight.py`,
  `tests/cli/commands/test_check_branch_status_auto_fixes.py`,
  `tests/workflows/rebase/test_workflow_regression.py`

## WHAT

Signatures unchanged:

```python
def check_formatter_config(project_dir: Path, warn_legacy_key: bool = False) -> str | None
def run_formatters(project_dir: Path) -> bool
```

Imports: drop `from mcp_coder.mcp_tools_py import ...`; add
`from mcp_coder.utils.toolkit_runner import load_toolkit, run_binding, verify_toolkit`.

## ALGORITHM

`check_formatter_config` (callers unchanged: implement, rebase, review, fix_ci,
check_branch_status, all at entry):
```
warn about legacy key (unchanged)
try:
    loaded = load_toolkit(project_dir)          # before the gate: broken config stops the run
    if not get_format_code(project_dir).enabled or not loaded.config.bindings["commit"]: return None
    items = verify_toolkit(loaded, project_dir, "format")
except ValueError as e: return str(e)
errors = [f"{i.name}: {i.message}" if i.message else i.name for i in items if i.status == "error"]
return "\n".join(errors) or None
```

`run_formatters` (no longer calls `check_formatter_config`):
```
try: loaded = load_toolkit(project_dir); enabled = get_format_code(project_dir).enabled
except ValueError as e: raise FormatterConfigError(str(e)) from e
if not enabled: log "Code formatting disabled (...)"; return True
if not loaded.config.bindings["commit"]: log "No formatting configured (commit binding is empty)"; return True
logger.info("Running code formatters...")
for request, result in run_binding(loaded, project_dir, "commit"):
    if result.status not in ("ok", "skipped"): logger.error(f"{request} formatting failed: {result.summary}"); return False
    logger.info(f"{request} formatting completed successfully")
logger.info("All formatters completed successfully"); return True
```

## DATA

- `check_formatter_config` → `None` or one message (config error or the joined verify
  `error` items).
- `run_formatters` → `True`/`False`; raises `FormatterConfigError` only for config
  problems. A formatter that cannot be resolved at format time now returns `False`
  (allowed difference: the pre-flight catches it at entry).

## HOW

- `tests/conftest.py` `_resolvable_formatter`: patch
  `mcp_coder.workflow_steps.commit.verify_toolkit` with `lambda _l, _p, _a: []` instead of
  `commit.resolve_steps`, and also patch
  `mcp_coder.utils.toolkit_runner._toolkit_class` with `lambda _name: PythonToolkit`
  (`from mcp_tools_py.toolkit import PythonToolkit`), so fast unit tests that reach
  `check_formatter_config` / `run_formatters` (implement, rebase, review, fix_ci,
  check_branch_status, commit) never depend on installed `mcp_coder.toolkits`
  entry-point metadata. Update the docstring.
- `tests/utils/test_toolkit_runner.py` (step 2) overrides or bypasses this patch: its
  own monkeypatch of `_toolkit_class` takes precedence, and the registry tests of
  `_toolkit_class` itself call the real function captured at module import
  (`_REAL_TOOLKIT_CLASS = toolkit_runner._toolkit_class`) with `entry_points` patched.
- Tests that patched `commit.run_format_code` now patch `commit.run_binding`, returning
  e.g. `[("format@apply", ActionResult(status="ok", summary=""))]` (or an `error` result
  where they simulated a failure). Expectations stay the same.
- `test_workflow_regression.py`: the `assert not hasattr(rebase_module, "run_format_code")`
  check stays valid; retarget the wrapper patch to `commit.run_binding`.

## Tests (`tests/workflow_steps/test_commit.py`, update first)

`TestRunFormattersGate`:
- `format_code = false` → `True`, `run_binding` not called.
- Key absent → `run_binding` called once with entry `"commit"`.
- `test_resolve_error_raises_config_error` → becomes: `load_toolkit` raising
  `ValueError("No formatter declared")` (e.g. invalid toolkit config) →
  `FormatterConfigError` with that message, `run_binding` not called.
- `test_resolve_error_inside_wrapper_raises_config_error` → becomes: `run_binding`
  returns an `error` result ("No formatter declared") → `run_formatters` returns `False`
  and logs it (no exception).
- Non-bool `format_code` → `FormatterConfigError` (unchanged).
- New: empty `commit` binding (`[tool.mcp-coder.toolkit.bindings] commit = []`) → `True`,
  `run_binding` not called.
- New: broken toolkit config with `format_code = false` → still `FormatterConfigError`.

`TestCheckFormatterConfig`:
- Disabled → `None` even if `verify_toolkit` would report an error (not called).
- Clean verify (`[VerifyItem("formatter", "ok")]`) → `None`.
- Verify `error` item → message containing its name and message.
- `verify_toolkit` raising `ValueError` → its message.
- New: invalid `[tool.mcp-coder.toolkit]` with `format_code = false` → message (config
  loaded before the gate).
- Non-bool `format_code` → message naming the key (unchanged).
- Remove the `real_resolve_steps` import.
