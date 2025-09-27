# Testing Guide

## Quick Start

```bash
# All tests (unit + integration)
pytest

# Fast unit tests only
pytest -m "not git_integration and not claude_integration and not github_integration"

# Run specific test types
pytest -m git_integration      # File system operations
pytest -m claude_integration   # Claude API (requires auth)
pytest -m github_integration   # GitHub API (requires config)
```

## Test Markers

| Marker | Purpose | Speed | Requirements |
|--------|---------|-------|--------------|
| *(none)* | Unit tests | < 10s | None |
| `git_integration` | File system + git ops | < 60s | Git |
| `claude_integration` | Claude CLI/API calls | Variable | Auth setup |
| `github_integration` | GitHub API operations | < 30s | GitHub config |

## Marking Tests

```python
# Unit test (no marker needed)
def test_validation():
    pass

@pytest.mark.git_integration  
def test_git_workflow(git_repo):
    pass

@pytest.mark.claude_integration
def test_claude_api():
    pass
```

**Default**: `pytest` runs ALL tests. Use marker filtering to run specific subsets.
