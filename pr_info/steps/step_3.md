# Step 3: Update `display_status_table()` to Show Closed Issues and Compute Stale Reasons

## LLM Prompt

```
Reference: pr_info/steps/summary.md and this step file.

Update `display_status_table()` in status.py to:
1. Show closed issues (remove the skip)
2. Compute appropriate stale_reason for each session
3. Pass stale_reason to get_next_action()

Follow TDD approach - update tests first.
```

## WHERE

- **Test file**: `tests/workflows/vscodeclaude/test_status_display.py`
- **Implementation file**: `src/mcp_coder/workflows/vscodeclaude/status.py`

## WHAT

### Changes to `display_status_table()`

1. Remove the early `continue` for closed issues
2. Add import: `from .issues import is_status_eligible_for_session`
3. Compute `stale_reason` based on session state
4. Pass `stale_reason` to `get_next_action()`

### New Helper Function (optional, can be inline)

```python
def _compute_stale_reason(
    is_closed: bool,
    status: str,
    status_changed: bool,
) -> str | None:
    """Compute the reason a session is stale.
    
    Args:
        is_closed: Whether the issue is closed
        status: Current status label
        status_changed: Whether status differs from session
        
    Returns:
        Reason string or None if not stale
    """
```

## HOW

### Integration Points

- Import `is_status_eligible_for_session` from `.issues`
- Use existing `is_issue_closed()` to check closed state
- Use existing `is_session_stale()` for status change detection

## ALGORITHM

```
For each session:
1. Get is_closed from is_issue_closed(session, cached_issues)
2. Get current_status from cache or session
3. Get status_changed from is_session_stale(session, cached_issues)
4. Compute stale_reason:
   a. If is_closed → "issue closed"
   b. Elif not is_status_eligible_for_session(current_status):
      - If status is "status-10:pr-created" → "PR in GitHub"
      - Else → "now at bot stage"
   c. Elif status_changed → None (use default message)
   d. Else → None (not stale)
5. Compute is_stale = stale_reason is not None or status_changed
6. Call get_next_action(is_stale, is_dirty, is_running, blocked_label, stale_reason)
```

## DATA

### Test Scenarios

```python
# Closed issue - should be shown with delete message
session(status="status-07:code-review", issue_closed=True)
→ row shown with action "→ Delete (--cleanup, issue closed)"

# Bot stage - should be shown with delete message  
session(status="status-02:awaiting-planning", issue_open=True)
→ row shown with action "→ Delete (--cleanup, now at bot stage)"

# PR created - should be shown with delete message
session(status="status-10:pr-created", issue_open=True)
→ row shown with action "→ Delete (--cleanup, PR in GitHub)"

# Eligible status, open issue - should show restart
session(status="status-07:code-review", issue_open=True)
→ row shown with action "→ Restart"

# Dirty folder cases
session(status="status-02:awaiting-planning", issue_open=True, dirty=True)
→ row shown with action "!! Manual cleanup"
```

## Implementation Order

1. Add test cases for closed issues being displayed (not skipped)
2. Add test cases for bot stage sessions showing correct action
3. Add test cases for pr-created sessions showing correct action
4. Update `display_status_table()` to remove closed issue skip
5. Add stale_reason computation logic
6. Update `get_next_action()` call to pass stale_reason
7. Run tests to verify
