# Summary: Route workflows through the toolkit interface (#1195)

Part of epic #1192. Workflow steps stop calling `mcp_coder/mcp_tools_py.py` and request
`(action, depth)` from a configured **toolkit** instead (contract in
`mcp_coder_utils.toolkit`, first implementation `mcp_tools_py.toolkit.PythonToolkit`,
registered under the entry-point group `mcp_coder.toolkits` as `mcp-tools-py`).

Behaviour stays the same apart from the "allowed differences" listed in the issue
(mypy now really runs, `skipped`/`error` statuses, `-o strict_markers=false` for
unattended tests, a stale `VIRTUAL_ENV` stops the pre-flight, and so on).

## Architectural / design changes

### New: toolkit layer in `mcp_coder.utils`

| Module | Role |
|---|---|
| `utils/toolkit.py` | Thin shim re-exporting the contract: `Toolkit`, `ActionRequest`, `ActionResult`, `Finding`, `VerifyItem`, `ToolkitInfo`, `validate_params`. The only module (besides the existing shims) allowed to import `mcp_coder_utils.toolkit`. |
| `utils/toolkit_runner.py` | Everything else, as plain functions: strict config loading, registry lookup, instantiation, params validation, depth fallback, exception wrapping, `verify`, prompt fragments. |

No new classes besides two frozen dataclasses (`ToolkitConfig`, `LoadedToolkit`), and no
new exception types: config problems raise `ValueError` (like `get_format_code` and the
strict `_load_pyproject`). Callers map them to their own errors
(`FormatterConfigError`, `CheckRunError`, an `[ERR]` row, a pre-flight message).

Public API of `toolkit_runner`:

```python
DEFAULT_BINDINGS: dict[str, tuple[str, ...]]
def load_toolkit_config(project_dir: Path) -> ToolkitConfig            # parse only, strict
def get_binding(project_dir: Path, entry: str) -> tuple[str, ...]       # parse only
def load_toolkit(project_dir: Path) -> LoadedToolkit                    # + registry, ctor, describe, params
def run_request(loaded: LoadedToolkit, project_dir: Path, request: str) -> ActionResult
def run_binding(loaded: LoadedToolkit, project_dir: Path, entry: str) -> list[tuple[str, ActionResult]]
def verify_toolkit(loaded: LoadedToolkit, project_dir: Path, action: str | None) -> list[VerifyItem]
def get_fragment(loaded: LoadedToolkit, name: str) -> str
```

### Configuration: `[tool.mcp-coder.toolkit]`

- Read from `pyproject.toml`, else a root `mcp-coder.toml` (same table path). Both files
  are parsed strictly when present; both defining the table is an error.
