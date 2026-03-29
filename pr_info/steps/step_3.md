# Step 3: `claude_local.bat` — Two-Env Aware Launcher for Developers

## Context

See `pr_info/steps/summary.md` for full context. This is step 3 of 5.

## Goal

Rewrite `claude_local.bat` with the same two-env logic as `claude.bat` (step 2), plus an editable-install verification.

**Purpose:** For developers who have mcp-coder editable-installed (`pip install -e .`).

## WHERE

- `claude_local.bat` (project root)

## WHAT

Same structure as `claude.bat` with one additional check:

1. **Editable install verification** — `pip show mcp-coder` and check `Editable project location` or `Location` points to project dir
2. **Two-env discovery** — same as `claude.bat`
3. **Project env activation** — same as `claude.bat`
4. **MCP tool verification** — same as `claude.bat`
5. **Launch** — same as `claude.bat`

## HOW

Standalone batch file. Inherits the same env var contract as `claude.bat`.

**Difference from claude.bat:**
- Checks editable install via `pip show mcp-coder`
- Error message directs to `tools\reinstall_local.bat` instead of `tools\reinstall.bat`

## ALGORITHM

```
1. If %CD%\.venv does not exist → error: run tools\reinstall_local.bat
2. If VIRTUAL_ENV is set AND != %CD%\.venv:
     save TOOL_VENV_SCRIPTS = %VIRTUAL_ENV%\Scripts (tool env)
   Elif VIRTUAL_ENV is set AND == %CD%\.venv:
     derive tool env from "where mcp-coder" (extract first result's directory)
   Else (no VIRTUAL_ENV):
     derive tool env from "where mcp-coder" (extract first result's directory)
3. Set MCP_CODER_VENV_PATH = TOOL_VENV_SCRIPTS
   Set MCP_CODER_VENV_DIR = parent of MCP_CODER_VENV_PATH (i.e., resolve %MCP_CODER_VENV_PATH%\..)
4. Activate %CD%\.venv as project env
5. Verify editable install: pip show mcp-coder → check Location contains %CD%
   If not editable → warn (but continue)
6. Verify mcp-tools-py.exe and mcp-workspace.exe in MCP_CODER_VENV_PATH
7. Set env vars (same as claude.bat), add MCP_CODER_VENV_PATH to PATH
8. Launch claude.exe %*
```

## DATA

Same environment variables as `claude.bat` (see step 2).

## Testing

- **TDD**: Not applicable (batch file)
- **Manual verification**:
  1. With editable install in `.venv` + tool env on PATH → should work cleanly
  2. With PyPI install → should warn but still launch
  3. Without `.venv` → should error with reinstall_local.bat guidance

## Commit

```
chore: rewrite claude_local.bat with two-env discovery and editable check

Same two-env logic as claude.bat, plus verification that mcp-coder is
editable-installed. Warns if installed from PyPI instead.
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for context.
Also read the current claude_local.bat, the updated claude.bat (from step 2),
and p_tools claude_local.bat (via read_reference_file).

Rewrite claude_local.bat following the algorithm in step_3.md.
Key points:
- Same two-env discovery as claude.bat
- Add editable-install check via "pip show mcp-coder"
- Error messages reference tools\reinstall_local.bat
- Handle the case where VIRTUAL_ENV already points to %CD%\.venv
  (need alternative tool env discovery)
```
