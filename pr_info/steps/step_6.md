# Step 6: Add version printing to all four launchers

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

Print `mcp-workspace --version` and `mcp-tools-py --version` at startup in all four launcher batch files, after MCP tool verification succeeds.

## Changes

### MODIFY: `claude.bat`

Add after Step 4 (MCP tool verification), before Step 5 (set env vars and launch):

```batch
REM === Step 4b: Print MCP server versions ===
"!MCP_CODER_VENV_PATH!\mcp-workspace.exe" --version
"!MCP_CODER_VENV_PATH!\mcp-tools-py.exe" --version
```

### MODIFY: `claude_local.bat`

Add after Step 5 (MCP tool verification), before Step 6 (set env vars and launch):

```batch
REM === Step 5b: Print MCP server versions ===
"!MCP_CODER_VENV_PATH!\mcp-workspace.exe" --version
"!MCP_CODER_VENV_PATH!\mcp-tools-py.exe" --version
```

### MODIFY: `icoder.bat`

Add after Step 4 (MCP tool verification), before Step 5 (set env vars and launch):

```batch
REM === Step 4b: Print MCP server versions ===
"!MCP_CODER_VENV_PATH!\mcp-workspace.exe" --version
"!MCP_CODER_VENV_PATH!\mcp-tools-py.exe" --version
```

### MODIFY: `icoder_local.bat`

Add after Step 5 (MCP tool verification), before Step 6 (set env vars and launch):

```batch
REM === Step 5b: Print MCP server versions ===
"!MCP_CODER_VENV_PATH!\mcp-workspace.exe" --version
"!MCP_CODER_VENV_PATH!\mcp-tools-py.exe" --version
```

**DESIGN:** Plain calls, no extra error handling — the exe existence is already verified in the preceding step. Keep all four launchers structurally aligned (same placement relative to their existing steps).

## Verification

- Review all four files for structural consistency
- Verify version commands use `!MCP_CODER_VENV_PATH!` (delayed expansion) consistently
- pylint, mypy, pytest clean (batch files don't affect Python checks)

### `.mcp.json` consistency check

Verify that `.mcp.json` env var usage is consistent with what the batch launchers set:

| Env Var | Used in `.mcp.json` | Must be set by all launchers |
|---------|--------------------|--------------------------|
| `MCP_CODER_VENV_PATH` | `command` fields | Yes |
| `MCP_CODER_PROJECT_DIR` | `--project-dir` args | Yes |
| `VIRTUAL_ENV` | `--python-executable`, `--venv-path` | Yes |
| `MCP_CODER_VENV_DIR` | workspace `PYTHONPATH` env | Yes |

Read `.mcp.json` and all four launcher scripts. Confirm every env var referenced in `.mcp.json` is set by all launchers. Report any inconsistencies.

### PR description items

Add to the PR description:
- Reviewer checklist item: `.mcp.json` env var consistency verified
- Placeholder reminder for related issues in mcp-tools-py, mcp-workspace, mcp-config repos

## Commit

```
feat: print MCP server versions in launcher scripts (#640)
```

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_6.md.

Add version printing (mcp-workspace --version and mcp-tools-py --version) to all four 
launcher scripts: claude.bat, claude_local.bat, icoder.bat, icoder_local.bat. Place them 
after the MCP tool verification step in each file. Keep structural consistency across 
all four files.

Then verify .mcp.json env var consistency: read .mcp.json and all four launcher scripts, 
confirm every env var referenced in .mcp.json is set by all launchers. Add findings to 
the PR description as a reviewer checklist item, plus a placeholder for related issues 
in other repos. Run all quality checks.
```
