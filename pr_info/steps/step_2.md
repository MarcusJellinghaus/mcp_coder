# Step 2: Update Status Display and `check_folder_dirty()`

## LLM Prompt
```
Read pr_info/steps/summary.md for context on issue #413.
Implement Step 2: Update check_folder_dirty() to use new function and update status display in commands.py.
```

## Overview
Update existing `check_folder_dirty()` to use `get_folder_git_status()` internally, and update the status command to display the correct status string.

---

## Part A: Update `check_folder_dirty()`

### WHERE
`src/mcp_coder/workflows/vscodeclaude/status.py`

### WHAT
Refactor existing function to use new `get_folder_git_status()`:

```python
def check_folder_dirty(folder_path: Path) -> bool:
    """Check if folder has uncommitted changes.
    
    Args:
        folder_path: Path to git repository
        
    Returns:
        True if there are uncommitted changes OR if status cannot be determined
        (conservative approach for backward compatibility)
    """
```

### ALGORITHM
```python
def check_folder_dirty(folder_path: Path) -> bool:
    status = get_folder_git_status(folder_path)
    # Only "Clean" means definitely not dirty
    # All other states (Dirty, Missing, No Git, Error) return True
    return status != "Clean"
```

### HOW
- Replace the existing try/except implementation
- Preserves backward compatibility (same return type, same conservative behavior)

---

## Part B: Update Status Display in Commands

### WHERE
`src/mcp_coder/cli/commands/coordinator/commands.py`

### WHAT
In `execute_coordinator_vscodeclaude_status()`, use `get_folder_git_status()` for the "Changes" column display.

### CURRENT CODE (around line 520-530)
```python
# Check for uncommitted changes
folder_path = Path(session["folder"])
if folder_path.exists():
    is_dirty = check_folder_dirty(folder_path)
    changes = "Dirty" if is_dirty else "Clean"
else:
    changes = "-"
```

### NEW CODE
```python
# Check for uncommitted changes
folder_path = Path(session["folder"])
changes = get_folder_git_status(folder_path)
```

### HOW
- Import `get_folder_git_status` from `....workflows.vscodeclaude`
- Replace the if/else block with single function call
- The function returns the display string directly

---

## Part C: Update Import in commands.py

### WHERE
`src/mcp_coder/cli/commands/coordinator/commands.py`

### WHAT
Add `get_folder_git_status` to imports:

```python
from ....workflows.vscodeclaude import (
    ...
    check_folder_dirty,
    get_folder_git_status,  # Add this
    ...
)
```

---

## Part D: Verify Existing Tests Still Pass

### WHERE
`tests/workflows/vscodeclaude/test_status.py`

### WHAT
Existing tests for `check_folder_dirty()` should still pass since we preserved backward compatibility:
- `test_check_folder_dirty_clean` - expects `False` for clean repo
- `test_check_folder_dirty_with_changes` - expects `True` for dirty repo  
- `test_check_folder_dirty_returns_true_on_error` - expects `True` on error

---

## Verification
```bash
# Run all status tests
pytest tests/workflows/vscodeclaude/test_status.py -v

# Run coordinator tests
pytest tests/cli/commands/coordinator/test_commands.py -v
```
