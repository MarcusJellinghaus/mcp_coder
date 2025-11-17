# Step 6: Update Claude Provider Layer Documentation

## LLM Prompt
```
You are implementing Step 6 of the execution-dir feature.

Reference documents:
- Summary: pr_info/steps/summary.md
- Previous steps: pr_info/steps/step_1.md through step_5.md (completed)
- This step: pr_info/steps/step_6.md

Task: Update Claude provider documentation to clarify cwd parameter usage.

Follow Test-Driven Development:
1. Read this step document completely
2. Review existing tests (no new tests needed)
3. Update docstrings and comments
4. Verify documentation clarity

Apply KISS principle - clarify existing parameter, no behavior changes.
```

## Objective
Update documentation in Claude provider files to clarify that `cwd` parameter controls subprocess execution directory, not project location.

## WHERE
**Modified files:**
- File: `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
  - Function: `ask_claude_code_cli()` docstring
- File: `src/mcp_coder/llm/providers/claude/claude_code_api.py`
  - Function: `ask_claude_code_api()` docstring
- File: `src/mcp_coder/llm/providers/claude/claude_code_interface.py`
  - Function: `ask_claude_code()` docstring

**Test file:**
- No new tests needed (documentation only)
- Verify existing tests in `tests/llm/providers/claude/`

## WHAT

### Documentation Updates

**In `claude_code_cli.py`:**
```python
def ask_claude_code_cli(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,
    cwd: str | None = None,  # Already exists, just update docs
    mcp_config: str | None = None,
) -> LLMResponseDict:
    """Ask Claude via CLI with native session support.

    Uses Claude CLI's native --resume flag for session continuity.
    Session management is handled by Claude Code CLI - no manual history needed.

    Args:
        question: The question to ask Claude
        session_id: Optional Claude session ID to resume previous conversation
        timeout: Timeout in seconds (default: 30)
        env_vars: Optional environment variables for the subprocess
        cwd: Optional working directory for the Claude subprocess.
            This controls where Claude executes, which affects:
            - Where .mcp.json config files are discovered
            - Resolution of relative file paths in prompts
            - Where Claude looks for local context files
            Note: This is separate from project_dir (which sets MCP_CODER_PROJECT_DIR).
            Default: None (subprocess uses caller's current working directory)
        mcp_config: Optional path to MCP config file

    Returns:
        LLMResponseDict with complete response data including session_id
    """
```

**In `claude_code_api.py`:**
```python
def ask_claude_code_api(
    question: str,
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,
    cwd: str | None = None,
    mcp_config: str | None = None,
) -> LLMResponseDict:
    """Ask Claude via Python SDK with session support.

    Args:
        question: The question to ask Claude
        session_id: Optional session ID to resume conversation
        timeout: Timeout in seconds (default: 30)
        env_vars: Optional environment variables for the subprocess
        cwd: Optional working directory for the Claude subprocess.
            Controls where Claude executes and discovers config files.
            Default: None (uses caller's current working directory)
        mcp_config: Optional path to MCP config file

    Returns:
        LLMResponseDict with complete response data including session_id
    """
```

**In `claude_code_interface.py`:**
```python
def ask_claude_code(
    question: str,
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,
    cwd: str | None = None,
    mcp_config: str | None = None,
) -> str:
    """
    Ask Claude a question using the specified implementation method.

    Routes between different Claude Code implementation methods (CLI, API, etc.).
    Supports both CLI and Python SDK (API) methods with session continuity.

    Args:
        question: The question to ask Claude
        method: The implementation method to use ("cli" or "api")
        session_id: Optional session ID to resume previous conversation
        timeout: Timeout in seconds for the request (default: 30)
        env_vars: Optional environment variables to pass to the LLM subprocess
        cwd: Optional working directory for the LLM subprocess.
            Controls Claude's execution context and config file discovery.
            Default: None (subprocess uses caller's working directory)
        mcp_config: Optional path to MCP configuration file

    Returns:
        Claude's response text as a string
    """
