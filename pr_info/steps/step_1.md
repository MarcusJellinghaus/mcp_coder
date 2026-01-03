# Step 1: Test Implementation for Cache Label Update

## LLM Prompt
```
Review the summary at pr_info/steps/summary.md for context on Issue #231 coordinator cache invalidation.

Implement comprehensive tests for the _update_issue_labels_in_cache() function that will update issue labels in cache after successful workflow dispatch. 

Follow TDD approach - write tests first before the actual implementation exists.

Focus on:
- Valid cache update scenarios (add/remove labels)
- Error handling (missing issue, invalid cache, file errors)
- Integration with existing cache structure
- Proper logging and metrics

Use existing test patterns from tests/utils/test_coordinator_cache.py as reference.
```

## WHERE: File Locations
- **Primary**: `tests/utils/test_coordinator_cache.py`
- **Reference**: `src/mcp_coder/cli/commands/coordinator.py` (for function signature)

## WHAT: Test Functions to Add

### Core Test Class
```python
class TestCacheIssueUpdate:
    """Tests for _update_issue_labels_in_cache function."""
    
    def test_update_issue_labels_success(self)
    def test_update_issue_labels_remove_only(self)
    def test_update_issue_labels_add_only(self)
    def test_update_issue_labels_missing_issue(self)
    def test_update_issue_labels_invalid_cache_structure(self)
    def test_update_issue_labels_file_permission_error(self)
    def test_update_issue_labels_logging(self)
```

### Integration Test Class
```python
class TestCacheUpdateIntegration:
    """Integration tests for cache update in dispatch workflow."""
    
    def test_dispatch_workflow_updates_cache(self)
    def test_multiple_dispatches_update_cache_correctly(self)
    def test_cache_update_failure_does_not_break_dispatch(self)
```

## HOW: Integration Points

### Test Dependencies
```python
from unittest.mock import Mock, patch
import pytest
import tempfile
from pathlib import Path

# Import function under test (will not exist yet - TDD)
from mcp_coder.cli.commands.coordinator import _update_issue_labels_in_cache
```

### Mock Objects
- `Mock` issue data with labels
- `tempfile.TemporaryDirectory` for cache file tests
- `patch` for file system operations and RepoIdentifier

## ALGORITHM: Test Logic Patterns

### Basic Update Test
```
1. Create sample cache with issue containing old labels
2. Call _update_issue_labels_in_cache(repo, issue_num, old_label, new_label)
3. Load updated cache from file
4. Assert old label removed and new label added
5. Verify other issue data unchanged
```

### Error Handling Test
```
1. Create problematic cache state (missing issue, bad structure, etc.)
2. Call _update_issue_labels_in_cache() 
3. Assert function handles error gracefully
4. Verify appropriate warning/debug messages logged
5. Assert main workflow would not be interrupted
```

## DATA: Test Data Structures

### Sample Cache Data
```python
{
    "last_checked": "2025-01-03T10:30:00Z",
    "issues": {
        "123": {
            "number": 123,
            "state": "open", 
            "labels": ["status-02:awaiting-planning", "bug"],
            "updated_at": "2025-01-03T09:00:00Z",
            # ... other issue fields
        },
        "456": {
            "number": 456,
            "state": "open",
            "labels": ["status-05:plan-ready", "enhancement"], 
            # ... other issue fields
        }
    }
}
```

### Expected Function Signature (TDD)
```python
def _update_issue_labels_in_cache(
    repo_full_name: str,
    issue_number: int, 
    old_label: str,
    new_label: str
) -> None:
    """Update issue labels in cache after successful dispatch.
    
    Args:
        repo_full_name: Repository in "owner/repo" format
        issue_number: GitHub issue number
        old_label: Label to remove from cache
        new_label: Label to add to cache
        
    Returns:
        None (updates cache file in-place)
    """
```

### Test Scenarios Coverage

#### Happy Path Tests
1. **Replace label**: Remove old label, add new label
2. **Add only**: New label not in cache, no old label to remove
3. **Remove only**: Old label exists, no new label to add (empty string)

#### Error Handling Tests  
1. **Missing issue**: Issue number not in cache
2. **Missing cache file**: Cache file doesn't exist
3. **Corrupted cache**: Invalid JSON structure
4. **File permissions**: Cannot write to cache file
5. **Repository parsing**: Invalid repo_full_name format

#### Integration Tests
1. **Full dispatch flow**: Mock dispatch_workflow + cache update
2. **Multiple issues**: Process several issues in sequence
3. **Cache persistence**: Verify updates persist across function calls

## Success Criteria

### Test Coverage
- All core functionality paths covered
- Error conditions properly tested
- Integration scenarios validated
- Logging behavior verified

### Test Quality
- Tests are isolated and independent
- Clear test names describing scenarios
- Proper use of fixtures and mocks
- Follows existing test patterns in codebase