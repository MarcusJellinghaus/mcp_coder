# Step 2: Update `display_status_table()` with "(Closed)" Prefix and Folder-Exists Filter

## LLM Prompt

```
Reference: pr_info/steps/summary.md and this step file.

Update `display_status_table()` in status.py to:
1. Show "(Closed)" prefix in Status column for closed issues
2. Only show closed issues if their session folder still exists
3. Use simple delete message `→ Delete (--cleanup)` for all stale sessions

Follow TDD approach - update tests first.
```

## WHERE

- **Test file**: `tests/workflows/vscodeclaude/test_status_display.py`
- **Implementation file**: `src/mcp_coder/workflows/vscodeclaude/status.py`

## WHAT

### Changes to `display_status_table()`

1. Remove the early `continue` for closed issues
2. Add folder existence check for closed issues (skip if folder missing)
3. Add "(Closed)" prefix to Status column for closed issues
4. Import `is_status_eligible_for_session` from `.issues` for stale detection
5. Compute `is_stale` based on: closed OR ineligible status OR status changed

## HOW

### Integration Points

- Import `is_status_eligible_for_session` from `.issues`
- Use existing `is_issue_closed()` to check closed state
- Use existing `is_session_stale()` for status change detection
- Check `Path(session["folder"]).exists()` for folder existence

## ALGORITHM

```
For each session:
1. Get folder_path = Path(session["folder"])
2. Get is_closed = is_issue_closed(session, cached_issues)
3. If is_closed AND NOT folder_path.exists() → skip (nothing to clean up)
4. Get current_status from cache or session
5. Get status_changed = is_session_stale(session, cached_issues)
6. Get is_eligible = is_status_eligible_for_session(current_status)
7. Compute is_stale = is_closed OR NOT is_eligible OR status_changed
8. Format status for display:
   - If is_closed → "(Closed) {status}"
   - Else → status as-is
9. Call get_next_action(is_stale, is_dirty, is_running, blocked_label)
   - Note: No stale_reason parameter - simple delete message
```

## DATA

### Test Scenarios

```python
# Closed issue with existing folder - should be shown with "(Closed)" prefix
session(status="status-07:code-review", issue_closed=True, folder_exists=True)
→ row shown with status "(Closed) status-07:code-review", action "→ Delete (--cleanup)"

# Closed issue with missing folder - should be SKIPPED
session(status="status-07:code-review", issue_closed=True, folder_exists=False)
→ row NOT shown (nothing to clean up)

# Bot stage - should be shown with delete message  
session(status="status-02:awaiting-planning", issue_open=True)
→ row shown with action "→ Delete (--cleanup)"

# PR created - should be shown with delete message
session(status="status-10:pr-created", issue_open=True)
→ row shown with action "→ Delete (--cleanup)"

# Eligible status, open issue - should show restart
session(status="status-07:code-review", issue_open=True)
→ row shown with action "→ Restart"

# Dirty folder cases - all show manual cleanup
session(status="status-02:awaiting-planning", issue_open=True, dirty=True)
→ row shown with action "!! Manual cleanup"

session(status="status-07:code-review", issue_closed=True, dirty=True)
→ row shown with status "(Closed) status-07:code-review", action "!! Manual cleanup"
```

## Implementation Order

1. Add test cases for "(Closed)" prefix in status column
2. Add test case for closed issue with missing folder being skipped
3. Add test cases for bot stage sessions showing simple delete action
4. Add test cases for pr-created sessions showing simple delete action
5. Update imports in `status.py`
6. Remove the early `continue` for closed issues
7. Add folder existence check for closed issues
8. Add "(Closed)" prefix formatting
9. Add `is_status_eligible_for_session` check for stale computation
10. Run tests to verify
