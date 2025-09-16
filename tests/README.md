# Testing Guide

## Quick Start

```bash
# Fast unit tests (default)
pytest

# Exclude slow claude integration tests  
pytest -m "not claude_integration"

# Run specific test types
pytest -m git_integration      # File system operations
pytest -m claude_integration   # Claude API (requires auth)
```

## Test Markers

| Marker | Purpose | Speed | Requirements |
|--------|---------|-------|--------------|
| *(none)* | Unit tests | < 10s | None |
| `git_integration` | File system + git ops | < 60s | Git |
| `claude_integration` | Claude CLI/API calls | Variable | Auth setup |

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

**Default**: Run unmarked unit tests only. Mark tests only when external dependencies are needed.
