# Step 1: Tests for `gh-tool get-base-branch` Command

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement the tests for the `gh-tool get-base-branch` CLI command following Test-Driven Development.
Create comprehensive unit tests that cover all detection scenarios and edge cases.
Do NOT implement the actual command yet - only write the tests.
```

## WHERE

- **Create**: `tests/cli/commands/test_gh_tool.py`

## WHAT

### Test Classes and Functions

```python
# Test file structure
class TestGetBaseBranchCommand:
    """Tests for execute_get_base_branch function."""
    
    def test_get_base_branch_from_open_pr() -> None:
        """Test detection from open PR base branch."""
    
    def test_get_base_branch_from_issue_body() -> None:
        """Test detection from linked issue's ### Base Branch section."""
    
    def test_get_base_branch_falls_back_to_default() -> None:
        """Test fallback to default branch (main/master)."""
    
    def test_get_base_branch_pr_takes_priority_over_issue() -> None:
        """Test that PR base branch has higher priority than issue."""
    
    def test_get_base_branch_issue_takes_priority_over_default() -> None:
        """Test that issue base branch has higher priority than default."""
    
    def test_get_base_branch_outputs_to_stdout() -> None:
        """Test that branch name is printed to stdout only."""
    
    def test_get_base_branch_exit_code_success() -> None:
        """Test exit code 0 on successful detection."""
    
    def test_get_base_branch_exit_code_detection_failure() -> None:
        """Test exit code 1 when detection fails but no error."""
    
    def test_get_base_branch_exit_code_error() -> None:
        """Test exit code 2 on error (not a git repo, API failure)."""
    
    def test_get_base_branch_with_project_dir_option() -> None:
        """Test --project-dir option."""
    
    def test_get_base_branch_no_current_branch() -> None:
        """Test when not on any branch (detached HEAD)."""
    
    def test_get_base_branch_branch_without_issue_number() -> None:
        """Test when branch name doesn't contain issue number."""


class TestGhToolCommandIntegration:
    """Test gh-tool command CLI integration."""
    
    def test_gh_tool_get_base_branch_command_exists() -> None:
        """Test that gh-tool get-base-branch is registered in CLI."""
    
    def test_gh_tool_help_shows_get_base_branch() -> None:
        """Test that gh-tool --help shows get-base-branch subcommand."""
    
    def test_gh_tool_get_base_branch_help_shows_exit_codes() -> None:
        """Test that get-base-branch --help shows exit codes in epilog."""
```

## HOW

### Test Fixtures

```python
@pytest.fixture
def mock_pr_manager():
    """Mock PullRequestManager with open PR."""
    with patch("mcp_coder.cli.commands.gh_tool.PullRequestManager") as mock:
        yield mock

@pytest.fixture  
def mock_issue_manager():
    """Mock IssueManager for issue lookup."""
    with patch("mcp_coder.cli.commands.gh_tool.IssueManager") as mock:
        yield mock

@pytest.fixture
def mock_git_readers():
    """Mock git reader functions."""
    with patch("mcp_coder.cli.commands.gh_tool.get_current_branch_name") as mock_branch, \
         patch("mcp_coder.cli.commands.gh_tool.extract_issue_number_from_branch") as mock_extract, \
         patch("mcp_coder.cli.commands.gh_tool.get_default_branch_name") as mock_default:
        yield mock_branch, mock_extract, mock_default
```

### Test Pattern (Example)

```python
def test_get_base_branch_from_open_pr(
    mock_pr_manager, mock_git_readers, capsys
):
    """Test detection from open PR base branch."""
    mock_branch, mock_extract, mock_default = mock_git_readers
    
    # Setup: current branch has an open PR targeting 'develop'
    mock_branch.return_value = "370-feature-name"
    mock_pr_manager.return_value.list_pull_requests.return_value = [
        {"head_branch": "370-feature-name", "base_branch": "develop"}
    ]
    
    args = argparse.Namespace(project_dir=None)
    result = execute_get_base_branch(args)
    
    assert result == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "develop"
    # PR manager should be called, issue manager should NOT be called
    mock_pr_manager.return_value.list_pull_requests.assert_called_once()
```

## DATA

### Expected Test Scenarios

| Scenario | PR Exists | Issue Base | Default | Expected Output | Exit Code |
|----------|-----------|------------|---------|-----------------|-----------|
| PR with base branch | Yes (develop) | - | main | develop | 0 |
| No PR, issue has base | No | release/v2 | main | release/v2 | 0 |
| No PR, no issue base | No | None | main | main | 0 |
| No PR, branch has no issue # | No | N/A | main | main | 0 |
| Not a git repo | - | - | - | error | 2 |
| Detached HEAD | None | - | main | main | 0 |

## ALGORITHM

```
1. Import test dependencies (pytest, Mock, patch, argparse)
2. Create test fixtures for mocking managers
3. For each test case:
   a. Setup mocks for expected behavior
   b. Create args namespace
   c. Call execute_get_base_branch(args)
   d. Assert return code
   e. Assert stdout/stderr content
4. Test CLI integration separately
```

## Acceptance Criteria

- [ ] All detection priority scenarios tested (PR → Issue → Default)
- [ ] All exit codes tested (0, 1, 2)
- [ ] Output format tested (stdout only, no extra text)
- [ ] CLI integration tested (command registered, help works)
- [ ] Exit codes in --help epilog tested
- [ ] Edge cases tested (detached HEAD, no issue number in branch)