- No table anywhere → `toolkit = "mcp-tools-py"` with default bindings (until #1199).
- Keys: `toolkit`, `bindings`, `params`, and the selected toolkit's own section
  `[tool.mcp-coder.toolkit.<toolkit>]` (passed to the constructor, `{}` if absent).
- Strict: unknown keys/entries, malformed `action@depth`, unregistered toolkit,
  `bindings`/`params` as toolkit name, per-action `format`/`check`/`test` keys, and
  requests an entry can't act on are all config errors.

Default bindings (match today's behaviour):

| Entry | Requests | Allowed actions |
|---|---|---|
| `implement_task` | none | none (must stay empty) |
| `implement_final` | `check@quick` | `check` |
| `commit` | `format@apply` | `format`, never `format@check` |
| `rebase` | `check@standard`, `test@standard` | `check`, `test` |
| `rebase_automated` | `check@standard`, `test@unattended` | `check`, `test` |

### Runner semantics

- Depth fallback: declared depth runs; an undeclared depth inside
  `quick < standard < full` runs the nearest lower declared one (log line); anything
  else returns an `error` result.
- Exceptions from `run()` → `ActionResult(status="error")`. Exceptions from the
  constructor, `describe()`, `validate_params` or `verify()` → `ValueError`.

### Callers rewired

| Caller | Before | After |
|---|---|---|
| `workflow_steps/commit.py` `check_formatter_config` | `resolve_steps` | `load_toolkit` (always, before the `format_code` gate) then `verify_toolkit(loaded, project_dir, "format")` when formatting is on and `commit` binding is non-empty |
| `workflow_steps/commit.py` `run_formatters` | `run_format_code` wrapper | `run_binding(loaded, project_dir, "commit")`; config problems → `FormatterConfigError`; non-`ok`/`skipped` → `False` |
| `cli/commands/verify_sections.py` | Formatter row only | + Toolkit row and the toolkit's `verify(action="format")` items (skipping `formatter`); the Formatter steps row stays on the wrapper's `resolve_steps` |
| `workflows/implement/task_processing.py` | `_run_mypy_check` via wrapper, `RUN_MYPY_AFTER_EACH_TASK` | `_run_check(project_dir, entry)` over the `implement_task` / `implement_final` binding; same fix loop, prompt and session names |
| `workflows/rebase_checks.py` | three reducers over wrapper results, tuple keys | `run_binding` over `rebase` / `rebase_automated`; keys are `f"{action}: {finding.key}"` strings |
| `workflows/rebase.py`, `rebase_automated.py` | `markers=AUTOMATED_EXCLUDED_MARKERS` | `automated: bool`; `[pytest_marker_filter]` from fragment `check_instructions.unattended` |

Removed from core: `RUN_MYPY_AFTER_EACH_TASK`, `AUTOMATED_EXCLUDED_MARKERS`,
`REBASE_PYTEST_TIMEOUT_SECONDS`, the pytest/pylint/mypy key reducers.
`mcp_coder/mcp_tools_py.py` itself stays untouched until #1199 (still used for the
verify Formatter steps row).

### Architecture config

- `.importlinter`: add `mcp_coder.utils.toolkit -> mcp_coder_utils` to
  `mcp_coder_utils_isolation` `ignore_imports`. `mcp_checker_isolation` unchanged.
- `tach.toml`: drop `mcp_coder.mcp_tools_py` from the `depends_on` of
  `mcp_coder.workflow_steps` and `mcp_coder.workflows`. The new modules live in
  `mcp_coder.utils`, so no new tach module or import-linter layer is needed.
- This repo's `pyproject.toml` gets `[tool.mcp-coder.toolkit] toolkit = "mcp-tools-py"`.

## Files created or modified

Created:
- `src/mcp_coder/utils/toolkit.py`
- `src/mcp_coder/utils/toolkit_runner.py`
- `tests/utils/test_toolkit_config.py`
- `tests/utils/test_toolkit_runner.py`

Modified (source / config / docs):
- `src/mcp_coder/utils/toml_utils.py` (strict `load_toml`)
- `src/mcp_coder/utils/pyproject_config.py` (`_load_pyproject` delegates to `load_toml`)
- `src/mcp_coder/workflow_steps/commit.py`
- `src/mcp_coder/cli/commands/verify_sections.py`
- `src/mcp_coder/workflows/implement/task_processing.py`
- `src/mcp_coder/workflows/implement/core.py`
- `src/mcp_coder/workflows/implement/constants.py`
- `src/mcp_coder/workflows/rebase_checks.py`
- `src/mcp_coder/workflows/rebase.py`
- `src/mcp_coder/workflows/rebase_automated.py`
- `pyproject.toml`, `.importlinter`, `tach.toml`
- `docs/configuration/config.md`, `docs/repository-setup/python.md`,
  `docs/architecture/architecture.md`

Modified (tests; mostly patch targets):
- `tests/conftest.py` (autouse `_resolvable_formatter`)
- `tests/workflow_steps/test_commit.py`
- `tests/cli/commands/test_verify_project_section.py`
- `tests/cli/commands/test_check_branch_status_auto_fixes.py`
- `tests/workflows/fix_ci/test_core.py`
- `tests/workflows/review/test_core_formatter_preflight.py`
- `tests/workflows/implement/test_core.py`, `test_core_workflow.py`,
  `test_task_processing.py`, `test_task_processing_mypy.py`,
  `test_task_processing_branch_name.py`
- `tests/workflows/rebase/test_checks.py`, `test_llm_steps.py`,
  `test_rebase_automated.py`, `test_workflow_regression.py`,
  `test_workflow_branch_moved.py`, `conftest.py` (and any other rebase test asserting
  on removed names)

## Steps

1. Shim + strict config loading (+ this repo's config, docs rows)
2. Registry and runner
3. Formatting through the `commit` binding (`commit.py`; tach: `workflow_steps` drops `mcp_tools_py`)
4. Toolkit rows in `mcp-coder verify`
5. Implement check loop through bindings
6. Rebase checks through bindings + tach/architecture cleanup
