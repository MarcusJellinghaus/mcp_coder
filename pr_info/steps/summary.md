# Issue #643: Fix vscodeclaude startup script PATH ordering and missing commands for error statuses

## Problem Summary

Two bugs in the VSCodeClaude coordinator startup system:

1. **PATH ordering bug**: `mcp-coder --version` is called before `MCP_CODER_VENV_PATH` is added to `PATH`, so the command fails with "not recognized"
2. **Missing commands on error statuses**: Five error statuses have `vscodeclaude` config but no `commands`, so no Claude session launches after environment setup

## Architectural / Design Changes

**No architectural changes.** Both fixes are localized configuration/template corrections:

- **Fix 1** reorders existing lines in a batch script template string — the PATH setup block moves earlier, before the first `mcp-coder` invocation. No new logic, no new variables.
- **Fix 2** adds a `"commands"` key to five existing JSON entries. The command `/check_branch_status` already exists (`.claude/commands/check_branch_status.md`). The startup script generator (`workspace.py`) already handles single-command flows via the `INTERACTIVE_ONLY_SECTION_WINDOWS` template.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | Reorder `VENV_SECTION_WINDOWS`: move PATH setup before `mcp-coder --version` |
| `src/mcp_coder/config/labels.json` | Add `"commands": ["/check_branch_status"]` to 5 error statuses |

## Files Created

None.

## Implementation Steps

| Step | Description | File(s) |
|------|-------------|---------|
| 1 | Fix PATH ordering in `VENV_SECTION_WINDOWS` + tests | `templates.py`, `test_templates.py` |
| 2 | Add commands to error statuses in `labels.json` + tests | `labels.json`, `test_label_config.py` |
