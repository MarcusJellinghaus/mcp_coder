# Issue #613: Align Launcher and Install Scripts with Environment Model

## Problem

mcp-coder uses two Python environments (tool env + project env), but `.mcp.json` and the batch launchers assume a single environment. They use `${VIRTUAL_ENV}` for both MCP server executables (tool env) and pytest/pylint paths (project env). This causes:

- MCP servers not found when tool env ≠ project env
- Python version mismatch (tool env Python 3.13 vs project env Python 3.11)
- Flaky test failures from `caplog` + `pytest-xdist` bug (fixed in 3.13, but MCP server runs 3.11)

## Solution: Architectural Change

**Before:** All scripts treat `VIRTUAL_ENV` as the single source of truth for everything.

**After:** Two distinct environment references:

| Variable | Points to | Used for |
|----------|-----------|----------|
| `MCP_CODER_VENV_PATH` | Tool env `Scripts/` dir | MCP server executables (`command` in `.mcp.json`) |
| `VIRTUAL_ENV` | Project env venv root | `--venv-path`, `--python-executable` (pytest/pylint/mypy) |

The coordinator (`.vscodeclaude_start.bat`) already implements this separation. This PR aligns the remaining entry points.

## Design Decisions

1. **No Python code changes** — `env.py` has a known limitation but it's out of scope (acknowledged in `environments.md`)
2. **`templates.py` already correct** — already sets `MCP_CODER_VENV_PATH`
3. **Tool env discovery** — two cases only: `VIRTUAL_ENV` already set (save before overwrite) or `where mcp-coder` fallback
4. **p_tools `reinstall_local.bat` as template** — proven pattern for venv guard + layered install + entry point verification
5. **Self-hosting detection** — simple `if not exist %CD%\.venv` check; if missing, tool env serves as both

## Files Modified/Created

| File | Action | Purpose |
|------|--------|---------|
| `.mcp.json` | **Edit** | Change `command` from `${VIRTUAL_ENV}` to `${MCP_CODER_VENV_PATH}` |
| `claude.bat` | **Rewrite** | Two-env aware launcher for end-users |
| `claude_local.bat` | **Rewrite** | Two-env aware launcher for developers |
| `tools/reinstall.bat` | **Restructure** | Add venv guard, non-editable PyPI install, entry point checks |
| `tools/reinstall_local.bat` | **Create** | Editable install + GitHub overrides for developers |

No new Python modules, no new test files. Batch files are tested manually per issue spec.

## Testing Strategy

- **Batch files**: Manual testing only (per issue: "batch files tested manually")
- **TDD not applicable**: No Python code changes in this PR
- **Verification per step**: Each step includes manual verification commands

## Implementation Steps

1. **Step 1**: `.mcp.json` — separate tool env from project env (3-line edit)
2. **Step 2**: `claude.bat` — two-env aware launcher for end-users
3. **Step 3**: `claude_local.bat` — two-env aware launcher for developers
4. **Step 4**: `tools/reinstall.bat` — restructure with venv guard and entry point checks
5. **Step 5**: `tools/reinstall_local.bat` — new developer install script
