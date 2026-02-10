# Step 4: Update `get_stale_sessions()` to Include Ineligible Sessions

## LLM Prompt

```
Reference: pr_info/steps/summary.md and this step file.

Update `get_stale_sessions()` in cleanup.py to include sessions that are:
1. At bot statuses (not eligible for session)
2. At pr-created status
3. For closed issues

These should all be eligible for cleanup, not just status-changed sessions.
Follow TDD approach - update tests first.
```

## WHERE

- **Test file**: `tests/workflows/vscodeclaude/test_cleanup.py`
- **Implementation file**: `src/mcp_coder/workflows/vscodeclaude/cleanup.py`

## WHAT

### Changes to `get_stale_sessions()`

1. Add import: `from .issues import is_status_eligible_for_session`
2. Add import: `from .status import is_issue_closed`
3. Check for closed issues
4. Check for ineligible statuses (bot stages, pr-created)
5. Include these in the stale sessions list

### Updated Function Logic

The function currently returns sessions that are stale OR blocked.
Update to return sessions that are stale OR blocked OR closed OR ineligible.

## HOW

### Integration Points

- Import `is_status_eligible_for_session` from `.issues`
- Import `is_issue_closed` from `.status`
- Reuse existing `is_session_stale()` for status change detection

## ALGORITHM

```
For each session (with VSCode not running, in configured repo):
1. Get is_closed = check if issue is closed (from cache or API)
2. Get is_blocked = check for blocked label (existing logic)
3. Get is_stale = is_session_stale(session) (existing logic)
4. Get current_status from cache or session
5. Get is_ineligible = not is_status_eligible_for_session(current_status)
6. If is_stale OR is_blocked OR is_closed OR is_ineligible:
   a. Get git_status
   b. Add (session, git_status) to result
7. Return result
```

## DATA

### Test Scenarios

```python
# Existing behavior - stale session (status changed)
session(status="status-04:plan-review", current_github_status="status-07:code-review")
→ included in stale_sessions

# Existing behavior - blocked session
session(status="status-07:code-review", has_blocked_label=True)
→ included in stale_sessions

# NEW: Closed issue session
session(status="status-07:code-review", issue_closed=True)
→ included in stale_sessions

# NEW: Bot stage session
session(status="status-02:awaiting-planning", issue_open=True)
→ included in stale_sessions

# NEW: PR-created session
session(status="status-10:pr-created", issue_open=True)
→ included in stale_sessions

# NOT included - eligible status, open issue, not blocked
session(status="status-07:code-review", issue_open=True, not_blocked=True)
→ NOT in stale_sessions (should restart)
```

### Edge Cases

```python
# Session where we can't determine issue state (API error)
# Should be conservative - don't include in cleanup
session(status="status-07:code-review", api_error=True)
→ NOT in stale_sessions (conservative)
```

## Implementation Order

1. Add test cases for closed issue sessions being included
2. Add test cases for bot stage sessions being included
3. Add test cases for pr-created sessions being included
4. Add test case for eligible sessions NOT being included
5. Update imports in cleanup.py
6. Update `get_stale_sessions()` with new checks
7. Run tests to verify
