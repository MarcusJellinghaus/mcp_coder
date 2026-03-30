# Step 1: Fix PATH ordering in VENV_SECTION_WINDOWS

## Context

See `pr_info/steps/summary.md` for full issue context (Issue #643).

## Problem

In `VENV_SECTION_WINDOWS` (file: `src/mcp_coder/workflows/vscodeclaude/templates.py`), `mcp-coder --version` is called on line 2 of the template, but `MCP_CODER_VENV_PATH` isn't set and added to `PATH` until much later (after the entire venv creation/activation block). This means `mcp-coder` is not found.

## WHERE

- **Modify**: `src/mcp_coder/workflows/vscodeclaude/templates.py` — the `VENV_SECTION_WINDOWS` string constant
- **Modify**: `tests/workflows/vscodeclaude/test_templates.py` — add test for PATH ordering

## WHAT

Reorder the `VENV_SECTION_WINDOWS` template so that:

1. `echo Setting up environments...` (keep as-is)
2. **Move here**: The `MCP_CODER_VENV_PATH` assignment block (the `if "{mcp_coder_install_path}" NEQ ""` block with error handling)
3. **Move here**: `set "PATH=%MCP_CODER_VENV_PATH%;%PATH%"` (currently near the bottom)
4. **Move here**: `echo MCP-Coder environment: %MCP_CODER_VENV_PATH%` (for visibility)
5. `mcp-coder --version` (now works because PATH is set)
6. `echo   MCP-Coder install:` and `echo   Project directory:` lines
7. Rest of the template (MCP env vars, venv setup, editable install) — but **remove** the duplicate `set "PATH=%MCP_CODER_VENV_PATH%;%PATH%"` line that was near the bottom

## HOW

Edit the raw string constant `VENV_SECTION_WINDOWS` directly. No function signatures change. No imports change.

## ALGORITHM (pseudocode of new ordering)

```
echo Setting up environments...
SET MCP_CODER_VENV_PATH from {mcp_coder_install_path} (with error check)
SET PATH = MCP_CODER_VENV_PATH + PATH
mcp-coder --version
echo install path and project directory info
SET MCP environment variables (MCP_CODER_PROJECT_DIR, MCP_CODER_VENV_DIR)
venv creation/activation block (unchanged)
# REMOVED: duplicate "set PATH=..." line that was here
uv pip install -e . --no-deps
echo Environment setup complete.
```

## DATA

No return values or data structures change. This is a template string edit only.

## Test Plan

### Test: PATH is set before mcp-coder --version call (TDD — write first)

**File**: `tests/workflows/vscodeclaude/test_templates.py`

**Function**: `test_venv_section_path_set_before_mcp_coder_version()`

**Logic**: In `VENV_SECTION_WINDOWS`, find the line index of `set "PATH=%MCP_CODER_VENV_PATH%;%PATH%"` and the line index of `mcp-coder --version`. Assert PATH line comes first.

### Test: No duplicate PATH assignment

**Function**: `test_venv_section_no_duplicate_path_assignment()`

**Logic**: Count occurrences of `PATH=%MCP_CODER_VENV_PATH%` in `VENV_SECTION_WINDOWS`. Assert count == 1.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for full context.

Implement Step 1: Fix PATH ordering in VENV_SECTION_WINDOWS.

1. First, add two tests to tests/workflows/vscodeclaude/test_templates.py:
   - test_venv_section_path_set_before_mcp_coder_version: assert PATH assignment appears before mcp-coder --version
   - test_venv_section_no_duplicate_path_assignment: assert PATH=%MCP_CODER_VENV_PATH% appears exactly once

2. Then edit VENV_SECTION_WINDOWS in src/mcp_coder/workflows/vscodeclaude/templates.py:
   - Move the MCP_CODER_VENV_PATH assignment block (if "{mcp_coder_install_path}" NEQ "" ... ) to right after "echo Setting up environments..."
   - Add set "PATH=%MCP_CODER_VENV_PATH%;%PATH%" immediately after that block
   - Keep mcp-coder --version after PATH is set
   - Remove the duplicate set "PATH=..." line from later in the template

3. Run all three code quality checks (pylint, pytest, mypy). Fix any issues.
```
