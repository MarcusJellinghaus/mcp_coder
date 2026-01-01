# Step 4: Update Tests and Documentation

## Overview
Update existing tests to use `RepoIdentifier`, delete obsolete tests, and add integration test for warning verification.

## LLM Prompt
```
Update tests and documentation as specified in pr_info/steps/summary.md.

Requirements:
1. Update tests/utils/test_coordinator_cache.py:
   - Delete TestParseRepoIdentifier class
   - Delete test_get_cached_eligible_issues_url_parsing_fallback
   - Update TestCacheFilePath to use RepoIdentifier
   - Add test_no_spurious_warnings_with_owner_repo_format integration test
2. Update module docstring in coordinator.py with RepoIdentifier documentation
3. Run all tests to verify no regressions

Focus on removing obsolete tests and ensuring new behavior is covered.
```

## WHERE: File Paths
- **Primary**: `tests/utils/test_coordinator_cache.py`
- **Secondary**: `src/mcp_coder/cli/commands/coordinator.py` (module docstring)

## WHAT: Test Changes

### Tests to Delete
```python
# Delete entire class
class TestParseRepoIdentifier:
    ...

# Delete this test method from TestGetCachedEligibleIssues
def test_get_cached_eligible_issues_url_parsing_fallback(self, ...):
    ...
```

### Tests to Update: `TestCacheFilePath`

**BEFORE:**
```python
class TestCacheFilePath:
    def test_get_cache_file_path_basic(self) -> None:
        repo_name = "owner/repo"
        path = _get_cache_file_path(repo_name)
        ...

    def test_get_cache_file_path_with_owner_none(self) -> None:
        ...

    def test_get_cache_file_path_with_owner_provided(self) -> None:
        ...
```

**AFTER:**
```python
class TestCacheFilePath:
    def test_get_cache_file_path_basic(self) -> None:
        repo_identifier = RepoIdentifier(owner="owner", repo_name="repo")
        path = _get_cache_file_path(repo_identifier)
        
        expected_dir = Path.home() / ".mcp_coder" / "coordinator_cache"
        expected_file = expected_dir / "owner_repo.issues.json"
        
        assert path == expected_file

    def test_get_cache_file_path_complex_names(self) -> None:
        test_cases = [
            (RepoIdentifier("anthropics", "claude-code"), "anthropics_claude-code.issues.json"),
            (RepoIdentifier("user", "repo-with-dashes"), "user_repo-with-dashes.issues.json"),
            (RepoIdentifier("org", "very.long.repo.name"), "org_very.long.repo.name.issues.json"),
        ]

        for repo_identifier, expected_filename in test_cases:
            path = _get_cache_file_path(repo_identifier)
            assert path.name == expected_filename
```

### Test to Add: Integration Test for No Spurious Warnings

```python
class TestNoSpuriousWarnings:
    def test_no_spurious_warnings_with_repo_identifier(
        self,
        mock_issue_manager: Mock,
        sample_issue: IssueData,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that no spurious warnings occur when using RepoIdentifier."""
        caplog.set_level(logging.WARNING, logger="mcp_coder.cli.commands.coordinator")
        mock_issue_manager.list_issues.return_value = [sample_issue]

        with (
            patch("mcp_coder.cli.commands.coordinator._get_cache_file_path") as mock_path,
            patch("mcp_coder.cli.commands.coordinator._load_cache_file") as mock_load,
            patch("mcp_coder.cli.commands.coordinator._save_cache_file") as mock_save,
            patch("mcp_coder.cli.commands.coordinator._filter_eligible_issues") as mock_filter,
        ):
            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {"last_checked": None, "issues": {}}
            mock_save.return_value = True
            mock_filter.return_value = [sample_issue]

            repo_identifier = RepoIdentifier(owner="owner", repo_name="repo")
            result = get_cached_eligible_issues(repo_identifier, mock_issue_manager)

            assert result == [sample_issue]
            # Verify NO spurious warnings about fallback cache naming
            assert "Using fallback cache naming" not in caplog.text
            assert "owner could not be determined" not in caplog.text
```

### Update Imports in Test File

```python
from mcp_coder.cli.commands.coordinator import (
    _filter_eligible_issues,
    _get_cache_file_path,
    _load_cache_file,
    _log_cache_metrics,
    _log_stale_cache_entries,
    _save_cache_file,
    get_cached_eligible_issues,
)
from mcp_coder.utils.github_operations.github_utils import RepoIdentifier
```

## HOW: Integration Points
- **Import**: Add `RepoIdentifier` import to test file
- **Remove**: Delete import of `_parse_repo_identifier` (no longer exists)
- **Update**: All test methods that use `_get_cache_file_path`

## ALGORITHM: Test Migration Steps
```
1. Add RepoIdentifier import to test file
2. Remove _parse_repo_identifier from imports
3. Delete TestParseRepoIdentifier class entirely
4. Delete test_get_cached_eligible_issues_url_parsing_fallback method
5. Update TestCacheFilePath tests to use RepoIdentifier
6. Add TestNoSpuriousWarnings class with integration test
7. Update any other tests that reference old function signatures
8. Run pytest to verify all tests pass
```

## Implementation Notes
- **Test Count**: Net reduction in test count (deleting obsolete tests, adding focused new tests)
- **Coverage**: Ensure the new integration test verifies the original bug is fixed
- **Cleanup**: Remove any fixtures or helper methods only used by deleted tests
