# Step 2: Update task_processing.py - Commit Message File Handling

## LLM Prompt

```
Implement Step 2 from pr_info/steps/summary.md.

Update task_processing.py to:
1. Add a constant for the commit message file path
2. Add defensive cleanup at start of process_single_task()
3. Modify commit_changes() to read and use the file if present

Follow TDD - write tests first, then implement. Read the step file for details.
```

## WHERE

**Files**:
- `src/mcp_coder/workflows/implement/task_processing.py`
- `tests/workflows/implement/test_task_processing.py`

## WHAT

### 2.1 Add Constant (task_processing.py)

```python
# Add after existing constants (around line 25)
COMMIT_MESSAGE_FILE = "pr_info/.commit_message.txt"
```

### 2.2 Add Import (task_processing.py)

```python
# Add to imports from commit_operations
from mcp_coder.workflow_utils.commit_operations import (
    generate_commit_message_with_llm,
    parse_llm_commit_response,  # NEW
)
```

### 2.3 Defensive Cleanup in process_single_task() (task_processing.py)

**Location**: After `env_vars = prepare_llm_environment(project_dir)` (around line 340)

```python
def _cleanup_commit_message_file(project_dir: Path) -> None:
    """Remove stale commit message file from previous failed runs."""
    commit_msg_path = project_dir / COMMIT_MESSAGE_FILE
    if commit_msg_path.exists():
        commit_msg_path.unlink()
        logger.debug("Cleaned up stale commit message file")
```

Call at start of `process_single_task()`:
```python
# Cleanup stale commit message file from previous failed runs
_cleanup_commit_message_file(project_dir)
```

### 2.4 Modify commit_changes() Function (task_processing.py)

**Signature**: No change to signature

**Algorithm** (pseudocode):
```
1. commit_msg_path = project_dir / COMMIT_MESSAGE_FILE
2. IF commit_msg_path.exists() AND file has content:
     a. Read file content
     b. Delete file (before git add)
     c. Parse using parse_llm_commit_response()
     d. commit_message = parsed result
     e. Log: "Using prepared commit message from file"
3. ELSE:
     a. Call generate_commit_message_with_llm() (existing behavior)
     b. commit_message = result
4. Proceed with commit using commit_message
5. IF commit fails:
     a. Log commit_message via logger.error() so it's not lost
```

## HOW

### Integration Points

1. Import `parse_llm_commit_response` from `commit_operations`
2. Call `_cleanup_commit_message_file()` at start of `process_single_task()`
3. Add file-reading logic at start of `commit_changes()` before existing LLM call

## DATA

**Input**: `pr_info/.commit_message.txt` (plain text, UTF-8)
**Output**: Commit message string (may include header + body separated by blank line)

## TESTS TO ADD (test_task_processing.py)

### New Test Class: TestCommitMessageFile

```python
class TestCommitMessageFile:
    """Test commit message file handling."""

    def test_cleanup_removes_existing_file(self, tmp_path: Path) -> None:
        """Test that cleanup removes existing commit message file."""
        # Create the file
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        commit_file = pr_info / ".commit_message.txt"
        commit_file.write_text("old message")
        
        # Call cleanup
        from mcp_coder.workflows.implement.task_processing import _cleanup_commit_message_file
        _cleanup_commit_message_file(tmp_path)
        
        assert not commit_file.exists()

    def test_cleanup_handles_missing_file(self, tmp_path: Path) -> None:
        """Test that cleanup handles missing file gracefully."""
        from mcp_coder.workflows.implement.task_processing import _cleanup_commit_message_file
        # Should not raise
        _cleanup_commit_message_file(tmp_path)
```

### Updates to TestCommitChanges Class

```python
@patch("mcp_coder.workflows.implement.task_processing.commit_all_changes")
@patch("mcp_coder.workflows.implement.task_processing.generate_commit_message_with_llm")
def test_commit_changes_uses_file_when_present(
    self, mock_generate_message: MagicMock, mock_commit: MagicMock, tmp_path: Path
) -> None:
    """Test commit_changes uses prepared file instead of LLM."""
    # Create commit message file
    pr_info = tmp_path / "pr_info"
    pr_info.mkdir()
    commit_file = pr_info / ".commit_message.txt"
    commit_file.write_text("feat: prepared message\n\nBody text here.")
    
    mock_commit.return_value = {"success": True, "commit_hash": "abc123", "error": None}
    
    result = commit_changes(tmp_path)
    
    assert result is True
    # LLM should NOT be called
    mock_generate_message.assert_not_called()
    # File should be deleted
    assert not commit_file.exists()
    # Commit should use the prepared message
    mock_commit.assert_called_once()
    call_args = mock_commit.call_args[0]
    assert "feat: prepared message" in call_args[0]

@patch("mcp_coder.workflows.implement.task_processing.commit_all_changes")
@patch("mcp_coder.workflows.implement.task_processing.generate_commit_message_with_llm")
def test_commit_changes_falls_back_to_llm_when_no_file(
    self, mock_generate_message: MagicMock, mock_commit: MagicMock, tmp_path: Path
) -> None:
    """Test commit_changes falls back to LLM when file doesn't exist."""
    mock_generate_message.return_value = (True, "feat: llm message", None)
    mock_commit.return_value = {"success": True, "commit_hash": "abc123", "error": None}
    
    result = commit_changes(tmp_path)
    
    assert result is True
    mock_generate_message.assert_called_once()

@patch("mcp_coder.workflows.implement.task_processing.commit_all_changes")
def test_commit_changes_logs_message_on_failure(
    self, mock_commit: MagicMock, tmp_path: Path, caplog
) -> None:
    """Test commit message is logged when commit fails."""
    # Create commit message file
    pr_info = tmp_path / "pr_info"
    pr_info.mkdir()
    commit_file = pr_info / ".commit_message.txt"
    commit_file.write_text("feat: important message")
    
    mock_commit.return_value = {"success": False, "commit_hash": None, "error": "Git failed"}
    
    result = commit_changes(tmp_path)
    
    assert result is False
    # Message should be logged so it's not lost
    assert "feat: important message" in caplog.text
```

## VERIFICATION

```bash
# Run specific tests
pytest tests/workflows/implement/test_task_processing.py -v -k "commit"

# Run all task_processing tests
pytest tests/workflows/implement/test_task_processing.py -v

# Run pylint
pylint src/mcp_coder/workflows/implement/task_processing.py

# Run mypy
mypy src/mcp_coder/workflows/implement/task_processing.py
```
