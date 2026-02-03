# Step 1: Add Environment Variable Setup to VENV_SECTION_WINDOWS

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.
Implement Step 1: Add environment variable setup and mismatch warning to VENV_SECTION_WINDOWS.
Follow TDD - extend the test first, then modify the template.
```

## Overview

Add `MCP_CODER_PROJECT_DIR` and `MCP_CODER_VENV_DIR` setup to the Windows venv section template, with a warning when a mismatch is detected.

## TDD: Test First

### WHERE
`tests/workflows/vscodeclaude/test_workspace.py`

### WHAT
Extend existing test `test_creates_script_with_venv_section` in `TestCreateStartupScriptV2` class.

### HOW
Add assertions to verify the generated script contains the env var setup.

### Test Code to Add

```python
# Add to existing test_creates_script_with_venv_section method, after existing assertions:
assert 'set "MCP_CODER_PROJECT_DIR=%CD%"' in content
assert 'set "MCP_CODER_VENV_DIR=%CD%\\.venv"' in content
```

## Implementation

### WHERE
`src/mcp_coder/workflows/vscodeclaude/templates.py`

### WHAT
Modify `VENV_SECTION_WINDOWS` constant.

### HOW
Add mismatch warning and env var setup after venv activation.

### ALGORITHM (pseudocode)

```
1. After venv activation succeeds:
2. IF MCP_CODER_PROJECT_DIR is defined AND not equal to %CD%:
3.   Display warning message with expected vs found values
4.   Pause for user acknowledgment
5. Set MCP_CODER_PROJECT_DIR=%CD%
6. Set MCP_CODER_VENV_DIR=%CD%\.venv
```

### Code to Add

Insert the following at the end of `VENV_SECTION_WINDOWS`, after the venv activation:

```batch
if defined MCP_CODER_PROJECT_DIR (
    if not "%MCP_CODER_PROJECT_DIR%"=="%CD%" (
        echo.
        echo WARNING: MCP_CODER_PROJECT_DIR mismatch detected
        echo   Expected: %CD%
        echo   Found:    %MCP_CODER_PROJECT_DIR%
        echo.
        echo Press any key to continue...
        pause >nul
    )
)
set "MCP_CODER_PROJECT_DIR=%CD%"
set "MCP_CODER_VENV_DIR=%CD%\.venv"
```

### DATA
No new data structures. Template string is modified in place.

## Verification

```bash
# Run the specific test
pytest tests/workflows/vscodeclaude/test_workspace.py::TestCreateStartupScriptV2::test_creates_script_with_venv_section -v
```

## Expected Outcome

- Test passes with new assertions
- Generated `.vscodeclaude_start.bat` contains env var setup
- Warning displayed if mismatch detected at runtime
