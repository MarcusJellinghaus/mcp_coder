# Step 8: `.mcp.json` consistency verification (manual)

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

Verify that `.mcp.json` env var usage is consistent with what the batch launchers set. This is a manual verification task — no code changes.

## Verification Checklist

Check that these env vars used in `.mcp.json` are set consistently by all batch launchers:

| Env Var | Used in `.mcp.json` | Set by `claude.bat` | Set by `claude_local.bat` | Set by `icoder.bat` | Set by `icoder_local.bat` |
|---------|--------------------|--------------------|--------------------------|--------------------|--------------------------| 
| `MCP_CODER_VENV_PATH` | `command` fields | ? | ? | ? | ? |
| `MCP_CODER_PROJECT_DIR` | `--project-dir` args | ? | ? | ? | ? |
| `VIRTUAL_ENV` | `--python-executable`, `--venv-path` | ? | ? | ? | ? |
| `MCP_CODER_VENV_DIR` | workspace `PYTHONPATH` env | ? | ? | ? | ? |

## Output

Add findings to the PR description as a reviewer checklist item. No commit needed.

Also add a placeholder reminder in the PR description for the reviewer to create related issues for mcp-tools-py, mcp-workspace, mcp-config repos.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_8.md.

Verify .mcp.json env var consistency with the batch launchers. Read .mcp.json and all 
four launcher scripts. Check that every env var referenced in .mcp.json is set by all 
launchers. Report findings — do not modify any files.
```
