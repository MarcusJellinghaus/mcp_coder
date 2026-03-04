# Step 2: Write Tests for Uncommitted Changes Display (TDD)

## Context
Read `pr_info/steps/summary.md` for full context. This step follows TDD by writing failing tests BEFORE implementing the feature.

## Objective
Write comprehensive tests for uncommitted changes display logic. These tests will fail initially and will be made to pass in Step 3.

## Location
**File**: `tests/cli/commands/test_git_tool.py`

## Test Class

### WHERE: Add New Test Class
```python
class TestCompactDiffUncommittedChanges:
    """Test uncommitted changes display in compact-diff output."""
```

### Test Cases to Write

#### Test 1: Default Behavior - Show Uncommitted Changes
```python
def test_shows_uncommitted_changes_by_default(
    self,
    mock_get_compact_diff: MagicMock,
    mock_detect_base_branch: MagicMock,
    mock_resolve_project_dir: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that uncommitted changes are shown by default (without --committed-only)."""
    project_dir = Path("/test/project")
    mock_resolve_project_dir.return_value = project_dir
    mock_detect_base_branch.return_value = "main"
    mock_get_compact_diff.return_value = "diff --git foo.py\n+committed change"
    
    # Mock get_git_diff_for_commit to return uncommitted changes
    with patch("mcp_coder.cli.commands.git_tool.get_git_diff_for_commit") as mock_uncommitted:
        mock_uncommitted.return_value = (
            "=== STAGED CHANGES ===\n"
            "diff --git bar.py\n"
            "+staged change"
        )
        
        args = argparse.Namespace(
            project_dir=None,
            base_branch=None,
            exclude=None,
            committed_only=False,
        )
        result = execute_compact_diff(args)
        
        assert result == 0
        captured = capsys.readouterr()
        
        # Should contain both committed and uncommitted sections
        assert "diff --git foo.py" in captured.out  # committed
        assert "=== UNCOMMITTED CHANGES ===" in captured.out
        assert "=== STAGED CHANGES ===" in captured.out
        assert "staged change" in captured.out
```

#### Test 2: Committed-Only Flag Suppresses Uncommitted
```python
def test_committed_only_flag_suppresses_uncommitted(
    self,
    mock_get_compact_diff: MagicMock,
    mock_detect_base_branch: MagicMock,
    mock_resolve_project_dir: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that --committed-only flag suppresses uncommitted changes."""
    project_dir = Path("/test/project")
    mock_resolve_project_dir.return_value = project_dir
    mock_detect_base_branch.return_value = "main"
    mock_get_compact_diff.return_value = "diff --git foo.py\n+committed change"
    
    # Mock get_git_diff_for_commit to return uncommitted changes
    with patch("mcp_coder.cli.commands.git_tool.get_git_diff_for_commit") as mock_uncommitted:
        mock_uncommitted.return_value = "=== STAGED CHANGES ===\ndiff --git bar.py"
        
        args = argparse.Namespace(
            project_dir=None,
            base_branch=None,
            exclude=None,
            committed_only=True,  # Flag set to True
        )
        result = execute_compact_diff(args)
        
        assert result == 0
        captured = capsys.readouterr()
        
        # Should only contain committed changes
        assert "diff --git foo.py" in captured.out
        assert "UNCOMMITTED CHANGES" not in captured.out
        # get_git_diff_for_commit should NOT be called
        mock_uncommitted.assert_not_called()
```

#### Test 3: Clean Working Directory - Skip Uncommitted Section
```python
def test_clean_working_directory_skips_uncommitted_section(
    self,
    mock_get_compact_diff: MagicMock,
    mock_detect_base_branch: MagicMock,
    mock_resolve_project_dir: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that uncommitted section is skipped when working directory is clean."""
    project_dir = Path("/test/project")
    mock_resolve_project_dir.return_value = project_dir
    mock_detect_base_branch.return_value = "main"
    mock_get_compact_diff.return_value = "diff --git foo.py\n+committed change"
    
    # Mock get_git_diff_for_commit to return empty string (clean working dir)
    with patch("mcp_coder.cli.commands.git_tool.get_git_diff_for_commit") as mock_uncommitted:
        mock_uncommitted.return_value = ""  # No uncommitted changes
        
        args = argparse.Namespace(
            project_dir=None,
            base_branch=None,
            exclude=None,
            committed_only=False,
        )
        result = execute_compact_diff(args)
        
        assert result == 0
        captured = capsys.readouterr()
        
        # Should only contain committed changes
        assert "diff --git foo.py" in captured.out
        assert "UNCOMMITTED CHANGES" not in captured.out
```

#### Test 4: No Committed Changes, Only Uncommitted
```python
def test_no_committed_changes_only_uncommitted(
    self,
    mock_get_compact_diff: MagicMock,
    mock_detect_base_branch: MagicMock,
    mock_resolve_project_dir: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test 'No committed changes' message when only uncommitted changes exist."""
    project_dir = Path("/test/project")
    mock_resolve_project_dir.return_value = project_dir
    mock_detect_base_branch.return_value = "main"
    mock_get_compact_diff.return_value = ""  # No committed changes
    
    # Mock get_git_diff_for_commit to return uncommitted changes
    with patch("mcp_coder.cli.commands.git_tool.get_git_diff_for_commit") as mock_uncommitted:
        mock_uncommitted.return_value = (
            "=== STAGED CHANGES ===\n"
            "diff --git bar.py\n"
            "+staged change"
        )
        
        args = argparse.Namespace(
            project_dir=None,
            base_branch=None,
            exclude=None,
            committed_only=False,
        )
        result = execute_compact_diff(args)
        
        assert result == 0
        captured = capsys.readouterr()
        
        # Should show "No committed changes" message
        assert "No committed changes" in captured.out
        assert "=== UNCOMMITTED CHANGES ===" in captured.out
        assert "staged change" in captured.out
```

