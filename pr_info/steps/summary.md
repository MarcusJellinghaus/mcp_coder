# Implementation Summary: Add `--execution-dir` Flag

## Overview
Add `--execution-dir` flag to separate Claude's working directory from the project directory, enabling users to control where Claude executes independently from where files are modified.

## Problem Statement
Currently, `mcp-coder` conflates two separate concerns:
- **Project location**: Where files are modified and git operations occur (`project_dir`)
- **Execution context**: Where Claude runs and reads config files like `.mcp.json`

This creates friction when users want Claude to operate in their workspace (for config files and MCP server context) while targeting a different project directory.

## Architectural Changes

### Design Principle: Separation of Concerns
We're separating two distinct responsibilities that were previously conflated:

1. **Project Directory** (`project_dir`)
   - Purpose: Location of source files and git repository
   - Used by: Git operations, file modifications, `MCP_CODER_PROJECT_DIR` env var
   - Remains unchanged in behavior

2. **Execution Directory** (`execution_dir`)
   - Purpose: Working directory where Claude subprocess executes
   - Used by: Claude subprocess `cwd`, MCP config file discovery
   - New parameter with explicit control

### Key Architectural Decision: Minimal Parameter Addition

**Approach:** Add `execution_dir` parameter alongside existing `project_dir` parameter throughout the stack.

**Why this approach:**
- ✅ **KISS Principle**: Single clear parameter name throughout codebase
- ✅ **Backward Compatible**: Existing code continues working with `execution_dir=None`
- ✅ **Explicit Control**: Users see exactly what they're controlling
- ✅ **No Coupling**: `project_dir` and `execution_dir` are independent

**Default Behavior:**
- When `execution_dir=None` (default): Claude runs in shell's current working directory
- When `execution_dir` is specified: Claude runs in that directory
- `project_dir` continues to control where git operations happen

### Impact Analysis

**Modified Components:**
1. **CLI Layer** (`src/mcp_coder/cli/main.py`)
   - Add `--execution-dir` argument to 5 commands
   - Path validation and resolution

2. **Command Handlers** (`src/mcp_coder/cli/commands/*.py`)
   - Extract and validate `execution_dir` from args
   - Pass to workflow layer

3. **Workflow Layer** (`src/mcp_coder/workflows/*/core.py`)
   - Accept `execution_dir` parameter
   - Pass to LLM interface

4. **LLM Interface** (`src/mcp_coder/llm/interface.py`)
   - Add `execution_dir` parameter to `ask_llm()` and `prompt_llm()`
   - Pass to provider implementations

5. **Claude Provider** (`src/mcp_coder/llm/providers/claude/*.py`)
   - Pass `execution_dir` as `cwd` to subprocess
   - Update documentation

**Unchanged Components:**
- `src/mcp_coder/llm/env.py` - Still uses `project_dir` for `MCP_CODER_PROJECT_DIR`
- Git operations - Still use `project_dir`
- All existing tests - Continue working with defaults

## Implementation Strategy

### TDD Approach
Each step follows Test-Driven Development:
1. Write tests first (focus on essential tests with KISS principle)
2. Implement functionality to pass tests
3. Update integration points
4. Verify with existing tests

### Change Flow (Top-Down)
```
CLI (--execution-dir flag)
  ↓
Workflow Layer (accept parameter)
  ↓
LLM Interface (add parameter)
  ↓
Claude Provider (use as subprocess cwd)
  ↓
Command Handlers (extract from args and pass to workflows)
```

### Risk Mitigation
- **Breaking Changes**: None - new parameter is optional
- **Default Behavior**: Uses shell's CWD (explicit and intuitive)
- **Testing**: Essential unit tests at each layer (KISS)
- **Documentation**: Clear examples and use cases

## Files to Modify

### Source Files
```
src/mcp_coder/cli/main.py                           # Add CLI arguments
src/mcp_coder/cli/commands/prompt.py                # Extract execution_dir
src/mcp_coder/cli/commands/commit.py                # Extract execution_dir
src/mcp_coder/cli/commands/implement.py             # Extract execution_dir
src/mcp_coder/cli/commands/create_plan.py           # Extract execution_dir
src/mcp_coder/cli/commands/create_pr.py             # Extract execution_dir
src/mcp_coder/workflows/implement/core.py           # Accept execution_dir param
src/mcp_coder/workflows/create_pr/core.py           # Accept execution_dir param
src/mcp_coder/workflows/create_plan.py              # Accept execution_dir param
src/mcp_coder/llm/interface.py                      # Add execution_dir param
src/mcp_coder/llm/providers/claude/claude_code_interface.py  # Pass execution_dir
src/mcp_coder/llm/providers/claude/claude_code_cli.py        # Update docs
src/mcp_coder/llm/providers/claude/claude_code_api.py        # Update docs
```

### Test Files
```
tests/cli/test_main.py                              # CLI argument parsing tests
tests/cli/commands/test_prompt.py                   # Prompt command tests
tests/cli/commands/test_commit.py                   # Commit command tests
tests/cli/commands/test_implement.py                # Implement command tests
tests/cli/commands/test_create_plan.py              # Create-plan command tests
tests/cli/commands/test_create_pr.py                # Create-pr command tests
tests/llm/test_interface.py                         # LLM interface tests
tests/llm/providers/claude/test_claude_code_cli.py  # CLI provider tests
tests/llm/providers/claude/test_claude_code_api.py  # API provider tests
tests/integration/test_execution_dir_integration.py # Integration tests
```

### Documentation Files
```
docs/architecture/ARCHITECTURE.md                   # Update with new parameter
.claude/CLAUDE.md                                   # Add usage examples
```

## Implementation Steps

**Note:** Steps reordered to update workflows before command handlers, avoiding temporary type errors (see Decisions.md).

1. **Step 1**: Add path resolution utility for execution directory
2. **Step 2**: Update CLI argument parsing
3. **Step 5**: Update LLM interface layer (reordered)
4. **Step 6**: Update Claude provider documentation (reordered)
5. **Step 7**: Update workflow layers (reordered)
6. **Step 3**: Update command handlers (prompt, commit) (reordered)
7. **Step 4**: Update command handlers (implement, create-plan, create-pr) (reordered)
8. **Step 8**: Integration testing and documentation

## Expected Outcomes

### User Benefits
- ✅ Explicit control over where Claude executes
- ✅ Can keep MCP configs in workspace while working on different projects
- ✅ Clear separation between execution and project contexts
- ✅ Flexible workflow configurations
- ✅ MCP config in execution_dir takes precedence

### Code Quality
- ✅ Clear parameter naming throughout codebase
- ✅ Minimal changes to existing functionality
- ✅ Focused test coverage (KISS principle)
- ✅ Well-documented architectural decision
- ✅ Consistent error handling matching resolve_project_dir()

### Example Usage
```bash
# Default: Claude runs in shell's CWD
cd /home/user/workspace
mcp-coder implement --project-dir /path/to/project

# Explicit execution directory
mcp-coder implement --project-dir /path/to/project --execution-dir /custom/dir

# Relative path (resolved to shell CWD)
mcp-coder implement --project-dir /path/to/project --execution-dir ./subdir
```

## Success Criteria
- [ ] All new tests pass
- [ ] All existing tests continue to pass
- [ ] No breaking changes to existing CLI usage
- [ ] Documentation updated with examples
- [ ] Code follows project style guidelines
- [ ] All quality checks pass (pylint, mypy, pytest)
