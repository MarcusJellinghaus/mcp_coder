# Step 2: `claude.bat` — Two-Env Aware Launcher for End-Users

## Context

See `pr_info/steps/summary.md` for full context. This is step 2 of 5.

## Goal

Rewrite `claude.bat` to discover the tool env separately from the project env, matching the pattern already used by `.vscodeclaude_start.bat` (coordinator).

**Purpose:** For users who installed mcp-coder from PyPI into a separate tool env.

## WHERE

- `claude.bat` (project root)

## WHAT

Replace the current single-env logic with two-env discovery:

```batch
@echo off
cls
setlocal enabledelayedexpansion
```

### Functions / Sections

1. **Tool env discovery** — detect where mcp-coder is installed
2. **Project env activation** — activate `%CD%\.venv` (or skip for self-hosting)
3. **MCP tool verification** — check executables exist
4. **Launch** — set env vars and start Claude

## HOW

The script is a standalone batch file. No imports or decorators — just sequential batch logic.

**Integration points:**
- Sets `MCP_CODER_VENV_PATH` which `.mcp.json` (step 1) now reads
- Sets `VIRTUAL_ENV` (via activate.bat) which `.mcp.json` reads for `--venv-path`
- Sets `MCP_CODER_PROJECT_DIR` and `MCP_CODER_VENV_DIR`

## ALGORITHM

```
1. If VIRTUAL_ENV is set AND != %CD%\.venv:
     save TOOL_VENV_SCRIPTS = %VIRTUAL_ENV%\Scripts
   Elif VIRTUAL_ENV is set AND == %CD%\.venv:
     run "where mcp-coder" → extract first result's directory as TOOL_VENV_SCRIPTS
     if not found → error and exit
   Else (no VIRTUAL_ENV):
     run "where mcp-coder" → extract first result's directory as TOOL_VENV_SCRIPTS
     if not found → error and exit
2. Set MCP_CODER_VENV_PATH = %TOOL_VENV_SCRIPTS%
   Set MCP_CODER_VENV_DIR = parent of MCP_CODER_VENV_PATH (i.e., resolve %MCP_CODER_VENV_PATH%\..)
3. If %CD%\.venv exists:
     call .venv\Scripts\activate.bat  (sets VIRTUAL_ENV to project env)
   Else (self-hosting):
     set VIRTUAL_ENV=%MCP_CODER_VENV_DIR% (tool env serves as both; ensures .mcp.json vars resolve)
4. Verify mcp-tools-py.exe and mcp-workspace.exe exist in MCP_CODER_VENV_PATH
5. Set MCP_CODER_PROJECT_DIR=%CD%, DISABLE_AUTOUPDATER=1
6. Add MCP_CODER_VENV_PATH to front of PATH
7. Launch claude.exe %*
```

## DATA

Environment variables set before launch:

| Variable | Value |
|----------|-------|
| `MCP_CODER_VENV_PATH` | Tool env Scripts dir (e.g., `C:\Jenkins\...\Scripts`) |
| `VIRTUAL_ENV` | Project env root (e.g., `%CD%\.venv`) or tool env if self-hosting |
| `MCP_CODER_PROJECT_DIR` | `%CD%` |
| `MCP_CODER_VENV_DIR` | Tool env venv root (parent of `MCP_CODER_VENV_PATH`) |
| `DISABLE_AUTOUPDATER` | `1` |

## Testing

- **TDD**: Not applicable (batch file)
- **Manual verification**:
  1. With a tool env active: `set VIRTUAL_ENV=C:\path\to\tool\.venv` then run `claude.bat` — should discover tool env, activate project `.venv`
  2. Without any venv: ensure `mcp-coder` is on PATH, run `claude.bat` — should discover via `where`
  3. Self-hosting (no `%CD%\.venv`): should use tool env for both

## Commit

```
chore: rewrite claude.bat with two-env discovery

Discover tool env from VIRTUAL_ENV or PATH, then activate project
.venv separately. Supports self-hosting (tool env = project env).
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for context.
Also read the current claude.bat, the coordinator template in
src/mcp_coder/workflows/vscodeclaude/templates.py (VENV_SECTION_WINDOWS),
and p_tools claude.bat (via read_reference_file) for patterns.

Rewrite claude.bat following the algorithm in step_2.md.
Key points:
- Discover tool env from VIRTUAL_ENV (if set) or "where mcp-coder"
- Set MCP_CODER_VENV_PATH to tool env Scripts dir
- Activate %CD%\.venv as project env (skip if doesn't exist = self-hosting)
- Verify mcp-tools-py.exe and mcp-workspace.exe exist in tool env
- Set all env vars and launch Claude
- Use setlocal enabledelayedexpansion
- Set DISABLE_AUTOUPDATER=1
```
