# Step 1: Add `--llm-method claude_code_cli` to Windows templates

## File
`src/mcp_coder/workflows/vscodeclaude/templates.py`

## Changes

### 1a. `AUTOMATED_SECTION_WINDOWS` (line 109)
Add `--llm-method claude_code_cli` to the `mcp-coder prompt` call in the `for /f` loop:

```
Before:
  for /f "delims=" %%i in ('mcp-coder prompt "{initial_command} {issue_number}" --output-format session-id --mcp-config .mcp.json --timeout {timeout}') do set SESSION_ID=%%i

After:
  for /f "delims=" %%i in ('mcp-coder prompt "{initial_command} {issue_number}" --llm-method claude_code_cli --output-format session-id --mcp-config .mcp.json --timeout {timeout}') do set SESSION_ID=%%i
```

### 1b. `DISCUSSION_SECTION_WINDOWS` (line 130)
Add `--llm-method claude_code_cli` to the `mcp-coder prompt` call:

```
Before:
  mcp-coder prompt "/discuss" --session-id %SESSION_ID% --mcp-config .mcp.json --timeout {timeout}

After:
  mcp-coder prompt "/discuss" --llm-method claude_code_cli --session-id %SESSION_ID% --mcp-config .mcp.json --timeout {timeout}
```

## Rationale
Step 3 uses `claude --resume %SESSION_ID%` which requires a Claude Code conversation ID. By forcing `--llm-method claude_code_cli`, we ensure the session ID is always compatible, regardless of the user's default LLM provider config.
