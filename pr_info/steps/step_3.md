# Step 3: Integration Tests and Verification

## LLM Prompt

```
You are implementing Step 3 of issue #436 "Fix Closed Issues Being Restarted".

Read pr_info/steps/summary.md for context, then implement the following:

Add integration tests that verify the complete flow works end-to-end, ensuring closed issues are properly handled throughout the system.

Follow Test-Driven Development:
1. First write the integration tests
2. Run tests to verify the fix works
3. Add any additional logging or documentation

Refer to this step file (step_3.md) for detailed specifications.
```

---

## WHERE: File Locations

### Tests
- **File**: `tests/workflows/vscodeclaude/test_closed_issues_integration.py` (NEW FILE)

### Verification Script (Optional)
- **File**: `scripts/verify_closed_issues_fix.py` (NEW FILE)
  - Manual verification script for testing with real GitHub issues

---

## WHAT: Integration Test Scenarios

### Test Scope
Integration tests verify the complete flow from cache → orchestrator → status display, ensuring:
1. Closed issues from sessions are fetched in cache
2. Closed issues are properly skipped in restart flow
3. Status display shows correct information
4. No new sessions created for closed issues

---

## TEST SPECIFICATIONS

### Test File: `tests/workflows/vscodeclaude/test_closed_issues_integration.py`

#### Test 1: `test_closed_issue_session_not_restarted`
**Scenario**: User has an active session for issue #414, then the issue gets closed

**Given**:
- Session exists for issue #414 (was open, now closed)
- VSCode is not running (PID check fails)
- Folder exists and is clean

**When**: 
- Run `restart_closed_sessions()`

**Then**:
- Issue #414 is fetched via `additional_issues` parameter
- Issue #414 state is detected as "closed"
- Log message: "Skipping closed issue #414"
- Session is NOT restarted
- No VSCode launch attempted

**Verification**:
```python
# Mock setup
mock_sessions = [{"repo": "owner/repo", "issue_number": 414, ...}]
mock_issue_414 = {"number": 414, "state": "closed", "labels": [...]}

# Expected behavior
assert not vscode_launched
assert "Skipping closed issue #414" in log_output
```

#### Test 2: `test_process_eligible_issues_excludes_closed`
**Scenario**: Closed issues should never get new sessions created

**Given**:
- Cache has issue #414 (closed) and #100 (open, eligible)
- No existing sessions

**When**: 
- Run `process_eligible_issues()`

**Then**:
- Only issue #100 is processed
- Issue #414 is filtered out by `_filter_eligible_vscodeclaude_issues()`
- No session created for #414

**Verification**:
```python
# Mock setup
cached_issues = [
    {"number": 414, "state": "closed", "labels": ["status-07:code-review"], ...},
    {"number": 100, "state": "open", "labels": ["status-07:code-review"], ...},
]

# Expected behavior
assert len(started_sessions) == 1
assert started_sessions[0]["issue_number"] == 100
```

#### Test 3: `test_status_display_shows_closed_correctly`
**Scenario**: Status table should show closed sessions with correct action

**Given**:
- Session exists for issue #414 (closed)
- Cache includes issue #414 via `additional_issues`

**When**: 
- Run `display_status_table()`

**Then**:
- Status column shows: "(Closed) status-07:code-review"
- Next Action shows: "→ Delete (with --cleanup)"

**Verification**:
```python
# Expected output (captured from stdout)
assert "(Closed)" in status_output
assert "→ Delete (with --cleanup)" in status_output or "!! Manual" in status_output
```

#### Test 4: `test_cache_with_mixed_open_and_closed_sessions`
**Scenario**: Multiple sessions with mix of open and closed issues

**Given**:
- Sessions: #414 (closed), #408 (closed), #100 (open)
- Cache fetched with `additional_issues=[414, 408, 100]`

**When**: 
- Run `restart_closed_sessions()`

**Then**:
- All three issues are in cache
- Issues #414 and #408 are skipped (closed)
- Issue #100 is restarted (if VSCode closed and repo clean)

**Verification**:
```python
# Expected behavior
assert len(cache[414]) > 0  # Issue #414 in cache
assert len(cache[408]) > 0  # Issue #408 in cache
assert len(cache[100]) > 0  # Issue #100 in cache
assert restarted_count == 1  # Only #100 restarted
```

#### Test 5: `test_end_to_end_closed_issue_workflow`
**Scenario**: Complete workflow from session creation → close → cleanup

**Given**:
- Initial state: Issue #414 is open with session
- Action: Issue #414 gets closed on GitHub
- Current state: Session still exists locally

