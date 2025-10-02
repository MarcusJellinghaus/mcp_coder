# Testing Guide

## Quick Start

```bash
# All tests (unit + integration)
pytest

# Fast unit tests only
pytest -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"

# Run specific test types
pytest -m git_integration            # File system operations
pytest -m claude_cli_integration     # Claude CLI tests (requires CLI installed)
pytest -m claude_api_integration     # Claude API tests (requires auth)
pytest -m formatter_integration      # Code formatter tests (black, isort)
pytest -m github_integration         # GitHub API (requires config)

# Run specific subdirectories
pytest tests/utils/github_operations/    # All GitHub operations tests
pytest tests/utils/                      # All utils tests
```

## Test Structure

Tests mirror the source code structure:

```
tests/
├── cli/                    # CLI command tests
├── formatters/            # Code formatter tests
├── llm_providers/         # LLM provider tests
│   └── claude/           # Claude-specific tests
├── utils/                 # Utility tests
│   ├── github_operations/ # GitHub API tests
│   │   ├── test_github_utils.py
│   │   ├── test_issue_manager.py
│   │   └── test_issue_manager_integration.py
│   ├── test_clipboard.py
│   ├── test_data_files.py
│   └── test_git_*.py
├── workflows/             # Workflow tests
└── workflow_utils/        # Workflow utility tests
```

## Test Markers

| Marker | Purpose | Speed | Requirements |
|--------|---------|-------|--------------|
| *(none)* | Unit tests | < 10s | None |
| `git_integration` | File system + git ops | < 60s | Git |
| `claude_cli_integration` | Claude CLI calls | Variable | CLI installed |
| `claude_api_integration` | Claude API calls | Variable | Auth setup |
| `formatter_integration` | Code formatting | < 30s | black, isort |
| `github_integration` | GitHub API operations | < 30s | GitHub config |

## Marking Tests

```python
# Unit test (no marker needed)
def test_validation():
    pass

@pytest.mark.git_integration  
def test_git_workflow(git_repo):
    pass

@pytest.mark.claude_cli_integration
def test_claude_cli():
    pass

@pytest.mark.claude_api_integration
def test_claude_api():
    pass

@pytest.mark.formatter_integration
def test_formatter():
    pass

@pytest.mark.github_integration
def test_github_operations(issue_manager):
    pass
```

**Default**: `pytest` runs ALL tests. Use marker filtering to run specific subsets.
