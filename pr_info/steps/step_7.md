# Step 7: Update .mcp.json Template

## Context
Read `pr_info/steps/summary.md` for full context. Replace hardcoded paths with environment variables.

## WHERE

**Modified files:**
- `.mcp.json`

## WHAT

### Replace hardcoded paths with environment variables

**Before:**
```json
{
  "mcpServers": {
    "code-checker": {
      "command": "${USERPROFILE}\\Documents\\GitHub\\mcp_coder\\.venv\\Scripts\\mcp-code-checker.exe",
      "args": [
        "--project-dir", "${USERPROFILE}\\Documents\\GitHub\\mcp_coder",
        "--python-executable", "${USERPROFILE}\\Documents\\GitHub\\mcp_coder\\.venv\\Scripts\\python.exe",
        "--venv-path", "${USERPROFILE}\\Documents\\GitHub\\mcp_coder\\.venv"
      ],
      "env": {
        "PYTHONPATH": "${USERPROFILE}\\Documents\\GitHub\\mcp_coder\\"
      }
    }
  }
}
```

**After:**
```json
{
  "mcpServers": {
    "code-checker": {
      "command": "${MCP_CODER_VENV_DIR}\\Scripts\\mcp-code-checker.exe",
      "args": [
        "--project-dir", "${MCP_CODER_PROJECT_DIR}",
        "--python-executable", "${MCP_CODER_VENV_DIR}\\Scripts\\python.exe",
        "--venv-path", "${MCP_CODER_VENV_DIR}"
      ],
      "env": {
        "PYTHONPATH": "${MCP_CODER_PROJECT_DIR}"
      }
    },
    "filesystem": {
      "command": "${MCP_CODER_VENV_DIR}\\Scripts\\mcp-server-filesystem.exe",
      "args": [
        "--project-dir", "${MCP_CODER_PROJECT_DIR}",
        "--log-level", "INFO",
        "--reference-project", "p_fs=${USERPROFILE}\\Documents\\GitHub\\mcp_server_filesystem",
        "--reference-project", "p_config=${USERPROFILE}\\Documents\\GitHub\\mcp-config",
        "--reference-project", "p_checker=${USERPROFILE}\\Documents\\GitHub\\mcp-code-checker"
      ],
      "env": {
        "PYTHONPATH": "${MCP_CODER_VENV_DIR}\\Lib\\"
      }
    }
  }
}
```

## HOW

**Replacements:**
1. `${USERPROFILE}\\Documents\\GitHub\\mcp_coder` → `${MCP_CODER_PROJECT_DIR}`
2. `${USERPROFILE}\\Documents\\GitHub\\mcp_coder\\.venv` → `${MCP_CODER_VENV_DIR}`
3. Use backslashes for Windows compatibility

**Note:** Reference projects still use `${USERPROFILE}` - they're external to this project.

## ALGORITHM

```
1. Replace all project dir references with ${MCP_CODER_PROJECT_DIR}
2. Replace all venv dir references with ${MCP_CODER_VENV_DIR}
3. Keep backslashes for Windows paths
4. Keep reference-project paths unchanged (external)
```

## DATA

**Environment variables Claude Code will substitute:**
- `${MCP_CODER_PROJECT_DIR}` = absolute project path (set by mcp-coder)
- `${MCP_CODER_VENV_DIR}` = absolute venv path (set by mcp-coder)

## Test Coverage

**No automated test** - this is a configuration file. Functionality will be verified by integration test in Step 8.

## LLM Prompt

```
Context: Read pr_info/steps/summary.md and pr_info/steps/step_7.md

Task: Update .mcp.json to use environment variables.

Changes:
1. Replace ${USERPROFILE}\\Documents\\GitHub\\mcp_coder with ${MCP_CODER_PROJECT_DIR}
2. Replace ${USERPROFILE}\\Documents\\GitHub\\mcp_coder\\.venv with ${MCP_CODER_VENV_DIR}
3. Keep backslashes (\\) for Windows compatibility
4. Keep reference-project paths unchanged (they're external)

Verify both code-checker and filesystem server configs are updated.

Manual testing:
1. Run mcp-coder implement to verify MCP servers work
2. Test MCP tools function correctly
```
