# Implementation Summary: CI Waiting and Fix Retry for check branch-status

## Overview
Add CI waiting and fix retry capabilities to `mcp-coder check branch-status` command to enable automated workflows that wait for CI completion and automatically retry fixes when CI fails.

## Architectural Changes

### Design Philosophy: KISS Principle
- **No new abstractions** - Keep polling logic inline (simple ~20 line loops)
- **No cross-module refactoring** - All changes isolated to command module
- **Self-contained implementation** - Everything in one file for clarity
- **Preserve existing code** - Zero changes to `CIResultsManager` or `implement` workflow

### Key Design Decisions

1. **Inline Polling Logic** (Not Extracted)
   - Rationale: ~15 lines of polling code - inline is clearer than abstraction
   - Benefit: No new manager methods, easier to understand and debug
   - Trade-off: Accept slight duplication vs. premature abstraction

2. **Simple Retry Loop** (Not Framework)
   - Rationale: Straightforward for-loop with CI recheck between attempts
   - Benefit: Readable, maintainable, follows command flow naturally
   - Trade-off: Command-specific vs. generic retry framework

3. **Exit Code Strategy**
   - 0: CI passed or no CI configured
   - 1: CI failed or timeout
   - 2: Technical errors (invalid arguments, Git errors, API errors)

4. **Progress Feedback**
   - Reuse existing `--llm-truncate` flag (no new parameter)
   - Human mode: Show dots during polling
   - LLM mode: Silent polling, clean output

## New Parameters

### `--ci-timeout SECONDS`
- **Type**: `int` (with validation: must be ≥ 0)
- **Default CLI**: `0` (no wait, current behavior)
- **Default Slash Command**: `180` (3 minutes, but configurable)
- **Behavior**: Wait up to N seconds for CI completion
  - `0`: Return immediately (backward compatible)
  - `> 0`: Poll every 15 seconds until completion or timeout
- **Validation**: Rejects negative values with clear error message

### `--fix [N]`
- **Type**: `int` (optional argument)
- **Default**: Not provided = `0` (no fix)
- **Values**:
  - Not provided or `--fix 0`: No fixing
  - `--fix` or `--fix 1`: Fix once, no recheck (current behavior preserved)
  - `--fix N` (N ≥ 2): Fix up to N times with CI recheck between attempts

## Files Modified

### Core Implementation
```
src/mcp_coder/cli/parsers.py
  - Modify add_check_parsers() to add --ci-timeout parameter with validation
  - Change --fix from boolean to optional integer

src/mcp_coder/cli/commands/check_branch_status.py
  - Add _wait_for_ci_completion() helper (~20 lines)
  - Add _show_progress() helper (~5 lines)
  - Enhance execute_check_branch_status() with wait logic (~15 lines)
  - Enhance _run_auto_fixes() with retry loop (~30 lines)
```

### Documentation
```
.claude/commands/check_branch_status.md
  - Update command to use --ci-timeout 180

docs/cli-reference.md
  - Document new parameters
  - Add usage examples
  - Document exit codes
```

### Tests
```
tests/cli/commands/test_check_branch_status.py
  - Add test_execute_with_ci_timeout_waits_for_completion()
  - Add test_execute_with_ci_timeout_exits_on_timeout()
  - Add test_execute_with_fix_retries_multiple_times()
  - Add test_execute_with_fix_waits_after_each_attempt()
  - Add test_progress_feedback_shown_in_human_mode()
  - Add test_progress_feedback_silent_in_llm_mode()
  - Add test_exit_codes_for_different_scenarios()
```

## Implementation Flow

### Without Fix (Read-Only with Wait)
```
1. Parse args (--ci-timeout 180)
2. Wait for CI completion (if timeout > 0)
   - Poll every 15 seconds
   - Show progress dots (unless --llm-truncate)
   - Early exit on completion or timeout
3. Collect and display branch status
4. Exit with code 0 (pass) or 1 (fail/timeout)
```

### With Fix and Retry
```
1. Parse args (--ci-timeout 180 --fix 3)
2. Wait for CI completion
3. Display status
4. If CI failed and --fix > 0:
   Early return if --fix 0 (no fix requested)
   For attempt in range(fix_count):
     a. Run fix (analysis + implementation)
     b. Commit and push
     c. If fix_count > 1 (retry enabled):
        - Wait for new CI run
        - Wait for CI completion
        - Check if passed → exit 0
     d. If last attempt and still failed → exit 1
5. Exit with appropriate code
```

## Data Structures (Unchanged)

All existing data structures from `CIResultsManager` and `BranchStatusReport` remain unchanged:
- `CIStatusData` - CI run and jobs information
- `JobData` - Individual job details
- `BranchStatusReport` - Complete branch status

## Integration Points

### Reused Components (No Changes Required)
- `CIResultsManager.get_latest_ci_status()` - Existing API
- `collect_branch_status()` - Existing function
- `check_and_fix_ci()` - Existing fix logic (called via `_run_auto_fixes`)
- `parse_llm_method_from_args()` - Existing utility

### New Internal Helpers (Private Functions)
- `_wait_for_ci_completion()` - Simple polling loop
- `_show_progress()` - Progress dot display

## Testing Strategy

### Test-Driven Development Approach
- Step 1: Write parser tests, then implement parser changes
- Step 2: Write command tests (waiting logic), then implement
- Step 3: Write command tests (retry logic), then implement
- Step 4: Integration tests for end-to-end scenarios

### Test Coverage Areas
- Parameter parsing (--ci-timeout, --fix with values)
- Polling behavior (timeout, early exit, API errors)
- Retry loop (multiple attempts, wait between)
- Progress feedback (human vs LLM mode)
- Exit codes (0, 1, 2 for different scenarios)
- Edge cases (no CI, already complete, perpetual pending)

## Backward Compatibility

✅ **Fully Preserved**
- Default `--ci-timeout 0` = no wait (current behavior)
- `--fix` without argument = fix once, no recheck (current behavior)
- All existing command usage continues to work identically
- No changes to existing functions or APIs

## Success Criteria

- ✅ Command waits for CI completion when `--ci-timeout > 0`
- ✅ Polling occurs every 15 seconds with early exit
- ✅ Progress feedback appropriate for human/LLM modes
- ✅ `--fix N` enables retry with N total attempts
- ✅ Always waits after each fix (including last) to know final status
- ✅ Exit codes reflect check result (0=pass, 1=fail, 2=error)
- ✅ Backward compatible (existing usage unchanged)
- ✅ All tests passing (>95% coverage for new code)
- ✅ Documentation complete and accurate

## Code Volume Estimate

- **Parser changes**: ~10 lines
- **Helper functions**: ~25 lines
- **Enhanced command logic**: ~45 lines
- **Test additions**: ~200 lines
- **Documentation**: ~50 lines
- **Total new code**: ~330 lines (80% tests/docs, 20% implementation)

## Risk Assessment

### Low Risk
- ✅ Isolated changes (one module)
- ✅ No refactoring of existing code
- ✅ Backward compatible by design
- ✅ Simple logic (loops and conditionals)

### Mitigation
- Comprehensive unit tests before implementation
- Test existing behavior remains unchanged
- Clear exit code strategy for error handling
