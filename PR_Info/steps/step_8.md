# Step 8: Integration Testing and Documentation

## Objective
Create comprehensive integration tests and update documentation to cover the new CLI functionality.

## LLM Prompt
```
Based on the MCP Coder CLI Implementation Summary and all previous steps, implement Step 8: Create integration tests and documentation.

Requirements:
- Create integration tests that test the complete CLI workflow
- Test CLI commands in real git repositories
- Update README.md with CLI usage examples
- Create CLI-specific documentation
- Test error scenarios and edge cases
- Follow existing testing patterns and documentation style

Focus on end-to-end testing and clear user documentation.
```

## WHERE (File Structure)
```
tests/integration/
├── __init__.py (new)
├── test_cli_integration.py (new)
└── test_cli_workflows.py (new)

README.md (updated)
docs/cli_usage.md (new)
```

## WHAT (Tests & Documentation)

### `tests/integration/test_cli_integration.py`
```python
def test_cli_help_command_integration():
    """Test CLI help command in real environment."""

def test_cli_commit_auto_integration(temp_git_repo):
    """Test complete commit auto workflow in real git repo."""

def test_cli_commit_clipboard_integration(temp_git_repo, mock_clipboard):
    """Test complete commit clipboard workflow in real git repo."""

def test_cli_error_handling_non_git_directory():
    """Test CLI error handling outside git repositories."""
```

### `tests/integration/test_cli_workflows.py`
```python
def test_full_development_workflow(temp_git_repo):
    """Test complete development workflow with multiple commits."""

def test_cli_with_different_change_types(temp_git_repo):
    """Test CLI with various types of git changes."""

def test_cli_edge_cases_and_error_recovery(temp_git_repo):
    """Test CLI behavior in edge cases and error scenarios."""
```

### `docs/cli_usage.md`
```markdown
# MCP Coder CLI Usage Guide

## Installation
## Commands Overview  
## Usage Examples
## Troubleshooting
```

### `README.md` (additions)
```markdown
## CLI Usage
Brief overview and examples of CLI commands
```

## HOW (Integration Points)

### Test Infrastructure
```python
import subprocess
import tempfile
import git
from pathlib import Path
import pytest

@pytest.fixture
def temp_git_repo():
    """Create temporary git repository for testing."""
```

### Real CLI Execution
```python
def run_cli_command(args: list[str], cwd: Path = None) -> subprocess.CompletedProcess:
    """Run mcp-coder CLI command and return result."""
    return subprocess.run(
        ["mcp-coder"] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
```

## ALGORITHM (Integration Test Logic)
```
1. Create temporary git repository with test changes
2. Execute CLI commands via subprocess (real entry point)
3. Verify git repository state changes correctly
4. Check CLI output and exit codes
5. Test error scenarios with invalid inputs
6. Cleanup test repositories
```

## DATA (Test Scenarios)

### Successful Workflows
```python
# Test data for successful scenarios
test_scenarios = [
    {
        "description": "Single file modification",
        "files": {"test.py": "print('hello')"},
        "expected_commit_pattern": r"^(feat|fix|chore).*test\.py"
    },
    {
        "description": "Multiple file changes", 
        "files": {"src/main.py": "...", "tests/test_main.py": "..."},
        "expected_commit_pattern": r"^(feat|fix).*"
    }
]
```

### Error Scenarios
```python
error_scenarios = [
    {
        "description": "Non-git directory",
        "setup": lambda: Path("/tmp/not-git"),
        "expected_exit_code": 1,
        "expected_error": "Not a git repository"
    },
    {
        "description": "No changes to commit",
        "setup": lambda: create_clean_git_repo(),
        "expected_exit_code": 1,
        "expected_error": "No changes"
    }
]
```

## Tests Required

### Integration Test Categories

#### 1. **Command Execution Tests**
```python
def test_help_command_shows_usage():
    """Test help command displays correct usage information."""

def test_commit_auto_with_real_llm(mock_llm_response):
    """Test commit auto with mocked LLM response."""

def test_commit_clipboard_with_valid_message():
    """Test commit clipboard with valid clipboard content."""
```

#### 2. **Git Repository Tests**
```python
def test_cli_creates_valid_commits():
    """Test that CLI creates properly formatted git commits."""

def test_cli_stages_changes_correctly():
    """Test that CLI stages all changes before committing."""

def test_cli_handles_untracked_files():
    """Test CLI behavior with untracked files."""
```

#### 3. **Error Handling Tests**
```python
def test_cli_graceful_error_handling():
    """Test CLI provides helpful error messages."""

def test_cli_exit_codes_correct():
    """Test CLI returns appropriate exit codes."""

def test_cli_recovers_from_failures():
    """Test CLI handles and recovers from various failures."""
```

#### 4. **End-to-End Workflow Tests**
```python
def test_typical_development_workflow():
    """Test typical development workflow: modify files → commit auto → verify."""

def test_emergency_commit_workflow():
    """Test quick commit workflow: copy message → commit clipboard → verify."""
```

## Documentation Requirements

### CLI Usage Documentation
```markdown
# MCP Coder CLI Usage

## Quick Start
```bash
# Auto-generate commit message
mcp-coder commit auto

# Use clipboard commit message  
mcp-coder commit clipboard

# Show help
mcp-coder help
```

## Commands

### commit auto
Analyzes your git changes and generates an appropriate commit message using AI.

### commit clipboard  
Uses the commit message from your clipboard to create a commit.

## Examples
[Real-world usage examples]

## Troubleshooting
[Common issues and solutions]
```

### README.md Updates
```markdown
## Installation

```bash
pip install -e .
```

After installation, the `mcp-coder` CLI will be available:

```bash
# Auto-generate commit messages
mcp-coder commit auto

# Use clipboard commit message
mcp-coder commit clipboard
```

## CLI Features
- AI-powered commit message generation
- Clipboard-based commit workflow
- Comprehensive git repository validation
- Clear error messages and help
```

## Performance Testing

### CLI Startup Time
```python
def test_cli_startup_performance():
    """Test CLI startup time is reasonable."""
    import time
    start = time.time()
    result = run_cli_command(["help"])
    duration = time.time() - start
    assert duration < 2.0  # CLI should start quickly
```

### Git Operations Performance
```python
def test_large_repository_performance(large_git_repo):
    """Test CLI performance with large repositories."""
    # Test with repos containing many files
    # Ensure reasonable performance
```

## Mocking Strategy

### LLM Mocking
```python
@pytest.fixture
def mock_llm_success():
    """Mock successful LLM response."""
    with patch('mcp_coder.llm_interface.ask_llm') as mock:
        mock.return_value = "feat: add user authentication\n\nImplements login functionality."
        yield mock
```

### Clipboard Mocking
```python
@pytest.fixture  
def mock_clipboard_valid():
    """Mock valid clipboard content."""
    with patch('mcp_coder.utils.clipboard.get_clipboard_text') as mock:
        mock.return_value = (True, "fix: resolve validation bug", None)
        yield mock
```

## Acceptance Criteria
1. ✅ Comprehensive integration tests cover all CLI workflows
2. ✅ Tests use real git repositories and CLI entry points  
3. ✅ Error scenarios thoroughly tested with expected behaviors
4. ✅ CLI documentation provides clear usage examples
5. ✅ README.md updated with CLI installation and usage
6. ✅ Performance tests ensure reasonable CLI response times
7. ✅ All integration tests pass consistently
8. ✅ Documentation includes troubleshooting section
