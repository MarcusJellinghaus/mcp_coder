# Step 4: Move and Update Test File

## LLM Prompt

```
Read pr_info/steps/summary.md for context.

Implement Step 4: Move the test file and update imports.

1. Move `tests/utils/test_coordinator_cache.py` to `tests/utils/github_operations/test_issue_cache.py`

2. Update all imports in the test file:
   - Change `from mcp_coder.cli.commands.coordinator import ...` 
   - To `from mcp_coder.utils.github_operations.issue_cache import ...`
   - Keep `_filter_eligible_issues` import from coordinator (it stays there)

3. Update all patch paths in tests:
   - Change `@patch("mcp_coder.cli.commands.coordinator._get_cache_file_path")`
   - To `@patch("mcp_coder.utils.github_operations.issue_cache._get_cache_file_path")`
   - (And similar for all other patched functions)

4. Update logger paths in caplog.set_level calls

5. Merge shared fixtures into `tests/utils/github_operations/conftest.py`:
   - sample_issue
   - sample_cache_data  
   - mock_issue_manager

6. **VERIFY tests pass BEFORE deleting original file**

7. Delete the original file `tests/utils/test_coordinator_cache.py` only after verification

The test logic should remain UNCHANGED - only imports and patch paths change.
```

## WHERE

**Create**: `tests/utils/github_operations/test_issue_cache.py`
**Modify**: `tests/utils/github_operations/conftest.py`
**Delete** (after verification): `tests/utils/test_coordinator_cache.py`

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
    get_all_cached_issues,
)
# _filter_eligible_issues stays in coordinator
from mcp_coder.cli.commands.coordinator import (
    _filter_eligible_issues,
    get_cached_eligible_issues,  # thin wrapper
)
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
# These stay in coordinator:
@patch("mcp_coder.cli.commands.coordinator._filter_eligible_issues")
@patch("mcp_coder.cli.commands.coordinator.get_eligible_issues")
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

### Fixtures to Merge into conftest.py

Add to `tests/utils/github_operations/conftest.py`:

```python
from mcp_coder.utils.github_operations.issue_cache import CacheData
from mcp_coder.utils.github_operations.issue_manager import IssueData

@pytest.fixture
def sample_issue() -> IssueData:
    """Sample issue data for testing."""
    return {
        "number": 123,
        "state": "open",
        "labels": ["status-02:awaiting-planning"],
        "updated_at": "2025-12-31T09:00:00Z",
        "url": "https://github.com/test/repo/issues/123",
        "title": "Test issue",
        "body": "Test issue body",
        "assignees": [],
        "user": "testuser",
        "created_at": "2025-12-31T08:00:00Z",
        "locked": False,
    }

@pytest.fixture
def sample_cache_data() -> CacheData:
    """Sample cache data structure."""
    return {
        "last_checked": "2025-12-31T10:30:00Z",
        "issues": {
            "123": {
                "number": 123,
                "state": "open",
                "labels": ["status-02:awaiting-planning"],
                "updated_at": "2025-12-31T09:00:00Z",
                "url": "https://github.com/test/repo/issues/123",
                "title": "Test issue",
                "body": "Test issue body",
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
            }
        },
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

Only imports, patch paths, and logger names change.

## ALGORITHM

```
# Test migration steps:
1. Copy test file to new location
2. Update imports at top of file
3. Find/replace all patch paths (coordinator → issue_cache for cache functions)
4. Update logger names in caplog.set_level calls
5. Move fixtures to conftest.py
6. Remove fixture definitions from test file
7. **RUN TESTS to verify they pass**
8. Only after verification: delete original file
```

## DATA

No data structure changes.

## TESTS

### Verification Before Deletion

```bash
# Run moved tests - must pass before deleting original
pytest tests/utils/github_operations/test_issue_cache.py -v

# Verify coordinator tests still work
pytest tests/cli/commands/coordinator/ -v
```

### After Verification Passes

```bash
# Delete original file
rm tests/utils/test_coordinator_cache.py

# Verify no tests remain in old location (should show "no tests collected")
pytest tests/utils/test_coordinator_cache.py -v 2>&1 | grep -E "(no tests|not found)"
```

## Troubleshooting

### If tests fail after moving:
- Check patch paths are updated correctly
- Verify logger names match new module path
- Ensure fixtures are accessible from conftest.py
- Check that `_filter_eligible_issues` patches still point to coordinator

### If imports fail:
- Verify Step 3 exports are complete
- Check both import paths work (github_operations and coordinator)
