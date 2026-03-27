# Issue #609: feat(vscodeclaude): add --from-github option

## Summary

Add a `--from-github` CLI flag to `mcp-coder vscodeclaude launch` that installs
MCP packages from their GitHub repos (latest `main`) instead of PyPI, so sessions
get the latest unreleased versions. The flag is CLI-only (not persistable in config)
but stored in session data so restarts preserve it.

## Architecture / Design Changes

### Data Flow

```
CLI (parsers.py)
  → args.from_github
    → commands.py (execute_coordinator_vscodeclaude / _handle_intervention_mode)
      → session_launch.py (process_eligible_issues / prepare_and_launch_session)
        → workspace.py (create_startup_script)
          → reads [tool.mcp-coder.from-github] from cloned repo's pyproject.toml
          → generates uv pip install commands in .bat script
```

### Session Persistence

`VSCodeClaudeSession` TypedDict gains a `from_github: bool` field. On restart,
`regenerate_session_files()` reads `session.get("from_github", False)` and passes
it to `create_startup_script()` — no changes to `session_restart.py` needed.

### Startup Script Changes

The generated `.bat` script gains two sections:

1. **Always** (even without `--from-github`): `uv pip install -e . --no-deps` runs
   after venv activation to ensure the editable install is current.

2. **Only with `--from-github`**: After the editable install, inject
   `uv pip install` commands for GitHub packages (with/without deps), then re-run
   `-e .` to restore the editable install if overwritten.

### Configuration Format

Each project declares its GitHub override packages in `pyproject.toml`:

```toml
[tool.mcp-coder.from-github]
packages = [
    "mcp-config-tool @ git+https://github.com/MarcusJellinghaus/mcp-config.git",
    "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git",
]
packages-no-deps = [
    "mcp-tools-py @ git+https://github.com/MarcusJellinghaus/mcp-tools-py.git",
]
```

The startup script reads this at generation time (not runtime) and injects
`uv pip install` commands into the `.bat` file.

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| No new template constant | GitHub install section is 3-5 lines of batch, built inline in `workspace.py` |
| No separate pyproject.toml reader | 5-line inline read with `tomllib` (stdlib 3.11+) suffices |
| No changes to `session_restart.py` | `regenerate_session_files()` already reads session dict → `create_startup_script()` |
| All new params default to `False` | Backward compatible, no changes needed in callers that don't use the flag |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/types.py` | Add `from_github: NotRequired[bool]` to `VSCodeClaudeSession` |
| `src/mcp_coder/workflows/vscodeclaude/helpers.py` | Add `from_github` param to `build_session()` |
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | Append `uv pip install -e . --no-deps` to `VENV_SECTION_WINDOWS` |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | Add `from_github` param + pyproject.toml reading + inline github install generation in `create_startup_script()` |
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | Thread `from_github` through `process_eligible_issues()`, `prepare_and_launch_session()`, `regenerate_session_files()` |
| `src/mcp_coder/cli/parsers.py` | Add `--from-github` argument to launch subparser |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Read `args.from_github`, pass to workflow functions |
| `pyproject.toml` | Add `[tool.mcp-coder.from-github]` section |

## Test Files Modified

| File | Change |
|------|--------|
| `tests/workflows/vscodeclaude/test_types.py` | Test `from_github` field in `VSCodeClaudeSession` |
| `tests/workflows/vscodeclaude/test_helpers.py` | Test `build_session()` with `from_github` |
| `tests/workflows/vscodeclaude/test_templates.py` | Test `-e .` in `VENV_SECTION_WINDOWS` |
| `tests/workflows/vscodeclaude/test_workspace.py` | Test `create_startup_script()` with `from_github=True/False` |
| `tests/workflows/vscodeclaude/test_workspace_startup_script.py` | Test pyproject.toml reading and github install generation |
| `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` | Test `--from-github` flag parsing |

## Implementation Steps

- **Step 1**: Types + helpers (data layer) — `types.py`, `helpers.py` + tests
- **Step 2**: Template + always-run editable install — `templates.py` + tests
- **Step 3**: Core logic in `workspace.py` — pyproject.toml reading + github install generation + tests
- **Step 4**: Threading through `session_launch.py` + tests
- **Step 5**: CLI flag + command wiring — `parsers.py`, `commands.py` + tests
- **Step 6**: Configuration — `pyproject.toml` `[tool.mcp-coder.from-github]` section
