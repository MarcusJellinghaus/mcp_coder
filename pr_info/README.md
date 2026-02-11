# Issue #436 Implementation Plan

## Quick Start

1. Read `steps/summary.md` for complete architectural overview
2. Implement steps in order:
   - `steps/step_1.md` - Add `additional_issues` parameter to cache
   - `steps/step_2.md` - Update orchestrator to use the parameter
   - `steps/step_3.md` - Integration tests and verification

## Files Modified

### Core Implementation (2 files)
1. `src/mcp_coder/utils/github_operations/issues/cache.py`
   - Add `additional_issues` parameter to `get_all_cached_issues()`
   - Add `_fetch_additional_issues()` helper function

2. `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`
   - Add `_build_cached_issues_by_repo()` helper function
   - Modify `restart_closed_sessions()` to build cache with session issues

### Tests (3 new files)
3. `tests/utils/github_operations/test_issue_cache.py`
   - Unit tests for cache `additional_issues` functionality

4. `tests/workflows/vscodeclaude/test_orchestrator_cache.py`
   - Unit tests for orchestrator cache building

5. `tests/workflows/vscodeclaude/test_closed_issues_integration.py`
   - Integration tests for complete closed issue workflow

## Implementation Approach

### KISS Principle Applied
- **Minimal change**: Single parameter addition to existing function
- **No refactoring**: Existing code logic preserved
- **Backward compatible**: Default parameter value maintains current behavior
- **Defense in depth**: Multiple layers verify closed issues are handled

### Test-Driven Development
Each step follows TDD:
1. Write tests first (they fail)
2. Implement functionality
3. Tests pass
4. Move to next step

## Architecture Summary

### Layer 2: Infrastructure (Cache)
- Add optional `additional_issues` parameter
- Fetch specific issues even if closed
- Generic solution - any caller can use it

### Layer 5: Orchestration (Orchestrator)
- Build cache with session issue numbers
- Pass to `get_all_cached_issues(additional_issues=[...])`
- Ensures closed session issues are in cache

### No changes to other layers
- Existing filters remain in place (defense in depth)
- Status display already shows closed correctly
- Issue filtering already excludes closed

## Testing Strategy

### Unit Tests (Steps 1 & 2)
- Fast, isolated tests
- Mock external dependencies
- Verify individual functions

### Integration Tests (Step 3)
- Complete workflow tests
- Real data structures
- End-to-end verification

### Manual Verification
- Real GitHub issues
- Real closed issue scenario
- User-facing behavior check

## Expected Outcome

### Before Fix
```
mcp-coder coordinator vscodeclaude status

Folder               Issue  Status           VSCode     Repo            Next Action
-------------------------------------------------------------------------------------------------
mcp_coder_414        #414   status-07:cr...  Closed     mcp_coder       → Restart  ❌
mcp_coder_408        #408   status-07:cr...  Closed     mcp_coder       → Restart  ❌
```

After `--cleanup`, new sessions created for #414 and #408 (both closed) ❌

### After Fix
```
mcp-coder coordinator vscodeclaude status

Folder               Issue  Status                    VSCode     Repo            Next Action
-------------------------------------------------------------------------------------------------
mcp_coder_414        #414   (Closed) status-07:cr...  Closed     mcp_coder       → Delete (with --cleanup)  ✅
mcp_coder_408        #408   (Closed) status-07:cr...  Closed     mcp_coder       → Delete (with --cleanup)  ✅
```

After `--cleanup`, sessions removed and no new sessions created ✅

## Key Design Decisions

### 1. Why add parameter to cache instead of filter closed in caller?
- **Cache is source of truth**: If cache has the data, all callers benefit
- **Generic solution**: Any caller can use `additional_issues`, not just vscodeclaude
- **Simple**: Single parameter addition vs complex filtering logic in multiple places

### 2. Why build cache in orchestrator instead of higher level?
- **Self-contained**: Function knows what it needs
- **Simpler**: No changes to command handlers
- **Testable**: Easier to unit test
- **Future-proof**: Can optimize later by moving cache build up if needed

### 3. Why keep existing filters in place?
- **Defense in depth**: Multiple layers catch closed issues
- **Fail-safe**: If one check fails, others catch it
- **Clear intent**: Each layer documents what it should ignore

## Time Estimate

- Step 1: 1-2 hours (cache parameter + tests)
- Step 2: 1-2 hours (orchestrator update + tests)
- Step 3: 1-2 hours (integration tests + verification)
- **Total**: 3-6 hours including testing and documentation

## Verification Checklist

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Existing tests still pass (no regressions)
- [ ] Manual test with real closed issue succeeds
- [ ] Status display shows correct information
- [ ] No new sessions created for closed issues after cleanup
- [ ] Warning "is_session_stale called on closed issue" eliminated
- [ ] Code review completed
- [ ] Documentation updated

## Success Criteria

1. ✅ Closed issues never show "→ Restart"
2. ✅ Closed issues show "→ Delete (with --cleanup)"
3. ✅ After cleanup, no new sessions for closed issues
4. ✅ Cache includes closed issues from sessions
5. ✅ All tests pass
6. ✅ No regressions in existing functionality
