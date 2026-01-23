# Step 1: Add Tests for Clean Working Directory Check (TDD)

## LLM Prompt
```
Implement Step 1 from pr_info/steps/summary.md: Add tests for the clean working directory check in set-status command.

Reference: pr_info/steps/step_1.md for detailed specifications.
```

## Overview
Add unit tests for the new working directory check functionality before implementing the feature (TDD approach).

## WHERE: File Paths
- **Modify**: `tests/cli/commands/test_set_status.py`

## WHAT: Test Functions to Add

### Test Function Signatures
```python
def test_execute_set_status_dirty_directory_fails(
    mock_issue_manager: MagicMock,
    mock_load_labels_config: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that set-status fails when working directory has uncommitted changes."""

def test_execute_set_status_dirty_directory_with_force_succeeds(
    mock_issue_manager: MagicMock,
    mock_load_labels_config: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that set-status succeeds with --force even when directory is dirty."""

def test_execute_set_status_clean_directory_succeeds(
    mock_issue_manager: MagicMock,
    mock_load_labels_config: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that set-status succeeds when working directory is clean."""

def test_execute_set_status_ignored_files_allowed(
    mock_issue_manager: MagicMock,
    mock_load_labels_config: MagicMock,
    tmp_path: Path,
) -> None:
    """Test that files in DEFAULT_IGNORED_BUILD_ARTIFACTS don't block status update."""
```

## HOW: Integration Points

### New Mock Required
```python
@pytest.fixture
def mock_is_working_directory_clean():
    """Mock is_working_directory_clean function."""
    with patch(
        "mcp_coder.cli.commands.set_status.is_working_directory_clean"
    ) as mock:
        yield mock
```

### Existing Fixtures to Reuse
- `mock_issue_manager` - Already exists in test file
- `mock_load_labels_config` - Already exists in test file
- `tmp_path` - Pytest built-in

## ALGORITHM: Test Logic (Pseudocode)

### test_execute_set_status_dirty_directory_fails
```
1. Mock is_working_directory_clean to return False
2. Create args with status_label, no --force flag
3. Call execute_set_status(args)
4. Assert returns exit code 1
5. Assert error message contains "uncommitted changes"
```

### test_execute_set_status_dirty_directory_with_force_succeeds
```
1. Mock is_working_directory_clean to return False
2. Create args with status_label AND force=True
3. Call execute_set_status(args)
4. Assert is_working_directory_clean was NOT called (bypassed)
5. Assert returns exit code 0
```

### test_execute_set_status_clean_directory_succeeds
```
1. Mock is_working_directory_clean to return True
2. Create args with status_label, no --force flag
3. Call execute_set_status(args)
4. Assert returns exit code 0
```

### test_execute_set_status_ignored_files_allowed
```
1. Mock is_working_directory_clean, capture call args
2. Create args with status_label
3. Call execute_set_status(args)
4. Assert is_working_directory_clean called with ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS
```

## DATA: Expected Values

### Args Namespace Structure
```python
args = argparse.Namespace(
    status_label="status-05:plan-ready",
    issue=123,  # or None for branch detection
    project_dir=str(tmp_path),
    force=False,  # NEW: --force flag
)
```

### Return Values
- Success: `0`
- Failure (dirty directory): `1`
- Error message (dirty directory): `"Error: Working directory has uncommitted changes. Commit/stash first or use --force."`

## Notes
- Tests should be added to existing test file, following its patterns
- Use existing mock fixtures where possible
- Mock `is_working_directory_clean` at the module level where it's imported
