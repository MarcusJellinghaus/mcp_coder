# Step 1: Write Tests for Simplified Repository Identifier Handling

## Overview
Following TDD principles, create comprehensive tests for the new simplified repository identifier handling before implementing changes.

## LLM Prompt
```
Implement test cases for the new _split_repo_identifier() function as specified in pr_info/steps/summary.md. 

Requirements:
1. Create TestSplitRepoIdentifier class with 2-3 simple test methods
2. Test basic "owner/repo" splitting
3. Test edge case: no slash in input
4. Add one test verifying no spurious warnings are logged when using "owner/repo" format
5. Delete obsolete TestParseRepoIdentifier class and test_get_cached_eligible_issues_url_parsing_fallback

Follow the test patterns in the existing codebase and use pytest fixtures for setup.
```

## WHERE: File Paths
- **Primary**: `tests/utils/test_coordinator_cache.py`
- **Helper**: Add test utilities if needed in existing test structure

## WHAT: Main Functions

### Test Class to Add
```python
class TestSplitRepoIdentifier:
    def test_split_basic_owner_repo()
    def test_split_raises_on_no_slash()
    def test_split_raises_on_multiple_slashes()
```

### Test Function to Add
```python
def test_no_spurious_warnings_with_owner_repo_format()
```

### Tests to Delete
- Entire `TestParseRepoIdentifier` class
- `test_get_cached_eligible_issues_url_parsing_fallback` method

### Tests to Update
- `TestCacheFilePath` class: Remove tests that use the `owner` parameter (now removed from function signature)

## HOW: Integration Points
- **Import**: `from mcp_coder.cli.commands.coordinator import _split_repo_identifier, get_cached_eligible_issues`
- **Mocking**: Mock `IssueManager` to avoid GitHub API calls
- **Logging**: Capture log output with `caplog` to verify no warnings
- **Fixtures**: Use existing coordinator test fixtures

## ALGORITHM: Core Test Logic
```python
# For TestSplitRepoIdentifier:
1. Call _split_repo_identifier() with valid input
2. Assert returned tuple matches expected (owner, repo_name)
3. For invalid input (no slash, multiple slashes), assert ValueError is raised

# For warning verification test:
1. Create mock IssueManager with repo_url matching repo_full_name
2. Call get_cached_eligible_issues("owner/repo", ...)
3. Capture log output with caplog
4. Assert no "Using fallback cache naming" warnings in log
```

## DATA: Expected Test Outcomes

### Return Values for _split_repo_identifier()
```python
_split_repo_identifier("owner/repo") -> ("owner", "repo")
_split_repo_identifier("just-repo") -> raises ValueError
_split_repo_identifier("owner/repo/extra") -> raises ValueError
```

### Test Assertions
```python
# Basic split
assert _split_repo_identifier("owner/repo") == ("owner", "repo")

# No slash - raises exception
with pytest.raises(ValueError):
    _split_repo_identifier("just-repo")

# Multiple slashes - raises exception
with pytest.raises(ValueError):
    _split_repo_identifier("owner/repo/extra")

# No spurious warnings
assert "Using fallback cache naming" not in caplog.text
```

## Implementation Notes
- **Mock Strategy**: Mock GitHub API calls to focus on identifier parsing logic
- **Log Capture**: Use `caplog` fixture to verify warning elimination
- **Simplicity**: Keep tests focused and minimal — avoid over-testing simple string operations
- **Cleanup**: Remove obsolete tests that reference deleted `_parse_repo_identifier()` function