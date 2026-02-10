# Step 2: Add `skip_reason` Parameter to `get_next_action()`

## LLM Prompt

```
Implement Step 2 of Issue #422 (see pr_info/steps/summary.md for full context).

Add the `skip_reason` parameter to get_next_action() in status.py with TDD approach.
This parameter consolidates multiple error conditions into a single string indicator.
```

---

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/status.py` | MODIFY function |
| `tests/workflows/vscodeclaude/test_next_action.py` | ADD tests |

---

## WHAT

### Modified Function Signature

```python
def get_next_action(
    is_stale: bool,
    is_dirty: bool,
    is_vscode_running: bool,
    blocked_label: str | None = None,
    skip_reason: str | None = None,  # NEW PARAMETER
) -> str:
    """Determine next action for a session.

    Args:
        is_stale: Whether issue status changed
        is_dirty: Whether folder has uncommitted changes
        is_vscode_running: Whether VSCode is still running
        blocked_label: If set, the ignore label blocking this issue
        skip_reason: If set, reason session cannot restart:
                     "No branch", "Dirty", "Git error", "Multi-branch"

    Returns:
        Action string like "(active)", "→ Restart", "!! No branch"
    """
```

---

## HOW

### Integration Points

1. Modify existing function at line ~105 in `status.py`
2. Add `skip_reason` check early in the logic (after `is_vscode_running`)
3. Existing callers continue to work (parameter has default `None`)

---

## ALGORITHM

```python
def get_next_action(..., skip_reason: str | None = None) -> str:
    if is_vscode_running:
        return "(active)"
    if skip_reason:
        return f"!! {skip_reason}"
    if blocked_label is not None:
        if is_dirty:
            return "!! Manual"
        return f"Blocked ({blocked_label})"
    if is_stale:
        if is_dirty:
            return "!! Manual cleanup"
        return "→ Delete (with --cleanup)"
    return "→ Restart"
```

---

## DATA

### Input (new parameter)
- `skip_reason: str | None` - One of: `None`, `"No branch"`, `"Dirty"`, `"Git error"`, `"Multi-branch"`

### Output Priority
1. `(active)` - VSCode running
2. `!! {skip_reason}` - Skip reason provided
3. `!! Manual` / `Blocked (label)` - Blocked
4. `!! Manual cleanup` / `→ Delete` - Stale
5. `→ Restart` - Normal restart

### Test Cases

| skip_reason | is_vscode_running | Expected |
|-------------|-------------------|----------|
| `"No branch"` | `False` | `"!! No branch"` |
| `"Dirty"` | `False` | `"!! Dirty"` |
| `"Git error"` | `False` | `"!! Git error"` |
| `"No branch"` | `True` | `"(active)"` (running takes priority) |
| `None` | `False` | (existing logic applies) |

---

## TEST IMPLEMENTATION

### File: `tests/workflows/vscodeclaude/test_next_action.py`

Add new test class:

```python
class TestGetNextActionSkipReason:
    """Tests for skip_reason parameter in get_next_action()."""

    def test_skip_reason_no_branch(self) -> None:
        """skip_reason='No branch' returns !! No branch."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            skip_reason="No branch",
        )
        assert result == "!! No branch"

    def test_skip_reason_dirty(self) -> None:
        """skip_reason='Dirty' returns !! Dirty."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            skip_reason="Dirty",
        )
        assert result == "!! Dirty"

    def test_skip_reason_git_error(self) -> None:
        """skip_reason='Git error' returns !! Git error."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            skip_reason="Git error",
        )
        assert result == "!! Git error"

    def test_vscode_running_takes_priority_over_skip_reason(self) -> None:
        """VSCode running takes priority over skip_reason."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=True,
            skip_reason="No branch",
        )
        assert result == "(active)"

    def test_skip_reason_takes_priority_over_blocked(self) -> None:
        """skip_reason takes priority over blocked_label."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="blocked",
            skip_reason="No branch",
        )
        assert result == "!! No branch"

    def test_skip_reason_takes_priority_over_stale(self) -> None:
        """skip_reason takes priority over is_stale."""
        result = get_next_action(
            is_stale=True,
            is_dirty=False,
            is_vscode_running=False,
            skip_reason="Git error",
        )
        assert result == "!! Git error"

    def test_none_skip_reason_uses_existing_logic(self) -> None:
        """None skip_reason falls through to existing logic."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            skip_reason=None,
        )
        assert result == "→ Restart"
```

---

## VERIFICATION

After implementation, run:

```bash
pytest tests/workflows/vscodeclaude/test_next_action.py -v
```

All existing tests should still pass, plus the 7 new tests.
