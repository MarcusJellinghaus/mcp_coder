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
- **Existing Utilities**: Leverage working code, remove redundant functions

### Changes Overview
1. **Simplify Parsing Logic**: Replace URL parsing attempt with direct string split
2. **Remove Redundant Code**: Delete `_parse_repo_identifier()` function entirely
3. **Clarify Contracts**: Update docstrings to specify expected data formats

### Data Flow (After Changes)
```
execute_coordinator_run() → repo_full_name: "owner/repo"
                         ↓
get_cached_eligible_issues() → owner, repo = repo_full_name.split("/", 1)
                             ↓
_get_cache_file_path() → "owner_repo.issues.json"
```

## Files Modified

### Core Implementation
- **Modified**: `src/mcp_coder/cli/commands/coordinator.py`
  - Remove: `_parse_repo_identifier()` function (lines ~408-445)
  - Modify: `get_cached_eligible_issues()` parsing logic (lines ~614-618)
  - Update: Function docstrings

### Test Coverage
- **Modified**: `tests/utils/test_coordinator_cache.py` (if exists)
- **Enhanced**: Test cases for cache file naming with various repo formats

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