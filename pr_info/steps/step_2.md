# Step 2: Implement Command Building with MCP Config Parameter

## LLM Prompt
```
Implement Step 2 from the MCP Config File Selection Support plan (see pr_info/steps/summary.md).

Implement the command building logic in claude_code_cli.py to accept mcp_config parameter and append it to the Claude CLI command.

This should make the unit tests from Step 1 pass.
Use MCP tools exclusively as per CLAUDE.md requirements.
```

## Objective
Update `build_cli_command()` and `ask_claude_code_cli()` functions to accept and use optional `mcp_config` parameter.

## WHERE
**File to modify:**
- `src/mcp_coder/llm/providers/claude/claude_code_cli.py`

**Affected functions:**
- `build_cli_command()`
- `ask_claude_code_cli()`

## WHAT

### Function Signatures (Updated)

```python
def build_cli_command(
    claude_cmd: str,
    prompt: str,
    session_id: Optional[str] = None,
    mcp_config: Optional[str] = None
) -> list[str]:
    """
    Build Claude CLI command with optional MCP config.
    
    Args:
        claude_cmd: Path to Claude executable
        prompt: Prompt to send to Claude
        session_id: Optional session ID to resume
        mcp_config: Optional path to MCP config file
        
    Returns:
        List of command arguments for subprocess
    """

def ask_claude_code_cli(
    prompt: str,
    project_dir: Optional[Path] = None,
    session_id: Optional[str] = None,
    mcp_config: Optional[str] = None
) -> LlmResponse:
    """
    Ask Claude Code CLI a question.
    
    Args:
        prompt: Question or instruction for Claude
        project_dir: Project directory for context
        session_id: Optional session to resume
        mcp_config: Optional MCP config file path
        
    Returns:
        LlmResponse with answer and metadata
    """
```

## HOW

### Integration Points

1. **Import statements** (no changes needed - using existing imports)

2. **Function parameter addition**
   - Add `mcp_config: Optional[str] = None` to both function signatures

3. **Command construction logic**
   - Append `--mcp-config` and `--strict-mcp-config` after existing arguments

4. **Parameter threading**
   - Pass `mcp_config` from `ask_claude_code_cli()` to `build_cli_command()`

## ALGORITHM

### build_cli_command() Logic
```
1. Create base command: [claude_cmd, "-p", "", "--output-format", "json"]
2. IF session_id provided:
     Append ["--resume", session_id]
3. IF mcp_config provided:
     Append ["--mcp-config", mcp_config, "--strict-mcp-config"]
4. Return complete command list
```

### ask_claude_code_cli() Logic
```
1. Locate Claude CLI executable
2. Build command using build_cli_command(claude_cmd, prompt, session_id, mcp_config)
3. Execute subprocess with built command
4. Parse response and return LlmResponse
5. (No validation logic - Claude CLI handles errors)
```

## Implementation Details

### Code Changes in build_cli_command()

**Location:** After session_id handling, before return statement

```python
# Existing code
command = [claude_cmd, "-p", "", "--output-format", "json"]

if session_id:
    command.extend(["--resume", session_id])

# NEW CODE - Add here
if mcp_config:
    command.extend(["--mcp-config", mcp_config, "--strict-mcp-config"])

return command
```

### Code Changes in ask_claude_code_cli()

**Location:** Function signature and call to build_cli_command()

```python
# Update function signature
def ask_claude_code_cli(
    prompt: str,
    project_dir: Optional[Path] = None,
    session_id: Optional[str] = None,
    mcp_config: Optional[str] = None,  # NEW PARAMETER
) -> LlmResponse:

# Update call to build_cli_command
command = build_cli_command(
    claude_cmd=claude_cmd,
    prompt=prompt,
    session_id=session_id,
    mcp_config=mcp_config  # NEW ARGUMENT
)
```

## DATA

### Input Data
```python
# Function parameters
mcp_config: Optional[str] = None | ".mcp.linux.json" | "/absolute/path/.mcp.json"
```

### Output Data
```python
# Command list structure
# Without mcp_config
["claude", "-p", "", "--output-format", "json"]

# With mcp_config
["claude", "-p", "", "--output-format", "json", "--mcp-config", ".mcp.linux.json", "--strict-mcp-config"]

# With session_id and mcp_config
["claude", "-p", "", "--output-format", "json", "--resume", "abc123", "--mcp-config", ".mcp.linux.json", "--strict-mcp-config"]
```

### LlmResponse (unchanged)
```python
# Existing return structure
LlmResponse(
    answer: str,
    session_id: Optional[str],
    metadata: dict
)
```

## Implementation Checklist
- [ ] Read current implementation of build_cli_command()
- [ ] Add mcp_config parameter to build_cli_command() signature
- [ ] Add conditional logic to append --mcp-config and --strict-mcp-config
- [ ] Add mcp_config parameter to ask_claude_code_cli() signature
- [ ] Pass mcp_config to build_cli_command() call
- [ ] Run unit tests from Step 1 (should PASS now)
- [ ] Run pylint/mypy/pytest checks

## Validation

### Test Execution
```bash
# Run specific test file
pytest tests/unit/llm/providers/claude/test_claude_mcp_config.py -v

# Expected: All tests PASS
```

### Type Checking
```bash
# Verify type annotations
mypy src/mcp_coder/llm/providers/claude/claude_code_cli.py
```

## Expected Result
- All unit tests from Step 1 pass
- No breaking changes to existing functionality
- Type hints remain consistent
- Code quality checks pass
