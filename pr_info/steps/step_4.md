# Step 4: Write Tests for Exclude Patterns on Uncommitted Changes (TDD)

## Context
Read `pr_info/steps/summary.md` for full context. This step follows TDD by writing tests for exclude pattern filtering BEFORE implementing the feature.

## Objective
Write tests to verify that `--exclude` patterns apply to uncommitted changes, not just committed changes. These tests will fail initially and be made to pass in Step 5.

## Location
**File**: `tests/cli/commands/test_git_tool.py`

## Test Cases to Add

### Add to Existing TestCompactDiffUncommittedChanges Class

#### Test 1: Exclude Patterns Apply to Uncommitted Changes
```python
def test_exclude_patterns_apply_to_uncommitted_changes(
    self,
    mock_get_compact_diff: MagicMock,
    mock_detect_base_branch: MagicMock,
    mock_resolve_project_dir: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that --exclude patterns filter uncommitted changes."""
    project_dir = Path("/test/project")
    mock_resolve_project_dir.return_value = project_dir
    mock_detect_base_branch.return_value = "main"
    mock_get_compact_diff.return_value = "diff --git committed.py\n+committed"
    
    with patch("mcp_coder.cli.commands.git_tool.get_git_diff_for_commit") as mock_uncommitted:
        # Uncommitted diff includes both .py and .log files
        mock_uncommitted.return_value = (
            "=== STAGED CHANGES ===\n"
            "diff --git staged.py staged.py\n"
            "+staged python\n"
            "diff --git debug.log debug.log\n"
            "+log file content"
        )
        
        # Apply --exclude *.log pattern
        args = argparse.Namespace(
            project_dir=None,
            base_branch=None,
            exclude=["*.log"],
            committed_only=False,
        )
        result = execute_compact_diff(args)
        
        assert result == 0
        captured = capsys.readouterr()
        
        # Should contain .py file but NOT .log file
        assert "staged.py" in captured.out
        assert "staged python" in captured.out
        assert "debug.log" not in captured.out
        assert "log file content" not in captured.out
```

#### Test 2: Multiple Exclude Patterns
```python
def test_multiple_exclude_patterns_on_uncommitted(
    self,
    mock_get_compact_diff: MagicMock,
    mock_detect_base_branch: MagicMock,
    mock_resolve_project_dir: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that multiple --exclude patterns filter uncommitted changes."""
    project_dir = Path("/test/project")
    mock_resolve_project_dir.return_value = project_dir
    mock_detect_base_branch.return_value = "main"
    mock_get_compact_diff.return_value = ""
    
    with patch("mcp_coder.cli.commands.git_tool.get_git_diff_for_commit") as mock_uncommitted:
        # Uncommitted diff with multiple file types
        mock_uncommitted.return_value = (
            "=== STAGED CHANGES ===\n"
            "diff --git code.py code.py\n"
            "+python code\n"
            "diff --git test.log test.log\n"
            "+log content\n"
            "diff --git data.json data.json\n"
            "+json data"
        )
        
        # Exclude both .log and .json
        args = argparse.Namespace(
            project_dir=None,
            base_branch=None,
            exclude=["*.log", "*.json"],
            committed_only=False,
        )
        result = execute_compact_diff(args)
        
        assert result == 0
        captured = capsys.readouterr()
        
        # Should only contain .py file
        assert "code.py" in captured.out
        assert "python code" in captured.out
        assert "test.log" not in captured.out
        assert "data.json" not in captured.out
```

#### Test 3: Exclude All Uncommitted Changes
```python
def test_exclude_all_uncommitted_changes(
    self,
    mock_get_compact_diff: MagicMock,
    mock_detect_base_branch: MagicMock,
    mock_resolve_project_dir: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that excluding all uncommitted files results in no uncommitted section."""
    project_dir = Path("/test/project")
    mock_resolve_project_dir.return_value = project_dir
    mock_detect_base_branch.return_value = "main"
    mock_get_compact_diff.return_value = "diff --git committed.py\n+committed"
    
    with patch("mcp_coder.cli.commands.git_tool.get_git_diff_for_commit") as mock_uncommitted:
        # Uncommitted diff with only .log files
        mock_uncommitted.return_value = (
            "=== STAGED CHANGES ===\n"
            "diff --git debug.log debug.log\n"
            "+log content"
        )
        
        # Exclude *.log (all uncommitted files)
        args = argparse.Namespace(
            project_dir=None,
            base_branch=None,
            exclude=["*.log"],
            committed_only=False,
        )
        result = execute_compact_diff(args)
        
        assert result == 0
        captured = capsys.readouterr()
        
        # Should not show uncommitted section if all files excluded
        assert "UNCOMMITTED CHANGES" not in captured.out
        assert "debug.log" not in captured.out
```

