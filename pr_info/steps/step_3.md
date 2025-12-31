# Step 3: Remove _parse_repo_identifier Function

## Overview
Remove the redundant `_parse_repo_identifier()` function that is no longer needed after Step 2's simplification.

## LLM Prompt
```
Remove the _parse_repo_identifier() function from coordinator.py as specified in pr_info/steps/summary.md.

Requirements:
1. Delete the entire _parse_repo_identifier() function (lines ~408-445)
2. Ensure no other code references this function
3. Run all tests to verify no regressions
4. Confirm the coordinator functionality works without this function

This cleanup removes redundant code that was causing spurious warnings.
```

## WHERE: File Paths
- **Primary**: `src/mcp_coder/cli/commands/coordinator.py`
- **Lines**: Approximately 408-445 (function definition and implementation)

## WHAT: Main Functions

### Function to Remove
```python
def _parse_repo_identifier(repo_url: str, repo_name: str) -> tuple[str, str | None]:
    """Parse repository URL to extract owner and repo name with fallback.
    
    Args:
        repo_url: Repository URL in various formats
        repo_name: Repository name for fallback
        
    Returns:
        Tuple of (repo_name, owner) where owner may be None if extraction fails
    """
    # Implementation spanning ~37 lines
    # Contains redundant regex patterns and warning logging
```

### Verification Steps
- Search for any remaining references to `_parse_repo_identifier`
- Check if any other functions call this removed function
- Verify imports/exports don't reference it

## HOW: Integration Points
- **No Dependencies**: Function should have no remaining callers after Step 2
- **No Imports**: Function is internal, no module exports to update
- **Error Handling**: Existing fallback logic in caller functions handles edge cases

## ALGORITHM: Cleanup Process
```python
# Removal process:
1. Locate _parse_repo_identifier function definition (~line 408)
2. Delete entire function including docstring and implementation
3. Search codebase for any remaining references
4. Run tests to verify no import/call errors
5. Confirm coordinator functionality still works
```

## DATA: Impact Assessment

### Before Removal
- **Function**: 37 lines of complex regex-based URL parsing
- **Warnings**: Source of "Using fallback cache naming..." messages
- **Complexity**: Redundant logic already handled by `parse_github_url()`

### After Removal
- **Lines Saved**: ~37 lines of code
- **Complexity**: Reduced maintenance burden
- **Warnings**: Eliminated spurious log messages

### Risk Mitigation
- **Step 2**: Already replaced all function calls
- **Tests**: Verify functionality preservation
- **Fallback**: Existing error handling in caller functions

## Implementation Notes

### Search Pattern
Use these commands to verify complete removal:
```bash
# Search for any remaining references
grep -r "_parse_repo_identifier" src/
grep -r "_parse_repo_identifier" tests/

# Should return no results after cleanup
```

### Validation
- **Unit Tests**: All existing tests should pass
- **Integration Tests**: Coordinator functionality should work normally
- **Log Output**: No "Using fallback cache naming" warnings

### Documentation Impact
- **Function**: Remove from any internal API documentation
- **Comments**: Remove any references in related functions