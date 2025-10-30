# Step 4: Implement CLI Argument and Thread Through Commands

## LLM Prompt
```
Implement Step 4 from the MCP Config File Selection Support plan (see pr_info/steps/summary.md).

Implement the --mcp-config CLI argument in main.py and thread it through the command implementations.

This should make the integration tests from Step 3 pass.
Use MCP tools exclusively as per CLAUDE.md requirements.
```

## Objective
Add `--mcp-config` argument to CLI parsers and pass it through command implementations to the LLM provider.

## WHERE

**Files to modify:**
1. `src/mcp_coder/cli/main.py` - Add CLI argument to parsers
2. `src/mcp_coder/cli/commands/prompt.py` - Pass parameter to ask_llm
3. `src/mcp_coder/cli/commands/implement.py` - Pass parameter to ask_llm
4. `src/mcp_coder/cli/commands/create_plan.py` - Pass parameter to ask_llm
5. `src/mcp_coder/cli/commands/create_pr.py` - Pass parameter to ask_llm

## WHAT

### CLI Argument Definition (main.py)

```python
# Add to prompt_parser
prompt_parser.add_argument(
    "--mcp-config",
    type=str,
    default=None,
    help="Path to MCP configuration file (e.g., .mcp.linux.json)"
)

# Repeat for: implement_parser, create_plan_parser, create_pr_parser
```

### Command Function Signatures (Updated)

```python
# prompt.py
def prompt_command(
    prompt_text: str,
    project_dir: Path | None = None,
    session_id: str | None = None,
    mcp_config: str | None = None
) -> None:
    """Execute prompt command with optional MCP config"""

# implement.py
def implement_command(
    issue_number: str,
    project_dir: Path | None = None,
    session_id: str | None = None,
    mcp_config: str | None = None
) -> None:
    """Execute implement command with optional MCP config"""

# create_plan.py
def create_plan_command(
    issue_number: str,
    project_dir: Path | None = None,
    mcp_config: str | None = None
) -> None:
    """Execute create-plan command with optional MCP config"""

# create_pr.py
def create_pr_command(
    issue_number: str,
    project_dir: Path | None = None,
    mcp_config: str | None = None
) -> None:
    """Execute create-pr command with optional MCP config"""
```

## HOW

### Integration Points

1. **CLI Parser (main.py)**
   - Add argument to 4 subparsers
   - Argument stored in `args.mcp_config`

2. **Command Dispatch (main.py)**
   - Pass `args.mcp_config` to command functions

3. **Command Functions (4 files)**
   - Accept `mcp_config` parameter
   - Pass to `ask_llm()` calls

4. **LLM Interface**
   - `ask_llm()` already accepts keyword arguments
   - Claude provider receives and uses parameter (from Step 2)

## ALGORITHM

### main.py - Add CLI Argument
```
1. Locate prompt_parser definition
2. Add --mcp-config argument with type=str, default=None
3. Repeat for implement_parser, create_plan_parser, create_pr_parser
4. In command dispatch, pass args.mcp_config to command function
```

### Command Files - Thread Parameter
```
1. Add mcp_config parameter to function signature
2. Locate ask_llm() call(s)
3. Add mcp_config=mcp_config to call arguments
4. No other logic changes needed
```

## Implementation Details

### main.py Changes

**Location 1:** Add argument to parsers (4 locations)

```python
# Example for prompt_parser (repeat for others)
prompt_parser = subparsers.add_parser("prompt", help="Send prompt to Claude")
prompt_parser.add_argument("prompt_text", help="The prompt to send")
prompt_parser.add_argument("--project-dir", type=Path, help="Project directory")
prompt_parser.add_argument("--session-id", type=str, help="Session ID to resume")

# NEW CODE - Add this
prompt_parser.add_argument(
    "--mcp-config",
    type=str,
    default=None,
    help="Path to MCP configuration file (e.g., .mcp.linux.json)"
)
```

**Location 2:** Pass to command function (4 locations)

```python
# Example for prompt command (repeat for others)
if args.command == "prompt":
    prompt_command(
        prompt_text=args.prompt_text,
        project_dir=args.project_dir,
        session_id=args.session_id,
        mcp_config=args.mcp_config  # NEW ARGUMENT
    )
```

### prompt.py Changes

**Location:** Function signature and ask_llm call

```python
# Update function signature
def prompt_command(
    prompt_text: str,
    project_dir: Path | None = None,
    session_id: str | None = None,
    mcp_config: str | None = None  # NEW PARAMETER
) -> None:
    """Send a prompt to Claude Code CLI"""
    
    # Update ask_llm call
    response = ask_llm(
        prompt=prompt_text,
        project_dir=project_dir,
        session_id=session_id,
        mcp_config=mcp_config  # NEW ARGUMENT
    )
```

### implement.py Changes

**Similar pattern to prompt.py:**
- Add `mcp_config` to function signature
- Pass `mcp_config` to all `ask_llm()` calls

### create_plan.py Changes

**Similar pattern to prompt.py:**
- Add `mcp_config` to function signature
- Pass `mcp_config` to `ask_llm()` call

### create_pr.py Changes

**Similar pattern to prompt.py:**
- Add `mcp_config` to function signature
- Pass `mcp_config` to `ask_llm()` call

## DATA

### Input Data (CLI Arguments)
```python
# User provides via CLI
--mcp-config .mcp.linux.json
--mcp-config /absolute/path/.mcp.json
# Or omitted (default None)
```

### Threading Flow
```
CLI args.mcp_config (str | None)
    ↓
Command function mcp_config parameter
    ↓
ask_llm(mcp_config=...) keyword argument
    ↓
ask_claude_code_cli(mcp_config=...) parameter
    ↓
build_cli_command(mcp_config=...) parameter
    ↓
Claude CLI command: ["claude", ..., "--mcp-config", "path", "--strict-mcp-config"]
```

### No New Data Structures
- Simple string passthrough
- No validation, transformation, or storage

## Implementation Checklist

### main.py
- [ ] Add --mcp-config to prompt_parser
- [ ] Add --mcp-config to implement_parser
- [ ] Add --mcp-config to create_plan_parser
- [ ] Add --mcp-config to create_pr_parser
- [ ] Pass args.mcp_config to prompt_command()
- [ ] Pass args.mcp_config to implement_command()
- [ ] Pass args.mcp_config to create_plan_command()
- [ ] Pass args.mcp_config to create_pr_command()

### Command Files
- [ ] Update prompt.py function signature
- [ ] Update prompt.py ask_llm call
- [ ] Update implement.py function signature
- [ ] Update implement.py ask_llm calls
- [ ] Update create_plan.py function signature
- [ ] Update create_plan.py ask_llm call
- [ ] Update create_pr.py function signature
- [ ] Update create_pr.py ask_llm call

### Verification
- [ ] Run integration tests from Step 3 (should PASS)
- [ ] Run all existing tests (should still PASS)
- [ ] Run pylint/mypy/pytest checks

## Expected Result
- All integration tests from Step 3 pass
- All existing tests continue to pass (backward compatibility)
- CLI accepts `--mcp-config` argument without errors
- Parameter correctly threaded to Claude CLI provider
- Type checking passes with no errors

## Verification Commands
```bash
# Run integration tests
pytest tests/integration/test_mcp_config_integration.py -v

# Run all tests
pytest tests/ -n auto -m "not git_integration and not claude_integration and not formatter_integration and not github_integration"

# Type check
mypy src/mcp_coder/
```