#### Test 4: Exclude Patterns on Path Prefixes
```python
def test_exclude_path_prefix_on_uncommitted(
    self,
    mock_get_compact_diff: MagicMock,
    mock_detect_base_branch: MagicMock,
    mock_resolve_project_dir: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that path prefix patterns (e.g., pr_info/**) filter uncommitted changes."""
    project_dir = Path("/test/project")
    mock_resolve_project_dir.return_value = project_dir
    mock_detect_base_branch.return_value = "main"
    mock_get_compact_diff.return_value = ""
    
    with patch("mcp_coder.cli.commands.git_tool.get_git_diff_for_commit") as mock_uncommitted:
        # Uncommitted diff with files in different directories
        mock_uncommitted.return_value = (
            "=== STAGED CHANGES ===\n"
            "diff --git src/main.py src/main.py\n"
            "+source code\n"
            "diff --git pr_info/notes.md pr_info/notes.md\n"
            "+notes content"
        )
        
        # Exclude pr_info/** pattern
        args = argparse.Namespace(
            project_dir=None,
            base_branch=None,
            exclude=["pr_info/**"],
            committed_only=False,
        )
        result = execute_compact_diff(args)
        
        assert result == 0
        captured = capsys.readouterr()
        
        # Should contain src/ file but not pr_info/ file
        assert "src/main.py" in captured.out
        assert "source code" in captured.out
        assert "pr_info/notes.md" not in captured.out
        assert "notes content" not in captured.out
```

## Helper Function Test (Internal)

These tests validate the helper function we'll create in Step 5:

#### Test 5: Helper Function - Filter Diff by Patterns
```python
def test_apply_exclude_patterns_to_uncommitted_diff_helper(self) -> None:
    """Test the helper function that filters uncommitted diff by exclude patterns."""
    from mcp_coder.cli.commands.git_tool import _apply_exclude_patterns_to_uncommitted_diff
    
    # Sample uncommitted diff with multiple files
    uncommitted_diff = (
        "=== STAGED CHANGES ===\n"
        "diff --git code.py code.py\n"
        "+python\n"
        "diff --git test.log test.log\n"
        "+log\n"
        "\n"
        "=== UNSTAGED CHANGES ===\n"
        "diff --git data.json data.json\n"
        "+json"
    )
    
    # Apply *.log pattern
    filtered = _apply_exclude_patterns_to_uncommitted_diff(uncommitted_diff, ["*.log"])
    
    # Should exclude test.log
    assert "code.py" in filtered
    assert "test.log" not in filtered
    assert "data.json" in filtered
```

## Validation

### Running Tests (Expected to Fail)
```bash
# Run the new test cases
pytest tests/cli/commands/test_git_tool.py::TestCompactDiffUncommittedChanges::test_exclude_patterns_apply_to_uncommitted_changes -v
pytest tests/cli/commands/test_git_tool.py::TestCompactDiffUncommittedChanges::test_multiple_exclude_patterns_on_uncommitted -v
pytest tests/cli/commands/test_git_tool.py::TestCompactDiffUncommittedChanges::test_exclude_all_uncommitted_changes -v
pytest tests/cli/commands/test_git_tool.py::TestCompactDiffUncommittedChanges::test_exclude_path_prefix_on_uncommitted -v

# Expected result: All tests FAIL
# Typical error: "debug.log found in output" (exclude not implemented yet)
# or "AttributeError: module has no attribute '_apply_exclude_patterns_to_uncommitted_diff'"
```

## Definition of Done
- [ ] 4 new test cases added to `TestCompactDiffUncommittedChanges`
- [ ] 1 helper function test added
- [ ] Tests verify exclude patterns filter uncommitted changes
- [ ] Tests verify multiple patterns work
- [ ] Tests verify path prefix patterns (e.g., `pr_info/**`)
- [ ] Tests verify all files excluded → no uncommitted section
- [ ] All tests currently FAIL (expected, since feature not implemented)
- [ ] Test code follows existing patterns

## LLM Implementation Prompt

```
You are implementing Step 4 of the compact-diff uncommitted changes feature (TDD approach).

Read pr_info/steps/summary.md for full context.

Task: Write failing tests for exclude pattern filtering on uncommitted changes.

File: tests/cli/commands/test_git_tool.py
Class: TestCompactDiffUncommittedChanges (add to existing class from Step 2)

Add 4 new test methods:

1. test_exclude_patterns_apply_to_uncommitted_changes
   - Uncommitted diff has .py and .log files
   - Apply --exclude "*.log"
   - Verify .py file shown, .log file NOT shown

2. test_multiple_exclude_patterns_on_uncommitted
   - Uncommitted diff has .py, .log, .json files
   - Apply --exclude ["*.log", "*.json"]
   - Verify only .py file shown

3. test_exclude_all_uncommitted_changes
   - Uncommitted diff has only .log files
   - Apply --exclude "*.log"
   - Verify no "UNCOMMITTED CHANGES" section shown

4. test_exclude_path_prefix_on_uncommitted
   - Uncommitted diff has src/main.py and pr_info/notes.md
   - Apply --exclude "pr_info/**"
   - Verify src/main.py shown, pr_info/notes.md NOT shown

Also add helper function test:
5. test_apply_exclude_patterns_to_uncommitted_diff_helper
   - Test the _apply_exclude_patterns_to_uncommitted_diff() function directly
   - Input: uncommitted diff with multiple files
   - Output: filtered diff with excluded files removed

Use existing fixtures and patterns from Step 2 tests.

Follow TDD: These tests should FAIL when run (feature not implemented yet).

Verify:
- Run: pytest tests/cli/commands/test_git_tool.py::TestCompactDiffUncommittedChanges -v
- Expected: New tests FAIL (this is correct for TDD)
```

## Next Step
Proceed to `pr_info/steps/step_5.md` - Implement exclude pattern filtering to make tests pass.
