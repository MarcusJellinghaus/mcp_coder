# Step 2: Update `get_next_action()` with `stale_reason` Parameter

## LLM Prompt

```
Reference: pr_info/steps/summary.md and this step file.

Update the `get_next_action()` function in status.py to accept an optional `stale_reason` 
parameter that enables specific delete messages for different stale scenarios.
Follow TDD approach - update tests first.
```

## WHERE

- **Test file**: `tests/workflows/vscodeclaude/test_next_action.py`
- **Implementation file**: `src/mcp_coder/workflows/vscodeclaude/status.py`

## WHAT

### Updated Function Signature

```python
def get_next_action(
    is_stale: bool,
    is_dirty: bool,
    is_vscode_running: bool,
    blocked_label: str | None = None,
    stale_reason: str | None = None,  # NEW PARAMETER
) -> str:
    """Determine next action for a session.

    Args:
        is_stale: Whether issue status changed or session is ineligible
        is_dirty: Whether folder has uncommitted changes
        is_vscode_running: Whether VSCode is still running
        blocked_label: If set, the ignore label blocking this issue
        stale_reason: If set, specific reason for staleness (used in delete message)
                      Examples: "issue closed", "now at bot stage", "PR in GitHub"

    Returns:
        Action string like "(active)", "→ Restart", "→ Delete (--cleanup, reason)"
    """
```

## HOW

### Integration Points

- Backward compatible - existing callers don't need changes until step 3
- New callers pass `stale_reason` to get specific delete messages

## ALGORITHM

```
1. If is_vscode_running → return "(active)"
2. If blocked_label is not None:
   a. If is_dirty → return "!! Manual"
   b. Else → return f"Blocked ({blocked_label})"
3. If is_stale:
   a. If is_dirty → return "!! Manual cleanup"
   b. If stale_reason → return f"→ Delete (--cleanup, {stale_reason})"
   c. Else → return "→ Delete (with --cleanup)"
4. Return "→ Restart"
```

## DATA

### New Stale Reasons (Constants to use in callers)

```python
STALE_REASON_CLOSED = "issue closed"
STALE_REASON_BOT_STAGE = "now at bot stage"
STALE_REASON_PR_CREATED = "PR in GitHub"
STALE_REASON_STATUS_CHANGED = None  # Use default message
```

### New Test Cases (add to existing tests)

```python
# With stale_reason - clean folder
(True, False, False, None, "issue closed") → "→ Delete (--cleanup, issue closed)"
(True, False, False, None, "now at bot stage") → "→ Delete (--cleanup, now at bot stage)"
(True, False, False, None, "PR in GitHub") → "→ Delete (--cleanup, PR in GitHub)"

# With stale_reason - dirty folder (reason ignored, same message)
(True, True, False, None, "issue closed") → "!! Manual cleanup"
(True, True, False, None, "now at bot stage") → "!! Manual cleanup"

# Without stale_reason - backward compatible
(True, False, False, None, None) → "→ Delete (with --cleanup)"
```

## Implementation Order

1. Add new test cases to `test_next_action.py` for `stale_reason` parameter
2. Update `get_next_action()` signature and implementation
3. Run all existing tests to verify backward compatibility
4. Run new tests to verify stale_reason behavior
