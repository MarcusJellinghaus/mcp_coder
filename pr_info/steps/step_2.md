# Step 2: Remove V2 Suffix from Template Names

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.
Implement Step 2: Remove V2 suffix from template constant names.
This is a pure refactor - no test changes needed, just verify tests still pass.
```

## Overview

Clean up legacy naming by removing `_V2` suffix from 4 template constants and updating all 8 references.

## TDD Approach

No new tests needed - this is a refactor. Existing tests will verify the rename doesn't break functionality.

## Implementation

### Part A: Rename Constants in templates.py

### WHERE
`src/mcp_coder/workflows/vscodeclaude/templates.py`

### WHAT
Rename 4 constants:

| Current Name | New Name |
|--------------|----------|
| `AUTOMATED_SECTION_WINDOWS_V2` | `AUTOMATED_SECTION_WINDOWS` |
| `INTERACTIVE_SECTION_WINDOWS_V2` | `INTERACTIVE_SECTION_WINDOWS` |
| `STARTUP_SCRIPT_WINDOWS_V2` | `STARTUP_SCRIPT_WINDOWS` |
| `INTERVENTION_SCRIPT_WINDOWS_V2` | `INTERVENTION_SCRIPT_WINDOWS` |

### HOW
Find and replace in the constant definitions.

### ALGORITHM (pseudocode)

```
1. Find "AUTOMATED_SECTION_WINDOWS_V2" -> replace with "AUTOMATED_SECTION_WINDOWS"
2. Find "INTERACTIVE_SECTION_WINDOWS_V2" -> replace with "INTERACTIVE_SECTION_WINDOWS"
3. Find "STARTUP_SCRIPT_WINDOWS_V2" -> replace with "STARTUP_SCRIPT_WINDOWS"
4. Find "INTERVENTION_SCRIPT_WINDOWS_V2" -> replace with "INTERVENTION_SCRIPT_WINDOWS"
```

---

### Part B: Update References in workspace.py

### WHERE
`src/mcp_coder/workflows/vscodeclaude/workspace.py`

### WHAT
Update 8 references (4 in imports, 4 in function body).

### HOW

**Imports to update** (in `create_startup_script` function):
```python
from .templates import (
    AUTOMATED_SECTION_WINDOWS,  # was AUTOMATED_SECTION_WINDOWS_V2
    DISCUSSION_SECTION_WINDOWS,
    INTERACTIVE_SECTION_WINDOWS,  # was INTERACTIVE_SECTION_WINDOWS_V2
    INTERVENTION_SCRIPT_WINDOWS,  # was INTERVENTION_SCRIPT_WINDOWS_V2
    STARTUP_SCRIPT_WINDOWS,  # was STARTUP_SCRIPT_WINDOWS_V2
    VENV_SECTION_WINDOWS,
)
```

**Usages to update** (in function body):
- `AUTOMATED_SECTION_WINDOWS_V2` -> `AUTOMATED_SECTION_WINDOWS`
- `INTERACTIVE_SECTION_WINDOWS_V2` -> `INTERACTIVE_SECTION_WINDOWS`
- `STARTUP_SCRIPT_WINDOWS_V2` -> `STARTUP_SCRIPT_WINDOWS`
- `INTERVENTION_SCRIPT_WINDOWS_V2` -> `INTERVENTION_SCRIPT_WINDOWS`

### DATA
No data structure changes.

## Verification

```bash
# Run all workspace tests to verify refactor didn't break anything
pytest tests/workflows/vscodeclaude/test_workspace.py -v
```

## Expected Outcome

- All 4 constants renamed in templates.py
- All 8 references updated in workspace.py
- All existing tests pass unchanged
