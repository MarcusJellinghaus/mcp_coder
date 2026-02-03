# Step 3: Final Verification

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.
Implement Step 3: Run final verification to ensure all changes work correctly.
```

## Overview

Verify all changes are complete and tests pass.

## Verification Commands

```bash
# Run all vscodeclaude workflow tests
pytest tests/workflows/vscodeclaude/ -v

# Run specific workspace tests
pytest tests/workflows/vscodeclaude/test_workspace.py -v

# Run type checking
mypy src/mcp_coder/workflows/vscodeclaude/templates.py src/mcp_coder/workflows/vscodeclaude/workspace.py

# Run linting
pylint src/mcp_coder/workflows/vscodeclaude/templates.py src/mcp_coder/workflows/vscodeclaude/workspace.py
```

## Acceptance Criteria Checklist

Verify each item manually:

- [ ] `VENV_SECTION_WINDOWS` contains `set "MCP_CODER_PROJECT_DIR=%CD%"`
- [ ] `VENV_SECTION_WINDOWS` contains `set "MCP_CODER_VENV_DIR=%CD%\.venv"`
- [ ] `VENV_SECTION_WINDOWS` contains mismatch warning with pause
- [ ] `AUTOMATED_SECTION_WINDOWS_V2` renamed to `AUTOMATED_SECTION_WINDOWS`
- [ ] `INTERACTIVE_SECTION_WINDOWS_V2` renamed to `INTERACTIVE_SECTION_WINDOWS`
- [ ] `STARTUP_SCRIPT_WINDOWS_V2` renamed to `STARTUP_SCRIPT_WINDOWS`
- [ ] `INTERVENTION_SCRIPT_WINDOWS_V2` renamed to `INTERVENTION_SCRIPT_WINDOWS`
- [ ] All 8 references in workspace.py updated
- [ ] Test `test_creates_script_with_venv_section` verifies env vars
- [ ] All tests pass

## Expected Outcome

All tests pass and acceptance criteria are met.
