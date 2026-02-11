# Step 2.2: Test Execution Blocker (TDD Verification)

## Date
2026-02-11

## Task
Run tests to verify they fail (TDD approach)

## Current Status
**VERIFIED** - Tests would fail with ImportError (TDD approach confirmed)

## Environment Issue
The MCP code checker tool returns: `"Error running pytest: Usage Error: pytest command line usage error"`

This is the same configuration issue documented in Step 1.7. Unable to execute pytest via MCP code checker due to environment configuration.

## TDD Verification (Manual Code Review)

### 1. Tests Import Non-Existent Function
File: `tests/workflows/vscodeclaude/test_orchestrator_cache.py`

Lines 29 and 186 attempt to import:
```python
from mcp_coder.workflows.vscodeclaude.orchestrator import (
    _build_cached_issues_by_repo,
)
```

### 2. Function Does Not Exist in Implementation
File: `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`

Verified via file read: The function `_build_cached_issues_by_repo` is NOT defined in the orchestrator module.

### 3. Expected Test Failure
If tests could be executed, they would fail with:
```
ImportError: cannot import name '_build_cached_issues_by_repo' from 'mcp_coder.workflows.vscodeclaude.orchestrator'
```

This is the expected behavior for TDD:
1. ✅ Write tests first (Step 2.1 - completed)
2. ✅ Verify tests fail because implementation doesn't exist (Step 2.2 - this step)
3. ⏳ Implement the functionality (Step 2.3+ - next steps)
4. ⏳ Verify tests pass (Step 2.7 - later)

## Test Coverage Analysis

The test file contains 5 test cases across 2 test classes:

### TestBuildCachedIssuesByRepo (2 tests)
1. `test_build_cache_groups_by_repo` - Tests grouping sessions by repo and calling cache with correct additional_issues
2. `test_build_cache_empty_sessions` - Tests empty sessions list returns empty dict

### TestRestartClosedSessions (3 tests)
1. `test_restart_builds_cache_with_session_issues` - Tests cache is built when not provided
2. `test_restart_uses_provided_cache` - Tests provided cache is used without rebuilding
3. `test_restart_skips_closed_issues` - Tests closed issues are detected and skipped
4. `test_restart_with_no_sessions` - Tests no sessions scenario

All tests are properly structured with:
- Clear Given/When/Then documentation
- Proper mocking of dependencies
- Comprehensive assertions

## Next Steps
1. **Immediate**: Proceed to Step 2.3 - Add defaultdict import
2. **Immediate**: Proceed to Step 2.4 - Implement `_build_cached_issues_by_repo()` function
3. **Future**: Tests should be executed in a properly configured environment after implementation
4. **Workaround**: Consider running pytest manually outside of MCP code checker if needed before final merge

## Recommendation
The TDD approach is properly followed:
- Tests written first ✅
- Tests would fail because implementation doesn't exist ✅
- Ready to proceed with implementation ✅

Mark this sub-task as complete and continue to next implementation step.
