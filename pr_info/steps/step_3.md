# Step 3: Add Blocked Label Support to get_next_action()

## LLM Prompt

```
Implement Step 3 of Issue #400 (see pr_info/steps/summary.md for context).

This step adds blocked label support to the get_next_action() function in status.py.

Follow TDD: Write tests first, then implement the functionality.
```

## Overview

Modify `get_next_action()` in `status.py` to accept a `blocked_label` parameter and return `"Blocked (label-name)"` when appropriate.

---

## Part A: Modify get_next_action() Function

### WHERE
- `src/mcp_coder/workflows/vscodeclaude/status.py`
- `tests/workflows/vscodeclaude/test_status.py`

### WHAT

**Current signature:**
```python
def get_next_action(
    is_stale: bool,
    is_dirty: bool,
    is_vscode_running: bool,
) -> str:
```

**New signature:**
```python
def get_next_action(
    is_stale: bool,
    is_dirty: bool,
    is_vscode_running: bool,
    blocked_label: str | None = None,
) -> str:
    """Determine next action for a session.

    Args:
        is_stale: Whether issue status changed
        is_dirty: Whether folder has uncommitted changes
        is_vscode_running: Whether VSCode is still running
        blocked_label: If set, the ignore label blocking this issue (e.g., "blocked", "wait")

    Returns:
        Action string like "(active)", "-> Restart", "-> Delete", "Blocked (blocked)"
    """
```

### HOW
- Add new parameter with default `None` for backward compatibility
- Add condition to check `blocked_label` when VSCode is not running
- No new imports needed

### ALGORITHM

```
1. If is_vscode_running: return "(active)"
2. If blocked_label is not None:
3.   If is_dirty: return "!! Manual"
4.   Else: return f"Blocked ({blocked_label})"
5. If is_stale:
6.   If is_dirty: return "!! Manual cleanup"
7.   Else: return "-> Delete (with --cleanup)"
8. Return "-> Restart"
```

### DATA

**Input scenarios:**
```python
# Blocked, VSCode closed, clean folder
get_next_action(is_stale=False, is_dirty=False, is_vscode_running=False, blocked_label="blocked")
# Returns: "Blocked (blocked)"

# Blocked, VSCode closed, dirty folder  
get_next_action(is_stale=False, is_dirty=True, is_vscode_running=False, blocked_label="wait")
# Returns: "!! Manual"

# Blocked but VSCode running (active takes priority)
get_next_action(is_stale=False, is_dirty=False, is_vscode_running=True, blocked_label="blocked")
# Returns: "(active)"

# Not blocked, normal behavior
get_next_action(is_stale=False, is_dirty=False, is_vscode_running=False, blocked_label=None)
# Returns: "-> Restart"
```

---

## Part B: Tests

### WHERE
- `tests/workflows/vscodeclaude/test_status.py`

### TEST CASES

Add to existing `TestGetNextAction` class or create new test class:

```python
class TestGetNextActionBlocked:
    """Tests for get_next_action with blocked_label parameter."""
    
    def test_blocked_clean_returns_blocked_message(self):
        """Blocked + clean folder shows Blocked message."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="blocked"
        )
        assert result == "Blocked (blocked)"
        
    def test_blocked_with_wait_label(self):
        """Blocked with wait label shows correct message."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="wait"
        )
        assert result == "Blocked (wait)"
        
    def test_blocked_dirty_returns_manual(self):
        """Blocked + dirty folder shows Manual message."""
        result = get_next_action(
            is_stale=False,
            is_dirty=True,
            is_vscode_running=False,
            blocked_label="blocked"
        )
        assert result == "!! Manual"
        
    def test_blocked_but_running_returns_active(self):
        """Running VSCode takes priority over blocked."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=True,
            blocked_label="blocked"
        )
        assert result == "(active)"
        
    def test_blocked_and_stale_blocked_takes_priority(self):
        """Blocked takes priority over stale when both true."""
        result = get_next_action(
            is_stale=True,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="blocked"
        )
        assert result == "Blocked (blocked)"
        
    def test_none_blocked_label_normal_behavior(self):
        """None blocked_label maintains normal behavior."""
        # Not stale, not dirty, not running -> Restart
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label=None
        )
        assert result == "-> Restart"
        
    def test_default_parameter_backward_compatible(self):
        """Function works without blocked_label parameter."""
        # Call without the new parameter
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False
        )
        assert result == "-> Restart"
        
    def test_preserves_label_case_in_output(self):
        """Output preserves the case of the label passed in."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="Blocked"  # Capital B
        )
        assert result == "Blocked (Blocked)"
```

---

## Part C: Verify Existing Tests Still Pass

The function signature change is backward compatible (new param has default), but verify:

```python
# Existing tests should still pass without modification
class TestGetNextAction:
    def test_running_vscode_returns_active(self):
        result = get_next_action(is_stale=False, is_dirty=False, is_vscode_running=True)
        assert result == "(active)"
        
    def test_stale_clean_returns_delete(self):
        result = get_next_action(is_stale=True, is_dirty=False, is_vscode_running=False)
        assert "Delete" in result
        
    def test_stale_dirty_returns_manual(self):
        result = get_next_action(is_stale=True, is_dirty=True, is_vscode_running=False)
        assert "Manual" in result
        
    def test_not_stale_not_dirty_returns_restart(self):
        result = get_next_action(is_stale=False, is_dirty=False, is_vscode_running=False)
        assert result == "-> Restart"
```

---

## Verification

After implementation, run:
```bash
pytest tests/workflows/vscodeclaude/test_status.py -v -k "next_action"
```

All tests should pass, confirming:
1. `blocked_label` parameter works correctly
2. Blocked message shows the label name
3. Dirty blocked sessions show manual action
4. Running VSCode takes priority
5. Backward compatibility maintained
