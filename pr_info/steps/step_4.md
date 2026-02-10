# Step 4: Update `restart_closed_sessions()` with Eligibility Checks + Module Docstring

## LLM Prompt

```
Reference: pr_info/steps/summary.md and this step file.

Update `restart_closed_sessions()` in orchestrator.py to:
1. Check if issue is closed → don't restart
2. Check if current status is eligible → don't restart if not
3. Remove the redundant is_session_stale() check (now covered by eligibility)

Also add a comprehensive module docstring documenting session lifecycle rules.
Follow TDD approach - update tests first.
```

## WHERE

- **Test file**: `tests/workflows/vscodeclaude/test_orchestrator_sessions.py`
- **Implementation file**: `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`

## WHAT

### Changes to `restart_closed_sessions()`

1. Add import: `from .issues import is_status_eligible_for_session`
2. After fetching issue data, check if issue is closed
3. Check if current status is eligible for session
4. **Remove** the redundant `is_session_stale()` check (eligibility check is more comprehensive)
5. Skip restart if either check fails

### New Module Docstring

Add comprehensive docstring at top of `orchestrator.py` documenting:
- Session lifecycle rules
- Which statuses need sessions
- Restart vs. stale logic
- Cleanup behavior
- Dirty folder protection

## HOW

### Integration Points

- Import `is_status_eligible_for_session` from `.issues`
- Add checks after existing issue fetch (around line 600)
- **Remove** the existing `is_session_stale()` check (it's now redundant)

### Location of New Checks

Insert after this existing code block:
```python
if issue["number"] == 0:
    logger.warning(...)
    continue
```

Add:
```python
# Check if issue is closed
if issue["state"] != "open":
    logger.info("Skipping closed issue #%d", issue_number)
    continue

# Check if status is eligible for session
current_status = get_issue_status(issue)
if not is_status_eligible_for_session(current_status):
    logger.info(
        "Skipping issue #%d: status %s doesn't need session",
        issue_number,
        current_status,
    )
    continue
```

### Remove Redundant Check

Delete this existing block (around line 580-585):
```python
# Check if session is stale (issue status changed)
if is_session_stale(session, cached_issues=repo_cached_issues):
    logger.info(
        "Skipping stale session for issue #%d (status changed)",
        session["issue_number"],
    )
    continue
```

## ALGORITHM

```
In restart_closed_sessions(), after fetching issue data:
1. If issue["state"] != "open" → log and continue (don't restart)
2. Get current_status from issue
3. If not is_status_eligible_for_session(current_status) → log and continue
4. Continue with existing restart logic (blocked label check, file regeneration, etc.)
```

## DATA

### Module Docstring Content

```python
"""Session orchestration for vscodeclaude feature.

Session Lifecycle Rules:
- Sessions are created for issues at human_action statuses with initial_command
- Eligible statuses: status-01:created, status-04:plan-review, status-07:code-review
- Ineligible: bot_pickup (02, 05, 08), bot_busy (03, 06, 09), pr-created (10)

Restart Behavior:
- Restart: Open issues at eligible statuses (01, 04, 07) without blocked labels
- Don't restart: Closed issues, bot statuses, pr-created, blocked issues

Cleanup Behavior:
- Stale sessions (status changed, closed, bot stage, pr-created) eligible for --cleanup
- Dirty folders (uncommitted changes) require manual cleanup, never auto-deleted

Dirty Folder Protection:
- Sessions with uncommitted git changes are never auto-deleted
- Display shows "!! Manual cleanup" for these cases
"""
```

### Test Scenarios

```python
# Should NOT restart - closed issue
session(status="status-07:code-review")
issue_on_github(state="closed")
→ session NOT restarted, logged "Skipping closed issue"

# Should NOT restart - bot stage
session(status="status-07:code-review")  # session has old status
issue_on_github(status="status-02:awaiting-planning", state="open")
→ session NOT restarted, logged "status doesn't need session"

# Should NOT restart - pr-created
session(status="status-07:code-review")  # session has old status
issue_on_github(status="status-10:pr-created", state="open")
→ session NOT restarted, logged "status doesn't need session"

# SHOULD restart - eligible status, open issue
session(status="status-07:code-review")
issue_on_github(status="status-07:code-review", state="open")
→ session IS restarted

# SHOULD restart - status changed but BOTH eligible (04 → 07)
session(status="status-04:plan-review")
issue_on_github(status="status-07:code-review", state="open")
→ session IS restarted with updated status
→ Files regenerated with new status
```

## Implementation Order

1. Add test cases for closed issues not being restarted
2. Add test cases for bot stage issues not being restarted
3. Add test cases for pr-created issues not being restarted
4. Add test cases for eligible issues being restarted
5. **Add test case for eligible-to-eligible transition (04 → 07)** - should restart with updated status
6. Add module docstring to orchestrator.py
7. Add import for `is_status_eligible_for_session`
8. Add closed issue check in `restart_closed_sessions()`
9. Add eligibility check in `restart_closed_sessions()`
10. **Remove** the redundant `is_session_stale()` check
11. Run all tests to verify

## Notes

- The existing `is_session_stale()` check is **removed** (not kept for logging) - cleaner code
- The new checks are more comprehensive: closed + eligibility covers all cases
- Existing blocked label check remains unchanged
- Status updates still happen for eligible-to-eligible transitions (e.g., 04 → 07)
