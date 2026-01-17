# Step 4: Move and Update Test File

## LLM Prompt

```
Read pr_info/steps/summary.md for context.

Implement Step 4: Move the test file and update imports.

1. Move `tests/utils/test_coordinator_cache.py` to `tests/utils/github_operations/test_issue_cache.py`

2. Update all imports in the test file:
   - Change `from mcp_coder.cli.commands.coordinator import ...` 
   - To `from mcp_coder.utils.github_operations.issue_cache import ...`

3. Update all patch paths in tests:
   - Change `@patch("mcp_coder.cli.commands.coordinator._get_cache_file_path")`
   - To `@patch("mcp_coder.utils.github_operations.issue_cache._get_cache_file_path")`
   - (And similar for all other patched functions)

4. Move shared fixtures to `tests/utils/github_operations/conftest.py`:
   - sample_issue
   - sample_cache_data  
   - mock_issue_manager

5. Delete the original file `tests/utils/test_coordinator_cache.py`

The test logic should remain UNCHANGED - only imports and patch paths change.
```

## WHERE

**Create**: `tests/utils/github_operations/test_issue_cache.py`
**Modify**: `tests/utils/github_operations/conftest.py`
**Delete**: `tests/utils/test_coordinator_cache.py`

## WHAT

### Import Changes

**Before**:
```python
from mcp_coder.cli.commands.coordinator import (
    CacheData,
    _filter_eligible_issues,
    _get_cache_file_path,
    _load_cache_file,
    _log_cache_metrics,
    _log_stale_cache_entries,
    _save_cache_file,
    _update_issue_labels_in_cache,
    get_cached_eligible_issues,
)
```

**After**:
```python
from mcp_coder.utils.github_operations.issue_cache import (
    CacheData,
    _get_cache_file_path,
    _load_cache_file,
    _log_cache_metrics,
    _log_stale_cache_entries,
    _save_cache_file,
    _update_issue_labels_in_cache,
    get_cached_eligible_issues,
)
# _filter_eligible_issues stays in coordinator
from mcp_coder.cli.commands.coordinator import _filter_eligible_issues
```

### Patch Path Changes

**Before**:
```python
@patch("mcp_coder.cli.commands.coordinator._get_cache_file_path")
@patch("mcp_coder.cli.commands.coordinator._load_cache_file")
@patch("mcp_coder.cli.commands.coordinator._save_cache_file")
@patch("mcp_coder.cli.commands.coordinator._filter_eligible_issues")
@patch("mcp_coder.cli.commands.coordinator.get_eligible_issues")
```

**After**:
```python
@patch("mcp_coder.utils.github_operations.issue_cache._get_cache_file_path")
@patch("mcp_coder.utils.github_operations.issue_cache._load_cache_file")
@patch("mcp_coder.utils.github_operations.issue_cache._save_cache_file")
# _filter_eligible_issues is passed as callback, may need different patching strategy
# get_eligible_issues is passed as callback
```

### Logger Path Changes

**Before**:
```python
caplog.set_level(logging.DEBUG, logger="mcp_coder.cli.commands.coordinator.core")
```

**After**:
```python
caplog.set_level(logging.DEBUG, logger="mcp_coder.utils.github_operations.issue_cache")
```

### Fixtures to Move to conftest.py

```python
@pytest.fixture
def sample_issue() -> IssueData:
    """Sample issue data for testing."""
    return {
        "number": 123,
        "state": "open",
        "labels": ["status-02:awaiting-planning"],
        # ... rest of fixture
    }

@pytest.fixture
def sample_cache_data() -> CacheData:
    """Sample cache data structure."""
    return {
        "last_checked": "2025-12-31T10:30:00Z",
        "issues": { ... }
    }

@pytest.fixture
def mock_issue_manager() -> Mock:
    """Mock IssueManager for testing."""
    manager = Mock()
    manager.list_issues.return_value = []
    return manager
```

## HOW

The test file structure remains the same:
- `TestCacheMetricsLogging`
- `TestCacheFilePath`
- `TestCacheFileOperations`
- `TestStalenessLogging`
- `TestEligibleIssuesFiltering`
- `TestGetCachedEligibleIssues`
- `TestCacheIssueUpdate`
- `TestCacheUpdateIntegration`

Only imports and patch paths change.

## ALGORITHM

```
# Test migration steps:
1. Copy test file to new location
2. Update imports at top of file
3. Find/replace all patch paths (coordinator → issue_cache)
4. Update logger names in caplog.set_level calls
5. Move fixtures to conftest.py
6. Run tests to verify
7. Delete original file
```

## DATA

No data structure changes.

## TESTS

Run the moved tests:
```bash
pytest tests/utils/github_operations/test_issue_cache.py -v
```

Verify no tests remain in old location:
```bash
# Should fail or show no tests
pytest tests/utils/test_coordinator_cache.py -v
```
