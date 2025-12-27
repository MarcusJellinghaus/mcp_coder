# Step 5: End-to-End Integration Testing

## Objective
Create comprehensive integration tests that verify the complete caching workflow from CLI invocation through cache file management.

## LLM Prompt
```
Based on the GitHub API caching implementation summary, implement Step 5: End-to-end integration testing.

Requirements:
- Create integration tests for the complete caching workflow
- Test CLI argument handling, cache file operations, and GitHub API integration
- Include scenarios: first run, incremental updates, force refresh, error handling
- Use mocking for GitHub API calls to ensure deterministic tests
- Follow existing testing patterns in the codebase

This completes the implementation. Refer to all previous steps and the summary document.
```

## WHERE
- **File**: `tests/cli/commands/test_coordinator.py` (extend existing)
- **New File**: `tests/utils/test_coordinator_cache_integration.py`
- **Test Fixtures**: Use existing `conftest.py` patterns

## WHAT
### Integration Test Functions
```python
def test_coordinator_caching_first_run_integration()
def test_coordinator_caching_incremental_update_integration() 
def test_coordinator_caching_duplicate_protection_integration()
def test_coordinator_caching_force_refresh_integration()
def test_coordinator_caching_cache_corruption_recovery()
def test_coordinator_caching_multiple_repos_integration()
```

### Mock Fixtures
```python
@pytest.fixture
def mock_github_issues_timeline()
@pytest.fixture  
def mock_cache_directory()
@pytest.fixture
def coordinator_config_with_cache()
```

## HOW
### Integration Points
- **CLI Testing**: Use existing coordinator CLI test patterns
- **Mocking**: Mock `IssueManager` GitHub API calls with `@patch`
- **File System**: Use `tmp_path` fixture for cache directory testing
- **Config Testing**: Mock configuration values for cache settings

### Test Structure
```python
def test_coordinator_caching_workflow(tmp_path, mock_github_api):
    # Setup: Create cache directory and mock responses
    # Execute: Run coordinator command with caching  
    # Verify: Check cache files, API call patterns, results
```

## ALGORITHM  
```
1. Setup test environment with temp cache directory and mocked GitHub API
2. Execute coordinator run command with various scenarios (first run, updates)
3. Verify cache file creation/updates with correct timestamps and data
4. Verify API calls match expected patterns (full vs incremental)
5. Verify duplicate protection behavior and force refresh override
6. Verify error recovery and fallback behavior
```

## DATA
### Test Scenarios
- **First Run**: No cache exists, creates cache with full fetch
- **Incremental Update**: Cache exists, uses `since` parameter for fetch
- **Duplicate Protection**: Recent cache triggers skip with INFO message
- **Force Refresh**: `--force-refresh` bypasses cache entirely
- **Cache Corruption**: Invalid JSON triggers recreation and full fetch
- **Permission Errors**: Cache write failures fall back gracefully

### Verification Points
- **Cache Files**: Correct JSON structure and timestamps
- **API Calls**: Appropriate GitHub API parameters used
- **CLI Output**: Expected logging messages appear
- **Error Handling**: Graceful fallback on failures
- **Performance**: Reduced API calls on subsequent runs

## Implementation Notes
- **Deterministic Tests**: Use fixed datetimes and predictable issue data
- **Isolated Tests**: Each test creates clean cache directory
- **Realistic Scenarios**: Test data matches actual GitHub API responses
- **Performance Validation**: Verify cache actually reduces API calls
- **Error Coverage**: Test all error paths have appropriate fallbacks
- **Integration Scope**: Test spans CLI → cache → GitHub API → results