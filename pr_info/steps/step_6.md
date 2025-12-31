# Step 6: Add Type Stubs and Request Timeout

## LLM Prompt
```
I'm implementing issue #213 - CI Pipeline Result Analysis Tool. Please refer to pr_info/steps/summary.md for the full architectural overview.

This is a code review follow-up step. Implement:
1. Add `types-requests` to dev dependencies in pyproject.toml
2. Remove the `# type: ignore` comment from the requests import
3. Add a configurable timeout constant for HTTP requests
4. Update `_download_and_extract_zip` to use the timeout

Follow Decision 24 and Decision 25 from pr_info/steps/Decisions.md.
```

## WHERE: File Locations
```
pyproject.toml                                              # Add types-requests
src/mcp_coder/utils/github_operations/ci_results_manager.py # Update imports and add timeout
```

## WHAT: Main Changes

### Add Dev Dependency
```toml
[project.optional-dependencies]
dev = [
    # ... existing deps
    "types-requests>=2.28.0",
]
```

### Add Class Constant
```python
class CIResultsManager(BaseGitHubManager):
    """Manages GitHub CI pipeline results using the GitHub API."""
    
    DEFAULT_REQUEST_TIMEOUT: int = 60  # seconds
```

### Update Import
```python
# Before
import requests  # type: ignore

# After
import requests
```

### Update HTTP Request
```python
# Before
response = requests.get(url, headers=headers, allow_redirects=True)

# After
response = requests.get(url, headers=headers, allow_redirects=True, timeout=self.DEFAULT_REQUEST_TIMEOUT)
```

## HOW: Integration Points

### pyproject.toml Changes
- Add `types-requests>=2.28.0` to `[project.optional-dependencies] dev` section

### ci_results_manager.py Changes
- Remove `# type: ignore` from requests import (line 13)
- Add `DEFAULT_REQUEST_TIMEOUT: int = 60` as class attribute
- Update `_download_and_extract_zip` method to use timeout

## ALGORITHM: Core Logic

```python
# 1. Define timeout as class constant
DEFAULT_REQUEST_TIMEOUT = 60

# 2. Use timeout in HTTP request
response = requests.get(
    url, 
    headers=headers, 
    allow_redirects=True,
    timeout=self.DEFAULT_REQUEST_TIMEOUT
)
```

## DATA: No data structure changes

This step only modifies configuration and adds a safety timeout.

## Success Criteria
- [ ] `types-requests` added to dev dependencies
- [ ] `# type: ignore` removed from requests import
- [ ] `DEFAULT_REQUEST_TIMEOUT` class constant added
- [ ] `_download_and_extract_zip` uses timeout parameter
- [ ] All existing tests still pass
- [ ] mypy passes without requests-related warnings
