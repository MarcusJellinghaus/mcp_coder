# Step 6: Integration Testing & Validation

## Reference
**Implementation Plan:** See `pr_info/steps/summary.md` for complete architectural overview.

## Objective
Add comprehensive integration tests and validate complete end-to-end workflow.

## WHERE

**Test File:**
- `tests/cli/commands/test_coordinator.py`
- Add new test class: `TestCoordinatorRunIntegration`

**No Implementation Changes:**
- This step only adds tests to validate existing implementation

## WHAT

### Test Class (Integration Tests)

```python
class TestCoordinatorRunIntegration:
    """Integration tests for coordinator run end-to-end workflow."""
    
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_single_repo_multiple_issues() -> None:
        """Test complete workflow with multiple issues in single repo."""
        # Setup: Mock 3 eligible issues (one per workflow type)
        # Verify: All 3 workflows dispatched correctly
        # Verify: All 3 labels updated correctly
        # Verify: Exit code 0
        
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_all_repos_mode() -> None:
        """Test --all mode with multiple repositories."""
        # Setup: Mock 2 repos, each with eligible issues
        # Verify: Both repos processed
        # Verify: Issues from both repos dispatched
        # Verify: Exit code 0
        
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_priority_ordering() -> None:
        """Test issues processed in correct priority order."""
        # Setup: Mock issues with status-02, 05, 08 in random order
        # Verify: Processed in order: 08, 05, 02
        # Verify: dispatch_workflow calls in correct sequence
        
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_ignore_labels_filtering() -> None:
        """Test issues with ignore_labels are excluded."""
        # Setup: Mock 3 issues, one has "Overview" label
        # Verify: Only 2 issues dispatched
        # Verify: "Overview" issue skipped
        
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_fail_fast_on_jenkins_error() -> None:
        """Test fail-fast when Jenkins job fails to start."""
        # Setup: Mock 3 eligible issues, 2nd one triggers JenkinsError
        # Verify: Only 1 issue dispatched (fail-fast)
        # Verify: Exit code 1
        # Verify: Error logged
        
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_fail_fast_on_missing_branch() -> None:
        """Test fail-fast when linked branch missing for implement/create-pr."""
        # Setup: Mock issue with status-05, but no linked branches
        # Verify: ValueError raised
        # Verify: Exit code 1
        # Verify: Helpful error message
        
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_log_level_pass_through() -> None:
        """Test log level passed through to workflow commands."""
        # Setup: Run with --log-level DEBUG
        # Verify: COMMAND contains "mcp-coder --log-level DEBUG"
```

### Additional Validation Tests

```python
class TestCoordinatorRunEdgeCases:
    """Edge case tests for coordinator run."""
    
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_no_open_issues() -> None:
        """Test handling when repository has no open issues."""
        
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_all_issues_have_bot_busy_labels() -> None:
        """Test when all issues are already being processed."""
        
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_issue_with_multiple_bot_pickup_labels() -> None:
        """Test handling of misconfigured issues with multiple bot_pickup labels."""
```

## HOW

### Mock Setup Patterns

**Complete End-to-End Mock:**
```python
# Mock config
mock_create_default_config.return_value = False

# Mock repo config
mock_load_repo_config.return_value = {
    "repo_url": "https://github.com/user/repo.git",
    "executor_test_path": "Test/job",
    "github_credentials_id": "github-pat"
}

# Mock Jenkins credentials
mock_get_jenkins_credentials.return_value = ("http://jenkins:8080", "user", "token")

# Mock Jenkins client
mock_jenkins_instance = MagicMock()
mock_JenkinsClient.return_value = mock_jenkins_instance
mock_jenkins_instance.start_job.return_value = 12345
mock_jenkins_instance.get_job_status.return_value = JobStatus(
    status="queued", build_number=None, duration_ms=None, url=None
)

# Mock IssueManager
mock_issue_instance = MagicMock()
mock_IssueManager.return_value = mock_issue_instance
mock_issue_instance.list_issues.return_value = [
    IssueData(number=1, labels=["status-08:ready-pr"], ...),
    IssueData(number=2, labels=["status-05:plan-ready"], ...),
    IssueData(number=3, labels=["status-02:awaiting-planning"], ...),
]

# Mock IssueBranchManager
mock_branch_instance = MagicMock()
mock_IssueBranchManager.return_value = mock_branch_instance
mock_branch_instance.get_linked_branches.return_value = ["123-feature"]
```

### Verification Patterns

**Verify Job Triggered:**
```python
# Check Jenkins start_job called 3 times
assert mock_jenkins_instance.start_job.call_count == 3

# Check specific workflow dispatched
calls = mock_jenkins_instance.start_job.call_args_list
assert "create-pr" in calls[0][0][1]["COMMAND"]  # First call (status-08)
assert "implement" in calls[1][0][1]["COMMAND"]   # Second call (status-05)
assert "create-plan" in calls[2][0][1]["COMMAND"] # Third call (status-02)
```

**Verify Label Updated:**
```python
# Check labels updated for each issue
assert mock_issue_instance.remove_labels.call_count == 3
assert mock_issue_instance.add_labels.call_count == 3

# Check specific label transitions
remove_calls = mock_issue_instance.remove_labels.call_args_list
add_calls = mock_issue_instance.add_labels.call_args_list

# Issue 1: status-08 → status-09
assert remove_calls[0][0] == (1, "status-08:ready-pr")
assert add_calls[0][0] == (1, "status-09:pr-creating")
```

