# Summary: Consolidate Formatters into mcp-tools-py

**Issue:** #737 — refactor: consolidate formatters into mcp-tools-py
**Type:** Refactoring — deletions + import swaps. No new business logic.

## Goal

Delete `mcp_coder/formatters/` package and its tests. The single production caller
(`task_processing.py`) switches to a thin shim in `mcp_tools_py.py` that delegates
to the mcp-tools-py library's `run_format_code`. Config files (`.importlinter`,
`tach.toml`, `tools/tach_docs.py`, `docs/architecture/architecture.md`) are updated
to remove all formatter references.

## Architectural Changes

### Before
```
task_processing.py → mcp_coder.formatters.format_code()
                     ├── black_formatter.py  (subprocess via execute_command)
                     ├── isort_formatter.py  (subprocess via execute_command)
                     ├── config_reader.py    (delegates to pyproject_config.py)
                     ├── models.py           (FormatterResult dataclass)
                     └── utils.py            (target dir + config reading)
```

### After
```
task_processing.py → mcp_coder.mcp_tools_py.run_format_code()
                     └── mcp_tools_py.formatter.runner.run_format_code()
                         (already exists in mcp-tools-py library)
```

### Key Decisions
- **mcp-tools-py wins**: uses venv python, lets tools read own config, `--check` mode,
  output truncation, tool-availability check, MCP integration
- **`.error_message` → `.output`**: mcp-tools-py's `FormatterResult` has `output: str`
  instead of `error_message: Optional[str]`; caller logs `result.output` on failure
- **No line-length check in shim**: the MCP tool already calls it; the implement
  workflow ignores it
- **`pyproject_config.py` shrinks** but is NOT renamed (follow-up scope)

## Files Modified

| File | Action |
|------|--------|
| `src/mcp_coder/mcp_tools_py.py` | Add `run_format_code` shim |
| `src/mcp_coder/workflows/implement/task_processing.py` | Swap import + adapt call |
| `tests/workflows/implement/test_task_processing.py` | Update mock target + assertions (incl. `test_error_recovery_patterns`) |
| `tach.toml` | Add `mcp_tools_py` dependency to workflows module |
| `src/mcp_coder/utils/pyproject_config.py` | Remove 2 functions |
| `tests/utils/test_pyproject_config.py` | Remove 2 test classes |
| `.importlinter` | Remove 2 contracts + refs in 2 others (keep `black_isolation` and `isort_isolation`) |
| `tach.toml` | Remove `mcp_coder.formatters` module + deps |
| `tools/tach_docs.py` | Remove formatter from diagram + module list |
| `docs/architecture/architecture.md` | Remove formatter section + `formatter_integration` marker description |
| `pyproject.toml` | Remove `formatter_integration` marker definition |

## Files Deleted

| Path | Files |
|------|-------|
| `src/mcp_coder/formatters/` | `__init__.py`, `black_formatter.py`, `isort_formatter.py`, `config_reader.py`, `models.py`, `utils.py` |
| `tests/formatters/` | `__init__.py`, `test_black_formatter.py`, `test_isort_formatter.py`, `test_config_reader.py`, `test_models.py`, `test_utils.py`, `test_main_api.py`, `test_debug.py`, `test_integration.py` |

## Files Unchanged (confirmed)

| File | Reason |
|------|--------|
| `tests/test_pyproject_config.py` | Only tests GitHub install config |
| `docs/architecture/dependencies/*` | Auto-generated; regenerated next tool run |
| `repo_architecture_plan/*` | Historical plan docs; out of scope |

## Step Sequence

| Step | Commit message | Description |
|------|---------------|-------------|
| 1 | `refactor: add run_format_code shim + swap caller` | Shim in mcp_tools_py.py, swap task_processing.py import, update tests (incl. `test_error_recovery_patterns`), add `tach.toml` workflows dependency |
| 2 | `refactor: delete formatters package and update configs` | Remove 6 source + 9 test files, update .importlinter (remove 2 contracts, keep `black_isolation`/`isort_isolation`), tach.toml, tach_docs.py, architecture.md, pyproject.toml marker cleanup |
| 3 | `refactor: remove formatter helpers from pyproject_config` | Remove 2 functions + 2 test classes from pyproject_config.py |

## Verification

After all steps: pytest, pylint, mypy, lint_imports, vulture all pass.
Grep confirms zero references to `mcp_coder.formatters`, `get_formatter_config`,
`check_line_length_conflicts` in production code.
