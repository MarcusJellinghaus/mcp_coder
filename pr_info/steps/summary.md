# Issue #436: Fix Closed Issues Being Restarted

## Problem Statement

Closed GitHub issues are being restarted instead of ignored by the VSCodeClaude coordinator:

1. Status display shows closed issues with `→ Restart` action
2. After `--cleanup` removes sessions, orchestrator creates NEW sessions for closed issues
3. Warning appears: `"is_session_stale called on closed issue #414 - filter these out first"`

## Root Cause

The cache in `get_all_cached_issues()` **only fetches OPEN issues** (`state: "open"`), but sessions can exist for CLOSED issues.

When `restart_closed_sessions()` checks if a session's issue is closed:
1. Tries to look up issue in cache
2. Closed issues are NOT in cache (cache only has open issues)
3. Falls back to API call which works correctly
4. The issue is properly skipped (line 726 in orchestrator.py)

**However**, the problem is that closed issues from existing sessions aren't available to other functions that rely on the cache, leading to inconsistent behavior.

## Solution (KISS Approach)

Add an optional `additional_issues` parameter to `get_all_cached_issues()` that allows callers to request specific issue numbers to be fetched even if they're closed.

This is a **minimal, single-parameter addition** that:
- Keeps the cache generic and reusable
- Doesn't tightly couple cache to vscodeclaude
- Preserves all existing behavior
- Requires changes in only 2 files

## Architectural Changes

### Layer 2 (Infrastructure - Cache Module)
**File**: `src/mcp_coder/utils/github_operations/issues/cache.py`

**Change**: Add `additional_issues: list[int] | None = None` parameter to `get_all_cached_issues()`

**Behavior**:
- If `additional_issues` is None or empty: behaves exactly as before (fetch open issues only)
- If `additional_issues` is provided: fetch ALL open issues + the specific additional issues via individual API calls
- Additional issues are merged into the cache just like open issues

**Design Decision**: Passing "what to fetch" DOWN from application layer (vscodeclaude) to infrastructure layer (cache) is acceptable because:
1. It keeps the cache generic - any caller can use this parameter
2. No tight coupling - cache doesn't know about vscodeclaude
3. Simple parameter addition preserves backward compatibility

### Layer 5 (Orchestration - Orchestrator Module)
**File**: `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`

**Change**: In `restart_closed_sessions()`, extract session issue numbers and pass them to `get_all_cached_issues()` via `additional_issues` parameter.

**Flow**:
1. Load sessions first
2. Extract issue numbers from all sessions
3. For each repo, pass those issue numbers to `get_all_cached_issues(additional_issues=[...])`
4. This ensures closed issues from existing sessions are in the cache

## Files to Modify

### Core Implementation
1. `src/mcp_coder/utils/github_operations/issues/cache.py`
   - Add `additional_issues` parameter to `get_all_cached_issues()`
   - Add logic to fetch additional issues via individual API calls
   - Merge additional issues into cache

2. `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`
   - Modify `restart_closed_sessions()` to pass session issue numbers to cache

### Tests
3. `tests/utils/github_operations/test_issue_cache.py` (new file)
   - Test cache with `additional_issues` parameter
   - Test that closed issues are fetched when requested
   - Test that cache behavior unchanged when parameter not provided

4. `tests/workflows/vscodeclaude/test_orchestrator.py` (new file or extend existing)
   - Test that `restart_closed_sessions()` passes session issues to cache
   - Test that closed issues are properly skipped

## Benefits of This Approach

1. **Minimal Code Changes**: Only 2 files modified for core functionality
2. **Backward Compatible**: Existing code continues to work without changes
3. **Generic Solution**: Any caller can use `additional_issues`, not just vscodeclaude
4. **Clear Separation**: Cache remains infrastructure, orchestrator remains application logic
5. **Easy to Test**: Simple parameter addition with clear behavior
6. **Easy to Maintain**: No complex logic, just fetch additional issues and merge

## What This Does NOT Fix

This implementation focuses on ensuring the cache has the data it needs. The existing code already:
- ✅ Filters closed issues in `_filter_eligible_vscodeclaude_issues()` (line 167 in issues.py)
- ✅ Skips closed issues in `restart_closed_sessions()` (line 726 in orchestrator.py)
- ✅ Shows closed sessions with "(Closed)" prefix in status display (line 190-191 in status.py)

These existing safeguards remain in place as defense-in-depth.

## Implementation Order

1. **Step 1**: Add `additional_issues` parameter to cache (with tests)
2. **Step 2**: Update orchestrator to use the parameter (with tests)
3. **Step 3**: Integration tests and verification
