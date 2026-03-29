# Step 1: `.mcp.json` — Separate Tool Env from Project Env

## Context

See `pr_info/steps/summary.md` for full context. This is step 1 of 5.

## Goal

Change `.mcp.json` so MCP server executables are resolved from the **tool env** (`MCP_CODER_VENV_PATH`) while pytest/pylint/mypy paths stay on the **project env** (`VIRTUAL_ENV`).

## WHERE

- `.mcp.json` (project root)

## WHAT

Two substitutions in `command` fields:

1. `tools-py.command`: `${VIRTUAL_ENV}\Scripts\mcp-tools-py.exe` → `${MCP_CODER_VENV_PATH}\mcp-tools-py.exe`
2. `workspace.command`: `${VIRTUAL_ENV}/Scripts/mcp-workspace.exe` → `${MCP_CODER_VENV_PATH}/mcp-workspace.exe`

## HOW

Edit the two `command` values. Everything else stays unchanged:
- `--venv-path ${VIRTUAL_ENV}` — correct (project env for pytest)
- `--python-executable ${VIRTUAL_ENV}\Scripts\python.exe` — correct (project Python)
- `PYTHONPATH` in `env` sections — unchanged

## ALGORITHM

```
1. In tools-py.command: replace "${VIRTUAL_ENV}\Scripts\mcp-tools-py.exe"
   with "${MCP_CODER_VENV_PATH}\mcp-tools-py.exe"
2. In workspace.command: replace "${VIRTUAL_ENV}/Scripts/mcp-workspace.exe"
   with "${MCP_CODER_VENV_PATH}/mcp-workspace.exe"
3. No other changes
```

## DATA

Target state matches `docs/environments/environments.md` "Target State (After #613)" section.

## Testing

- **TDD**: Not applicable (JSON config, no Python changes)
- **Manual verification**: After applying, confirm MCP servers launch when `MCP_CODER_VENV_PATH` is set correctly by the launcher scripts (steps 2-3)

## Commit

```
chore: use MCP_CODER_VENV_PATH for MCP server commands in .mcp.json

Separate tool env (MCP server executables) from project env
(pytest/pylint/mypy paths) in .mcp.json configuration.
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

Edit .mcp.json to change the two `command` fields from using
${VIRTUAL_ENV}\Scripts\ to ${MCP_CODER_VENV_PATH}\ for the MCP server
executables. Keep all other fields (--venv-path, --python-executable,
PYTHONPATH) unchanged — they correctly use the project environment.

After editing, verify the result matches the "Target State" in
docs/environments/environments.md.
```
