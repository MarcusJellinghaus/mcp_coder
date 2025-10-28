# Step 3: Workflow Dispatcher (TDD)

## Reference
**Implementation Plan:** See `pr_info/steps/summary.md` for complete architectural overview.

## Objective
Implement workflow dispatcher that triggers Jenkins jobs and updates issue labels.

## WHERE

**Test File:**
- `tests/cli/commands/test_coordinator.py`
- Add new test class: `TestDispatchWorkflow`

**Implementation File:**
- `src/mcp_coder/cli/commands/coordinator.py`
- Add function after `get_eligible_issues()`

## WHAT

### Test Class (TDD First)

```python
class TestDispatchWorkflow:
    """Tests for dispatch_workflow function."""
    
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    def test_dispatch_workflow_create_plan() -> None:
        """Test dispatching create-plan workflow."""
        # Mock issue with status-02:awaiting-planning
        # Verify BRANCH_NAME="main"
        # Verify COMMAND contains "create-plan {issue_number}"
        
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    def test_dispatch_workflow_implement() -> None:
        """Test dispatching implement workflow."""
        # Mock issue with status-05:plan-ready
        # Mock get_linked_branches() returns ["123-feature"]
        # Verify BRANCH_NAME="123-feature"
        # Verify COMMAND contains "implement"
        
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    def test_dispatch_workflow_create_pr() -> None:
        """Test dispatching create-pr workflow."""
        # Mock issue with status-08:ready-pr
        # Mock get_linked_branches() returns ["123-feature"]
        # Verify BRANCH_NAME="123-feature"
        # Verify COMMAND contains "create-pr"
        
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    def test_dispatch_workflow_missing_branch() -> None:
        """Test error when linked branch missing for implement/create-pr."""
        # Mock issue with status-05:plan-ready
        # Mock get_linked_branches() returns []
        # Verify raises ValueError with helpful message
        
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    def test_dispatch_workflow_jenkins_failure() -> None:
        """Test error handling when Jenkins job fails to start."""
        # Mock start_job() raises JenkinsError
        # Verify raises JenkinsError (bubbles up)
        
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    def test_dispatch_workflow_label_update() -> None:
        """Test label update after successful job trigger."""
        # Mock successful job trigger
        # Verify remove_labels() called with old label
        # Verify add_labels() called with new label
```

### Main Function Signature

```python
def dispatch_workflow(
    issue: IssueData,
    workflow_name: str,
    repo_config: dict[str, str],
    jenkins_client: JenkinsClient,
    issue_manager: IssueManager,
    branch_manager: IssueBranchManager,
    log_level: str
) -> None:
    """Trigger Jenkins job for workflow and update issue label.
    
    Args:
        issue: GitHub issue data
        workflow_name: Workflow to execute ("create-plan", "implement", "create-pr")
        repo_config: Repository configuration with repo_url, executor_test_path, credentials
        jenkins_client: Jenkins client for job triggering
        issue_manager: IssueManager for label updates
        branch_manager: IssueBranchManager for branch resolution
        log_level: Log level to pass to workflow command
        
    Raises:
        ValueError: If linked branch missing for implement/create-pr
        JenkinsError: If job trigger or status check fails
    """
```

### Constants to Add

```python
# Workflow configuration mapping
WORKFLOW_MAPPING = {
    "status-02:awaiting-planning": {
        "workflow": "create-plan",
        "branch_strategy": "main",
        "next_label": "status-03:planning",
    },
    "status-05:plan-ready": {
        "workflow": "implement",
        "branch_strategy": "from_issue",
        "next_label": "status-06:implementing",
    },
    "status-08:ready-pr": {
        "workflow": "create-pr",
        "branch_strategy": "from_issue",
        "next_label": "status-09:pr-creating",
    },
}

# Workflow command template
WORKFLOW_COMMAND_TEMPLATE = """# Tool verification
which mcp-coder && mcp-coder --version
which claude && claude --version

# Environment setup
uv sync --extra dev

# Claude MCP verification
claude mcp list

# Run workflow
mcp-coder --log-level {log_level} {workflow_command}
"""
```

## HOW

### Integration Points

**Imports:**
```python
from ..utils.jenkins_operations.client import JenkinsClient
from ..utils.github_operations.issue_manager import IssueManager, IssueData
from ..utils.github_operations.issue_branch_manager import IssueBranchManager
```

**Usage in coordinator run:**
```python
def execute_coordinator_run(args: Namespace) -> int:
    # ... get eligible issues
    
    for issue in eligible_issues:
        # Find matching workflow
        current_label = [l for l in issue["labels"] if l in WORKFLOW_MAPPING][0]
        workflow_config = WORKFLOW_MAPPING[current_label]
        
        # Dispatch workflow
        try:
            dispatch_workflow(
                issue=issue,
                workflow_name=workflow_config["workflow"],
                repo_config=validated_config,
                jenkins_client=jenkins_client,
                issue_manager=issue_manager,
                branch_manager=branch_manager,
                log_level=args.log_level
            )
        except Exception as e:
            logger.error(f"Failed to dispatch workflow for issue #{issue['number']}: {e}")
            return 1  # Fail-fast
```

