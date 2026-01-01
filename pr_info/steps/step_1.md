# Step 1: Write Tests for `RepoIdentifier` Class

## Overview
Following TDD principles, create comprehensive tests for the new `RepoIdentifier` class before implementing it.

## LLM Prompt
```
Implement test cases for the new RepoIdentifier class as specified in pr_info/steps/summary.md. 

Requirements:
1. Create tests in a new file: tests/utils/github_operations/test_repo_identifier.py
2. Test from_full_name(): valid input, no slash, multiple slashes, empty owner, empty repo
3. Test from_repo_url(): HTTPS URLs, SSH URLs, invalid URLs
4. Test properties: full_name, cache_safe_name
5. All invalid inputs should raise ValueError

Follow the test patterns in the existing codebase and use pytest fixtures for setup.
```

## WHERE: File Paths
- **New file**: `tests/utils/github_operations/test_repo_identifier.py`

## WHAT: Test Classes

### TestRepoIdentifierFromFullName (3 unit tests)
```python
class TestRepoIdentifierFromFullName:
    def test_valid_owner_repo(self):
        """Test parsing valid 'owner/repo' format."""
        
    def test_raises_on_no_slash(self):
        """Test ValueError for input without slash."""
        
    def test_raises_on_multiple_slashes(self):
        """Test ValueError for input with multiple slashes."""
        
    def test_raises_on_empty_owner(self):
        """Test ValueError for '/repo' input."""
        
    def test_raises_on_empty_repo(self):
        """Test ValueError for 'owner/' input."""
```

### TestRepoIdentifierFromRepoUrl
```python
class TestRepoIdentifierFromRepoUrl:
    def test_https_url(self):
        """Test parsing HTTPS GitHub URLs."""
        
    def test_https_url_with_git_suffix(self):
        """Test parsing HTTPS URLs with .git suffix."""
        
    def test_ssh_url(self):
        """Test parsing SSH GitHub URLs."""
        
    def test_ssh_url_with_git_suffix(self):
        """Test parsing SSH URLs with .git suffix."""
        
    def test_raises_on_invalid_url(self):
        """Test ValueError for non-GitHub URLs."""
        
    def test_raises_on_non_string(self):
        """Test ValueError for non-string input."""
```

### TestRepoIdentifierProperties
```python
class TestRepoIdentifierProperties:
    def test_full_name_property(self):
        """Test full_name returns 'owner/repo' format."""
        
    def test_cache_safe_name_property(self):
        """Test cache_safe_name returns 'owner_repo' format."""
        
    def test_str_returns_full_name(self):
        """Test __str__ returns full_name format."""
```

## HOW: Integration Points
- **Import**: `from mcp_coder.utils.github_operations.github_utils import RepoIdentifier`
- **Fixtures**: None required — class is self-contained

## ALGORITHM: Core Test Logic
```python
# For from_full_name():
1. Call RepoIdentifier.from_full_name("owner/repo")
2. Assert result.owner == "owner" and result.repo_name == "repo"
3. For invalid input, assert ValueError is raised with descriptive message

# For from_repo_url():
1. Call RepoIdentifier.from_repo_url("https://github.com/owner/repo")
2. Assert result.owner == "owner" and result.repo_name == "repo"
3. For invalid URLs, assert ValueError is raised

# For properties:
1. Create RepoIdentifier(owner="owner", repo_name="repo")
2. Assert full_name == "owner/repo"
3. Assert cache_safe_name == "owner_repo"
```

## DATA: Expected Test Outcomes

### from_full_name() Return Values
```python
RepoIdentifier.from_full_name("owner/repo") -> RepoIdentifier(owner="owner", repo_name="repo")
RepoIdentifier.from_full_name("just-repo") -> raises ValueError
RepoIdentifier.from_full_name("a/b/c") -> raises ValueError
RepoIdentifier.from_full_name("/repo") -> raises ValueError
RepoIdentifier.from_full_name("owner/") -> raises ValueError
```

### from_repo_url() Return Values
```python
RepoIdentifier.from_repo_url("https://github.com/owner/repo") -> RepoIdentifier(owner="owner", repo_name="repo")
RepoIdentifier.from_repo_url("https://github.com/owner/repo.git") -> RepoIdentifier(owner="owner", repo_name="repo")
RepoIdentifier.from_repo_url("git@github.com:owner/repo") -> RepoIdentifier(owner="owner", repo_name="repo")
RepoIdentifier.from_repo_url("git@github.com:owner/repo.git") -> RepoIdentifier(owner="owner", repo_name="repo")
RepoIdentifier.from_repo_url("https://gitlab.com/owner/repo") -> raises ValueError
RepoIdentifier.from_repo_url("invalid") -> raises ValueError
```

### Property Values
```python
repo = RepoIdentifier(owner="MarcusJellinghaus", repo_name="mcp_coder")
repo.full_name -> "MarcusJellinghaus/mcp_coder"
repo.cache_safe_name -> "MarcusJellinghaus_mcp_coder"
str(repo) -> "MarcusJellinghaus/mcp_coder"
```

## Implementation Notes
- **Test Count**: 3 unit tests for `from_full_name` + tests for `from_repo_url` + property tests
- **Error Messages**: Verify ValueError messages are descriptive
- **Edge Cases**: Test with dashes, underscores, numbers in owner/repo names