#### Test 5: Both Committed and Uncommitted Present
```python
def test_both_committed_and_uncommitted_present(
    self,
    mock_get_compact_diff: MagicMock,
    mock_detect_base_branch: MagicMock,
    mock_resolve_project_dir: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test output format when both committed and uncommitted changes exist."""
    project_dir = Path("/test/project")
    mock_resolve_project_dir.return_value = project_dir
    mock_detect_base_branch.return_value = "main"
    mock_get_compact_diff.return_value = "diff --git committed.py\n+committed"
    
    with patch("mcp_coder.cli.commands.git_tool.get_git_diff_for_commit") as mock_uncommitted:
        mock_uncommitted.return_value = (
            "=== STAGED CHANGES ===\n"
            "diff --git staged.py\n"
            "+staged\n"
            "\n"
            "=== UNSTAGED CHANGES ===\n"
            "diff --git modified.py\n"
            "+modified\n"
            "\n"
            "=== UNTRACKED FILES ===\n"
            "diff --git new.py\n"
            "+new file"
        )
        
        args = argparse.Namespace(
            project_dir=None,
            base_branch=None,
            exclude=None,
            committed_only=False,
        )
        result = execute_compact_diff(args)
        
        assert result == 0
        captured = capsys.readouterr()
        
        # Verify order and sections
        output = captured.out
        committed_idx = output.find("diff --git committed.py")
        uncommitted_header_idx = output.find("=== UNCOMMITTED CHANGES ===")
        staged_header_idx = output.find("=== STAGED CHANGES ===")
        
        # Committed should come first
        assert committed_idx < uncommitted_header_idx
        # Uncommitted header should come before staged header
        assert uncommitted_header_idx < staged_header_idx
        
        # All sections present
        assert "=== STAGED CHANGES ===" in output
        assert "=== UNSTAGED CHANGES ===" in output
        assert "=== UNTRACKED FILES ===" in output
```

## Fixtures Required

### Add Mock Fixture for get_git_diff_for_commit
```python
@pytest.fixture
def mock_get_git_diff_for_commit() -> Generator[MagicMock, None, None]:
    """Mock get_git_diff_for_commit function."""
    with patch("mcp_coder.cli.commands.git_tool.get_git_diff_for_commit") as mock:
        yield mock
```

Note: This fixture will be used inline with `with patch()` in tests for clarity.

## Validation

### Running Tests (Expected to Fail)
```bash
# Run the new test class
pytest tests/cli/commands/test_git_tool.py::TestCompactDiffUncommittedChanges -v

# Expected result: All tests FAIL (feature not implemented yet)
# Typical error: "AttributeError: module has no attribute 'get_git_diff_for_commit'"
# or "AssertionError: UNCOMMITTED CHANGES not found in output"
```

## Definition of Done
- [ ] 5 test cases written in new `TestCompactDiffUncommittedChanges` class
- [ ] Tests properly mock `get_git_diff_for_commit()`
- [ ] Tests verify output format and section ordering
- [ ] All tests currently FAIL (expected, since feature not implemented)
- [ ] Test code follows existing test patterns in file
- [ ] No syntax errors in test code

## LLM Implementation Prompt

```
You are implementing Step 2 of the compact-diff uncommitted changes feature (TDD approach).

Read pr_info/steps/summary.md for full context.

Task: Write failing tests for uncommitted changes display BEFORE implementing the feature.

File: tests/cli/commands/test_git_tool.py

Create a new test class TestCompactDiffUncommittedChanges with 5 test methods:

1. test_shows_uncommitted_changes_by_default
   - Mock get_compact_diff to return committed changes
   - Mock get_git_diff_for_commit to return uncommitted changes
   - Verify both sections appear in output
   - Verify "=== UNCOMMITTED CHANGES ===" header present

2. test_committed_only_flag_suppresses_uncommitted
   - Set args.committed_only = True
   - Verify get_git_diff_for_commit NOT called
   - Verify "UNCOMMITTED CHANGES" NOT in output

3. test_clean_working_directory_skips_uncommitted_section
   - Mock get_git_diff_for_commit to return empty string
   - Verify "UNCOMMITTED CHANGES" NOT in output

4. test_no_committed_changes_only_uncommitted
   - Mock get_compact_diff to return empty string
   - Mock get_git_diff_for_commit to return uncommitted changes
   - Verify "No committed changes" message present
   - Verify uncommitted section shown

5. test_both_committed_and_uncommitted_present
   - Both mocks return non-empty strings
   - Verify output order: committed first, then uncommitted
   - Verify all section headers present

Use existing fixtures (mock_get_compact_diff, mock_detect_base_branch, etc.) and add inline patches for get_git_diff_for_commit.

Follow TDD: These tests should FAIL when run (feature not implemented yet).

Verify:
- Run: pytest tests/cli/commands/test_git_tool.py::TestCompactDiffUncommittedChanges -v
- Expected: All tests FAIL (this is correct for TDD)
```

## Next Step
Proceed to `pr_info/steps/step_3.md` - Implement uncommitted changes display logic to make tests pass.
