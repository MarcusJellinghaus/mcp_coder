# Summary: Fix VSCodeClaude Test Dependencies Installation

## Issue
Coordinator vscodeclaude does not install test dependencies to the workspace environment. Currently only installs `--extra types`, missing pytest-asyncio and pytest-xdist required for running tests.

## Root Cause
The `VENV_SECTION_WINDOWS` template in `src/mcp_coder/workflows/vscodeclaude/templates.py` uses:
```batch
uv sync --extra types
```

This only installs type stubs, not test dependencies.

## Solution
Change the installation command to use the comprehensive `dev` extras group:
```batch
uv sync --extra dev
```

This installs all development dependencies defined in `pyproject.toml`:
- `types` - Type stubs for mypy (already working)
- `test` - Test utilities (pytest-asyncio, pytest-xdist) **[FIXES THE ISSUE]**
- `mcp` - MCP servers (currently empty but future-proof)
- Architecture tools (import-linter, pycycle, tach, vulture)

## Architectural/Design Changes

### No Architectural Changes
This is a **configuration fix**, not an architectural change. The design remains identical:
- Same workspace setup flow
- Same venv creation process
- Same file generation patterns
- Same orchestration logic

### What Changes
**Single template constant** in one file:
- File: `src/mcp_coder/workflows/vscodeclaude/templates.py`
- Constant: `VENV_SECTION_WINDOWS`
- Change: One line from `--extra types` to `--extra dev`

### Impact
- **Positive**: Workspaces will have complete development environment
- **Minimal**: No performance impact (one-time setup cost)
- **Safe**: No changes to logic, only dependency specification

## Files Modified

### Core Changes
1. `src/mcp_coder/workflows/vscodeclaude/templates.py`
   - Modify: `VENV_SECTION_WINDOWS` template string
   - Change: Line ~14 from `--extra types` to `--extra dev`

### Test Changes
2. `tests/workflows/vscodeclaude/test_templates.py` (new file)
   - Add: Test to verify `--extra dev` is in venv section

### Documentation
3. `docs/coordinator-vscodeclaude.md`
   - Add: Concise note about dev dependencies in Session Lifecycle section

### Files NOT Modified
- ❌ `src/mcp_coder/workflows/vscodeclaude/workspace.py` - No logic changes
- ❌ `src/mcp_coder/workflows/vscodeclaude/orchestrator.py` - No logic changes
- ❌ `src/mcp_coder/cli/commands/coordinator/command_templates.py` - Different coordinator commands
- ❌ `docs/coordinator-vscodeclaude.md` - Doesn't specify extras detail
- ❌ Linux templates - Not implemented yet (NotImplementedError)

## Implementation Approach

### KISS Principles Applied
1. **Minimal change**: One line in one template
2. **No new abstractions**: No new functions, classes, or patterns
3. **Existing validation**: Reuse existing `validate_setup_commands()` flow
4. **Standard testing**: Simple string assertion tests

### Test Strategy
1. **Unit tests**: Verify template contains `--extra dev`
2. **Integration tests**: Optional - would require actual uv/venv setup

### Risk Assessment
- **Risk**: Very low - changing dependency specification only
- **Validation**: Template string tests catch regressions
- **Rollback**: Single line revert if issues arise

## Verification Plan
After implementation:
1. Template contains correct `--extra dev` string
2. Tests pass validating the change
3. Manual verification: Create a vscodeclaude workspace and confirm pytest-asyncio, pytest-xdist are installed

## Steps Overview
- **Step 1**: Add test for dev dependencies in template
- **Step 2**: Update template to use `--extra dev`
- **Step 3**: Verify change, ensure tests pass, and update documentation
