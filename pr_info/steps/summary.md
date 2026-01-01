# Repository Identifier Cleanup - Implementation Summary

## Problem Statement
The coordinator produces spurious warnings during normal operation due to confused repository identifier handling:
```
WARNING - Using fallback cache naming for MarcusJellinghaus/mcp_coder: owner could not be determined from URL MarcusJellinghaus/mcp_coder
```

## Root Cause Analysis
1. `execute_coordinator_run()` correctly extracts `repo_full_name = "MarcusJellinghaus/mcp_coder"`
2. `get_cached_eligible_issues()` receives this already-parsed format
3. Function incorrectly tries to re-parse it as a URL via `_parse_repo_identifier()`
4. Parser fails because "owner/repo" format doesn't match URL patterns → spurious warning

## Architectural Changes

### Design Principles
- **KISS Principle**: Replace complex URL parsing with simple string operations
- **Single Responsibility**: Parse once at entry point, use consistently downstream
- **Testability**: Extract logic to small testable function

### Changes Overview
1. **Add Simple Function**: New `_split_repo_identifier()` function with validation (exactly one slash required)
2. **Remove Redundant Code**: Delete `_parse_repo_identifier()` function entirely
3. **Simplify `_get_cache_file_path()`**: Remove unused `owner` parameter and fallback branches
4. **Simplify Error Handling**: Exception handler uses `repo_full_name` directly
5. **Clarify Contracts**: Update docstrings to specify expected data formats (module docstring + function docstrings)

### Data Flow (After Changes)
```
execute_coordinator_run() → repo_full_name: "owner/repo"
                         ↓
get_cached_eligible_issues() → _split_repo_identifier(repo_full_name)
                             ↓ returns (owner, repo_name)
_get_cache_file_path(repo_full_name) → "owner_repo.issues.json"
```

## Files Modified

### Core Implementation
- **Modified**: `src/mcp_coder/cli/commands/coordinator.py`
  - Add: `_split_repo_identifier()` function with validation
  - Remove: `_parse_repo_identifier()` function
  - Simplify: `_get_cache_file_path()` — remove `owner` parameter and fallback branches
  - Modify: `get_cached_eligible_issues()` to use new function
  - Simplify: Exception handler to use `repo_full_name` directly
  - Update: Module and function docstrings (terminology table in both places)

### Test Coverage
- **Modified**: `tests/utils/test_coordinator_cache.py`
  - Add: `TestSplitRepoIdentifier` class with tests for valid input and exception cases
  - Add: Test verifying no spurious warnings
  - Delete: `TestParseRepoIdentifier` class (tests removed function)
  - Delete: `test_get_cached_eligible_issues_url_parsing_fallback`
  - Update: `TestCacheFilePath` tests to remove `owner` parameter usage

## Benefits

### Immediate
- ✅ Eliminates spurious warnings during normal operation
- ✅ Maintains correct cache file naming: `{owner}_{repo}.issues.json`
- ✅ Reduces code complexity and maintenance burden

### Long-term
- ✅ Clear separation of concerns (URL parsing vs string splitting)
- ✅ Better error messages and debugging experience
- ✅ Foundation for future repository handling improvements

## Risk Assessment
- **Low Risk**: Changes are minimal and localized
- **Backward Compatible**: No API changes, existing cache files continue to work
- **Test Coverage**: Existing tests verify cache functionality still works