# Environment Variables for Portable .mcp.json Configuration

## Overview

Make `.mcp.json` configuration portable across different development environments by introducing two environment variables that MCP Coder sets when spawning LLM processes.

## Problem

Current `.mcp.json` contains hardcoded absolute paths:
```json
"command": "${USERPROFILE}\\Documents\\GitHub\\mcp_coder\\.venv\\Scripts\\mcp-code-checker.exe"
```

This is non-portable and requires manual editing for each developer/environment.

## Solution

Introduce two environment variables:
- `MCP_CODER_PROJECT_DIR`: Absolute path to project directory
- `MCP_CODER_VENV_DIR`: Path to Python virtual environment

Updated `.mcp.json`:
```json
"command": "${MCP_CODER_VENV_DIR}/Scripts/mcp-code-checker.exe"
```

## Architectural Changes

### New Module
- **`src/mcp_coder/llm/env.py`**: Environment variable preparation
  - `prepare_llm_environment(project_dir: Path) -> dict[str, str]`
  - Uses existing `detect_python_environment()` from `utils/detection.py`
  - Raises `RuntimeError` if venv not found (strict requirement)

### Call Chain Updates
Environment variables flow through entire LLM invocation chain:

```
CLI Commands (implement/commit/prompt)
    ↓
Workflows (prepare env internally)
    ↓
LLM Interface (ask_llm, prompt_llm)
    ↓
Claude Code Interface (ask_claude_code)
    ↓
Providers (CLI/API)
    ↓
Subprocess/SDK (with env vars)
```

### Design Decisions

1. **Workflows prepare internally**: `run_implement_workflow()` and `generate_commit_message_with_llm()` call `prepare_llm_environment()` internally
2. **Full chain threading**: All functions in call chain accept `env_vars: dict[str, str] | None = None`
3. **Fail fast**: Raise `RuntimeError` if venv not found
4. **OS-native paths**: Use `str(Path.resolve())` for platform compatibility
5. **Minimal merging**: Pass only our 2 vars, let `subprocess_runner` merge with `os.environ`

## Files Created

```
src/mcp_coder/llm/env.py (NEW)
tests/llm/test_env.py (NEW)
```

## Documentation Updates

```
README.md (add Environment Variables section)
```

## Files Modified

### Core Implementation
```
src/mcp_coder/llm/interface.py
src/mcp_coder/llm/providers/claude/claude_code_interface.py
src/mcp_coder/llm/providers/claude/claude_code_cli.py
src/mcp_coder/llm/providers/claude/claude_code_api.py
```

### Workflows
```
src/mcp_coder/workflows/implement/core.py
src/mcp_coder/utils/commit_operations.py
```

### CLI Commands (minimal changes)
```
src/mcp_coder/cli/commands/implement.py
src/mcp_coder/cli/commands/commit.py
src/mcp_coder/cli/commands/prompt.py
```

### Configuration
```
.mcp.json
```

### Tests
```
tests/llm/test_interface.py
tests/llm/providers/claude/test_claude_code_cli.py
tests/llm/providers/claude/test_claude_code_api.py
tests/workflows/implement/test_core.py
tests/utils/test_commit_operations.py
tests/cli/commands/test_implement.py
tests/cli/commands/test_commit.py
tests/cli/commands/test_prompt.py
```

## Implementation Steps

1. **Step 1**: Create `llm/env.py` + tests
2. **Step 2**: Update CLI provider + tests
3. **Step 3**: Update API provider + tests
4. **Step 4**: Update interface layer + tests
5. **Step 5**: Update workflows + tests
6. **Step 6**: Update CLI commands + tests
7. **Step 7**: Update `.mcp.json` template
8. **Step 8**: Integration test

## Scope

**Included:**
- ✅ Windows implementation
- ✅ Strict venv requirement
- ✅ Both CLI and API methods
- ✅ Full test coverage

**Not Included (Future):**
- ❌ Linux/macOS support
- ❌ Optional venv fallback
- ❌ PYTHONPATH standardization

## Success Criteria

- [ ] `MCP_CODER_PROJECT_DIR` set when spawning Claude
- [ ] `MCP_CODER_VENV_DIR` auto-detected and set
- [ ] Works with both `claude_code_cli` and `claude_code_api`
- [ ] All tests pass
- [ ] `.mcp.json` uses environment variables
- [ ] Clear error if venv not found
