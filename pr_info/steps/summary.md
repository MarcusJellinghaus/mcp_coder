# Issue #479: Fix CI Log Display in check_branch_status

## Problem Summary
The `check_branch_status` command shows "(logs not available)" instead of displaying actual CI failure logs, even though the logs exist on GitHub.

## Root Cause
**Filename format mismatch** in log retrieval logic:
- **Code expects**: `{job_name}/{step_number}_{step_name}.txt`
- **GitHub provides**: `{global_execution_number}_{job_name}.txt`
- The step number from GitHub API doesn't match the global execution number in filenames

## Solution Overview
Apply KISS principle with minimal changes to fix log retrieval and add GitHub URLs for navigation.

## Architectural Changes

### Design Changes
1. **Pattern-based log matching** - Replace exact filename matching with simple pattern search
2. **Inline implementation** - No new helper functions, keep logic where it's used
3. **GitHub URL integration** - Add run and job URLs for user navigation
4. **Graceful fallback** - Preserve existing logic as fallback, improve error messages

### No New Components
- No new functions or classes
- No new modules or files
- Changes confined to existing `_build_ci_error_details()` function

## Files Modified

### Source Code
- `src/mcp_coder/checks/branch_status.py`
  - Function: `_build_ci_error_details()` (lines ~430-500)
  - Changes: ~20 lines modified
  - Add: Pattern-based log file search
  - Add: GitHub URL extraction and display
  - Update: Error message when logs unavailable

### Tests
- `tests/checks/test_branch_status.py`
  - Update: Existing test mocks to use real GitHub format
  - Add: Test for GitHub URL display
  - Add: Test for improved error message
  - Changes: ~15 lines modified in existing tests

## Files Created
None - all changes to existing files

## Key Implementation Details

### 1. Log File Pattern Matching
```
FOR each log filename in logs:
    IF filename ends with "_{job_name}.txt":
        RETURN log content
        
IF not found:
    TRY old format as fallback
```

### 2. GitHub URL Display
```
Extract run_url from run_data
Display at top: "GitHub Actions: {run_url}"
For each job:
    Display: "View job: {run_url}/job/{job_id}"
```

### 3. Enhanced Error Message
```
IF no log content found:
    IF GitHub URL available:
        Display: "(logs not available locally)\nView on GitHub: {url}"
    ELSE:
        Display: "(logs not available)"
```

## Implementation Approach
- **Test-Driven Development**: Update tests first, then implementation
- **Minimal Changes**: Only modify what's necessary
- **Backward Compatible**: Preserve fallback to old format
- **Self-Documenting**: Add comments explaining the "why"

## Success Criteria
- ✅ CI failure logs display correctly
- ✅ Logs matched using `*_{job_name}.txt` pattern
- ✅ Fallback pattern attempted if primary fails
- ✅ GitHub Actions run URL shown at top
- ✅ Individual job URLs shown below job names
- ✅ Clean error message with GitHub URL when logs unavailable
- ✅ All existing tests pass
- ✅ New tests cover pattern matching and URL generation

## Risk Assessment
**Low Risk**
- Changes isolated to error display logic
- Backward-compatible fallback preserved
- No impact on CI execution or git operations
- Only ~35 total lines changed across 2 files
