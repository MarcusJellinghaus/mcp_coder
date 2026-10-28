# Testing Guide

## Quick Start

```bash
# All tests (unit + integration)
pytest

# Fast unit tests only
# See the marker filter in .claude/CLAUDE.md

# Run specific test types
pytest -m git_integration            # File system operations
pytest -m claude_cli_integration     # Claude CLI tests (requires CLI installed)

# Run specific subdirectories
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
```

**Default**: `pytest` runs ALL tests. Use marker filtering to run specific subsets.