**When**: 
1. Run `restart_closed_sessions()` (should skip #414)
2. Run status display (should show "Closed")
3. Run cleanup (should remove session if folder clean)

**Then**:
- Step 1: Issue #414 not restarted, log shows "Skipping closed issue"
- Step 2: Status shows "(Closed)" and "→ Delete (with --cleanup)"
- Step 3: Session removed from sessions.json

**Verification**:
```python
# After step 1
assert not vscode_restarted_for_414

# After step 2
assert "(Closed)" in status_display

# After step 3 (cleanup)
final_sessions = load_sessions()
assert not any(s["issue_number"] == 414 for s in final_sessions["sessions"])
```

---

## VERIFICATION SCRIPT SPECIFICATIONS

### Script: `scripts/verify_closed_issues_fix.py`

This optional script helps manually verify the fix with real GitHub issues.

```python
#!/usr/bin/env python3
"""Manual verification script for closed issues fix.

Usage:
    python scripts/verify_closed_issues_fix.py

This script:
1. Creates a test session for a closed issue
2. Runs restart_closed_sessions()
3. Verifies the issue is skipped
4. Cleans up test data
"""

def main():
    # 1. Setup: Create test session for closed issue
    # 2. Run: Call restart_closed_sessions()
    # 3. Verify: Check logs and behavior
    # 4. Cleanup: Remove test session
    pass
```

**Key Checks**:
- Cache includes the closed issue
- Restart logic skips the closed issue
- Status display shows correct information
- No new sessions created

---

## IMPLEMENTATION CHECKLIST

- [ ] Write integration test file with 5 test scenarios
- [ ] Run integration tests
- [ ] Fix any issues discovered
- [ ] Write verification script (optional)
- [ ] Update documentation with fix details
- [ ] Run full test suite to ensure no regressions
- [ ] Manual verification with real closed issues

---

## ACCEPTANCE CRITERIA

### The fix is complete when:

1. **Cache Behavior**:
   - ✅ `additional_issues` parameter works correctly
   - ✅ Closed issues are fetched when requested
   - ✅ Backward compatibility maintained

2. **Orchestrator Behavior**:
   - ✅ Closed issues from sessions are in cache
   - ✅ Closed issues are skipped in restart flow
   - ✅ Log messages indicate closed issues are skipped

3. **Status Display**:
   - ✅ Shows "(Closed)" prefix for closed issues
   - ✅ Shows correct next action for closed sessions

4. **No Regressions**:
   - ✅ All existing tests pass
   - ✅ Open issues still create sessions correctly
   - ✅ Open issues still restart correctly

5. **Issue Requirements Met**:
   - ✅ Closed issues show "→ Delete (with --cleanup)", not "→ Restart"
   - ✅ After cleanup, no new sessions created for closed issues
   - ✅ Warning "is_session_stale called on closed issue" eliminated or properly handled

---

## TESTING STRATEGY

### Unit Tests (Steps 1 & 2)
- Test individual functions in isolation
- Mock external dependencies
- Fast execution

### Integration Tests (This Step)
- Test complete workflows
- Use real data structures
- May use test fixtures or light mocking

### Manual Testing
- Real GitHub repository
- Real closed issues
- Verify user-facing behavior

---

## LOGGING IMPROVEMENTS

Add or verify these log messages exist:

1. **Cache** (`cache.py`):
   ```python
   logger.debug(f"Fetching {len(additional_issues)} additional issues for {repo_name}")
   ```

2. **Orchestrator** (`orchestrator.py`):
   ```python
   logger.info(f"Skipping closed issue #{issue_number}")
   logger.debug(f"Built cache for {len(cached_issues_by_repo)} repos with session issues")
   ```

3. **Status** (`status.py`):
   ```python
   # Existing warning is fine:
   logger.warning(f"is_session_stale called on closed issue #{issue_number} - filter these out first")
   ```

---

## DOCUMENTATION UPDATES

### Update These Files

1. **CLAUDE.md** (if it contains workflow documentation):
   - Add note about closed issue handling
   - Mention the fix for issue #436

2. **orchestrator.py docstring**:
   - Update `restart_closed_sessions()` docstring to mention closed issues are skipped

3. **cache.py docstring**:
   - Update `get_all_cached_issues()` docstring to document `additional_issues` parameter

---

## NOTES

### Why Integration Tests Matter
Unit tests verify individual functions work, but integration tests catch issues like:
- Cache fetched correctly but orchestrator doesn't use it
- Orchestrator uses cache but status display doesn't show it
- All components work individually but don't integrate properly

### Test Data Setup
Use realistic test data that mirrors production:
- Real session structure
- Real issue data structure  
- Real status labels

### Performance Considerations
Integration tests may be slower than unit tests due to:
- More complex setup
- More components involved
- Potential file I/O

Keep integration tests focused and minimal.