```

## HOW

### Documentation Guidelines

1. **Clarify cwd purpose:**
   - What it controls: Subprocess execution directory
   - What it affects: Config file discovery, relative paths
   - What it doesn't affect: Project file location

2. **Add context about separation:**
   - Note distinction from project_dir (when mentioned)
   - Explain default behavior clearly
   - Provide examples where helpful

3. **Update code comments:**
   ```python
   # In build_cli_command() or similar functions
   # cwd parameter controls where Claude subprocess executes
   # This affects .mcp.json discovery and relative path resolution
   ```

## ALGORITHM

```
FOR EACH function IN [ask_claude_code_cli, ask_claude_code_api, ask_claude_code]:
    UPDATE docstring:
        CLARIFY cwd parameter:
            - Purpose: Working directory for subprocess
            - Affects: Config discovery, relative paths
            - Default: Caller's CWD
        
        ADD note:
            - Separate from project_dir concern
            - Used for execution context only
```

## DATA

### No Data Changes
This is a documentation-only step. No:
- Function signatures change
- Parameter types change
- Return values change
- Behavior changes

### Documentation Checklist
- [ ] Docstring for `ask_claude_code_cli()` updated
- [ ] Docstring for `ask_claude_code_api()` updated
- [ ] Docstring for `ask_claude_code()` updated
- [ ] Inline comments clarified where cwd is used
- [ ] Examples show typical usage patterns

## Test Requirements

### Verification (No New Tests)
1. **Existing tests should still pass:**
   ```bash
   pytest tests/llm/providers/claude/ -v
   ```

2. **Documentation quality checks:**
   - Docstrings follow project conventions
   - Type hints are accurate
   - Examples are correct

3. **Code review checklist:**
   - Clear explanation of cwd vs project_dir
   - Default behavior documented
   - Rationale for separation mentioned

## Implementation Notes

### KISS Principles Applied
- Documentation only (no code changes)
- Clear, concise explanations
- Focus on what changed and why
- Avoid over-documentation

### Why This Step
1. **Clarity**: Developers understand cwd purpose
2. **Maintainability**: Future changes respect separation
3. **Discoverability**: IDE tooltips show correct info
4. **Consistency**: All provider functions documented uniformly

### What Makes Good Documentation Here

**Before:**
```python
cwd: Optional working directory for the subprocess
```

**After:**
```python
cwd: Optional working directory for the Claude subprocess.
    Controls where Claude executes and discovers config files.
    This is separate from project_dir (file locations).
    Default: None (uses caller's current working directory)
```

## Verification Steps
1. Read updated docstrings in IDE
2. Generate API documentation: `pydoc src/mcp_coder/llm/providers/claude/`
3. Verify existing tests pass: `pytest tests/llm/providers/claude/ -v`
4. Run mypy: Should pass with no changes
5. Visual review: Docstrings are clear and helpful

## Dependencies
- Depends on: Step 5 (interface layer updated)
- Prepares for: Step 7 (workflow layer can reference docs)

## Estimated Complexity
- Lines changed: ~30 lines (docstring updates)
- Test lines: 0 (no new tests)
- Complexity: Very Low (documentation only)

## Additional Comments to Add

**In `claude_code_cli.py` near subprocess execution:**
```python
# Execute command with stdin input (I/O)
# cwd parameter controls where Claude subprocess runs
# This affects .mcp.json discovery and relative path resolution
logger.debug(
    f"Executing CLI command with stdin (prompt_len={len(question)}, "
    f"session_id={session_id}, cwd={cwd})"
)
```

## Documentation Best Practices

### Do:
- ✅ Explain what cwd controls
- ✅ Mention default behavior
- ✅ Note separation from project_dir
- ✅ Give concrete examples of effects

### Don't:
- ❌ Over-explain implementation details
- ❌ Duplicate info from other docstrings
- ❌ Make assumptions about caller context
- ❌ Use jargon without explanation

## Review Checklist
- [ ] Each docstring mentions cwd purpose
- [ ] Default behavior is clear (None = caller's CWD)
- [ ] Distinction from project_dir is noted
- [ ] Examples are accurate and helpful
- [ ] Inline comments support understanding
- [ ] No misleading information