## ALGORITHM

```
1. Set up comprehensive mocks for all dependencies
2. Create test scenarios covering:
   - Happy path (single repo, all repos)
   - Priority ordering
   - Filtering (ignore_labels)
   - Error handling (fail-fast)
   - Edge cases (no issues, misconfigured labels)
3. Execute coordinator run via execute_coordinator_run()
4. Verify:
   - Correct number of workflows dispatched
   - Correct workflow types triggered
   - Correct label transitions
   - Correct error handling
   - Correct exit codes
5. Run all tests and validate coverage
```

## DATA

### Test Scenarios

**Scenario 1: Complete Workflow (3 issues)**
```python
Input:
- Issue #101: ["status-08:ready-pr"] → Trigger create-pr
- Issue #102: ["status-05:plan-ready"] → Trigger implement
- Issue #103: ["status-02:awaiting-planning"] → Trigger create-plan

Expected Output:
- 3 Jenkins jobs triggered
- Labels updated: 08→09, 05→06, 02→03
- Exit code: 0
```

**Scenario 2: Filtering (ignore_labels)**
```python
Input:
- Issue #101: ["status-08:ready-pr"]
- Issue #102: ["status-05:plan-ready", "Overview"]  ← Excluded
- Issue #103: ["status-02:awaiting-planning"]

Expected Output:
- 2 Jenkins jobs triggered (issues #101, #103)
- Issue #102 skipped
- Exit code: 0
```

**Scenario 3: Fail-Fast (Jenkins error)**
```python
Input:
- Issue #101: ["status-08:ready-pr"] → Success
- Issue #102: ["status-05:plan-ready"] → JenkinsError
- Issue #103: ["status-02:awaiting-planning"] → Never reached

Expected Output:
- 1 Jenkins job triggered (issue #101)
- Processing stops at issue #102
- Exit code: 1
```

## Implementation Notes

1. **Comprehensive Mocking:**
   - Mock all external dependencies
   - Use MagicMock for flexible verification
   - Set up realistic return values

2. **Call Order Verification:**
   ```python
   # Verify priority order
   calls = mock_jenkins_instance.start_job.call_args_list
   # Extract issue numbers from calls and verify order
   issue_numbers = [extract_issue_from_command(call) for call in calls]
   assert issue_numbers == [101, 102, 103]  # Priority order
   ```

3. **Edge Case Coverage:**
   - Empty issue list
   - No eligible issues
   - Misconfigured issues
   - GitHub API errors
   - Jenkins API errors
   - Missing branches

## LLM Prompt for Implementation

```
Implement Step 6 of the coordinator run feature as described in pr_info/steps/summary.md.

Task: Add integration tests to tests/cli/commands/test_coordinator.py

Requirements:
1. Add TestCoordinatorRunIntegration class with 7 test methods:
   - End-to-end single repo with multiple issues
   - End-to-end all repos mode
   - Priority ordering verification
   - Ignore labels filtering
   - Fail-fast on Jenkins error
   - Fail-fast on missing branch
   - Log level pass-through

2. Add TestCoordinatorRunEdgeCases class with 3 test methods:
   - No open issues
   - All issues have bot_busy labels
   - Issues with multiple bot_pickup labels

3. Set up comprehensive mocks for all dependencies:
   - create_default_config, load_repo_config, get_jenkins_credentials
   - JenkinsClient, IssueManager, IssueBranchManager
   - Return realistic data (IssueData, JobStatus, etc.)

4. Verify complete workflow:
   - Correct workflows dispatched
   - Correct label transitions
   - Correct error handling
   - Correct exit codes

5. Run code quality checks:
   - mcp__code-checker__run_pytest_check (fast unit tests only)
   - mcp__code-checker__run_pylint_check
   - mcp__code-checker__run_mypy_check

Follow the exact test scenarios in step_6.md.
Ensure comprehensive coverage of happy path and error cases.
```

## Test Execution

**Run fast unit tests only:**
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"],
    show_details=False
)
```

**Check coverage:**
```bash
# Run with coverage report
pytest tests/cli/commands/test_coordinator.py::TestCoordinatorRunIntegration -v --cov=src/mcp_coder/cli/commands/coordinator --cov-report=term-missing
```

## Success Criteria

- ✅ All 10 integration tests pass
- ✅ End-to-end workflow validated
- ✅ Priority ordering verified
- ✅ Filtering logic verified
- ✅ Fail-fast behavior verified
- ✅ Edge cases handled correctly
- ✅ Code coverage >85% for coordinator.py
- ✅ Pylint/mypy checks pass
- ✅ All previous tests still pass

## Final Validation

After Step 6 completion, verify entire feature:

```bash
# Run all coordinator tests
pytest tests/cli/commands/test_coordinator.py -v

# Run all CLI tests  
pytest tests/cli/test_main.py -v

# Check overall coverage
pytest tests/ --cov=src/mcp_coder --cov-report=term-missing

# Manual CLI test (if Jenkins/GitHub configured)
mcp-coder coordinator run --repo mcp_coder --log-level DEBUG
```

Expected: All tests pass, feature ready for PR.