## ALGORITHM

```
1. Get workflow config from WORKFLOW_MAPPING using current label
2. Determine branch name:
   - If branch_strategy == "main" → use "main"
   - If branch_strategy == "from_issue" → get_linked_branches()[0]
     - If no linked branches → raise ValueError
3. Build workflow command string:
   - For create-plan: "create-plan {issue_number}"
   - For implement: "implement"
   - For create-pr: "create-pr"
4. Build full COMMAND using WORKFLOW_COMMAND_TEMPLATE
5. Build Jenkins job parameters dict
6. Trigger Jenkins job via client.start_job()
7. Verify job queued via client.get_job_status()
8. Update issue label: remove current_label, add next_label
9. Log success
```

## DATA

### Input: IssueData
```python
{
    "number": 123,
    "title": "Feature X",
    "labels": ["status-05:plan-ready", "enhancement"],
    # ... other fields
}
```

### Jenkins Job Parameters
```python
{
    "REPO_URL": "https://github.com/user/repo.git",
    "BRANCH_NAME": "123-feature-x",  # or "main" for create-plan
    "COMMAND": """# Tool verification
which mcp-coder && mcp-coder --version
which claude && claude --version

# Environment setup
uv sync --extra dev

# Claude MCP verification
claude mcp list

# Run workflow
mcp-coder --log-level INFO implement
""",
    "GITHUB_CREDENTIALS_ID": "github-pat"
}
```

### Label Updates
```python
# Before: ["status-05:plan-ready", "enhancement"]
# After:  ["status-06:implementing", "enhancement"]
```

## Implementation Notes

1. **Branch Resolution:**
   ```python
   if workflow_config["branch_strategy"] == "main":
       branch_name = "main"
   else:  # from_issue
       branches = branch_manager.get_linked_branches(issue["number"])
       if not branches:
           raise ValueError(f"No linked branch found for issue #{issue['number']}")
       branch_name = branches[0]
   ```

2. **Workflow Command Building:**
   ```python
   if workflow_config["workflow"] == "create-plan":
       workflow_cmd = f"create-plan {issue['number']}"
   elif workflow_config["workflow"] == "implement":
       workflow_cmd = "implement"
   else:  # create-pr
       workflow_cmd = "create-pr"
   ```

3. **Job Status Verification:**
   ```python
   queue_id = jenkins_client.start_job(executor_path, params)
   status = jenkins_client.get_job_status(queue_id)
   # If we get here without exception, job is queued/running
   ```

4. **Label Update (Atomic):**
   ```python
   # Remove old label first
   issue_manager.remove_labels(issue["number"], current_label)
   # Add new label
   issue_manager.add_labels(issue["number"], workflow_config["next_label"])
   ```

## LLM Prompt for Implementation

```
Implement Step 3 of the coordinator run feature as described in pr_info/steps/summary.md.

Task: Add workflow dispatcher to src/mcp_coder/cli/commands/coordinator.py

Requirements:
1. First add WORKFLOW_MAPPING and WORKFLOW_COMMAND_TEMPLATE constants after PRIORITY_ORDER

2. Write tests in tests/cli/commands/test_coordinator.py:
   - TestDispatchWorkflow class with 6 test methods
   - Mock JenkinsClient, IssueManager, IssueBranchManager
   - Test all three workflows (create-plan, implement, create-pr)
   - Test error cases (missing branch, Jenkins failure)
   - Test label updates

3. Then implement dispatch_workflow() function:
   - Determine branch name based on branch_strategy
   - Build workflow command string
   - Build full COMMAND using template
   - Trigger Jenkins job
   - Verify job status
   - Update issue labels
   - Handle errors appropriately

4. Run code quality checks:
   - mcp__code-checker__run_pytest_check (fast unit tests only)
   - mcp__code-checker__run_pylint_check
   - mcp__code-checker__run_mypy_check

Follow the exact algorithm and data structures in step_3.md.
Use existing JenkinsClient, IssueManager, IssueBranchManager APIs.
```

## Test Execution

**Run fast unit tests only:**
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"],
    show_details=False
)
```

## Success Criteria

- ✅ All 6 tests pass
- ✅ Correctly maps labels to workflows
- ✅ Resolves branch names per strategy
- ✅ Builds proper Jenkins parameters
- ✅ Triggers jobs and verifies status
- ✅ Updates labels correctly
- ✅ Error handling works (missing branch, Jenkins failures)
- ✅ Pylint/mypy checks pass
