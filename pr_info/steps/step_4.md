# Step 4: Main Coordinator Runner (TDD)

## Reference
**Implementation Plan:** See `pr_info/steps/summary.md` for complete architectural overview.

## Objective
Implement main coordinator run orchestration logic that processes repositories and dispatches workflows.

## WHERE

**Test File:**
- `tests/cli/commands/test_coordinator.py`
- Add new test class: `TestExecuteCoordinatorRun`

**Implementation File:**
- `src/mcp_coder/cli/commands/coordinator.py`
- Add function after `dispatch_workflow()`

## WHAT

### Test Class (TDD First)

```python
class TestExecuteCoordinatorRun:
    """Tests for execute_coordinator_run function."""
    
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_creates_config_if_missing() -> None:
        """Test config auto-creation on first run."""
        # Mock create_default_config() returns True
        # Verify exit code 1
        # Verify helpful message printed
        
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.get_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.dispatch_workflow")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_single_repo_success() -> None:
        """Test successful execution for single repository."""
        # Mock --repo mcp_coder
        # Mock 2 eligible issues
        # Verify dispatch_workflow called twice
        # Verify exit code 0
        
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.get_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_no_eligible_issues() -> None:
        """Test handling when no eligible issues found."""
        # Mock get_eligible_issues returns []
        # Verify exit code 0 (success, nothing to do)
        # Verify log message about no issues
        
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_missing_repo_config() -> None:
        """Test error when repository not in config."""
        # Mock load_repo_config returns all None values
        # Verify exit code 1
        # Verify error message printed
        
    @patch("mcp_coder.cli.commands.coordinator.dispatch_workflow")
    @patch("mcp_coder.cli.commands.coordinator.get_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_dispatch_failure_fail_fast() -> None:
        """Test fail-fast on dispatch error."""
        # Mock 3 eligible issues
        # Mock dispatch_workflow raises ValueError on 2nd issue
        # Verify only 1 dispatch attempted
        # Verify exit code 1
        
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_requires_all_or_repo() -> None:
        """Test error when neither --all nor --repo specified."""
        # Mock args without all or repo
        # Verify exit code 1
        # Verify error message about required argument
```

### Main Function Signature

```python
def execute_coordinator_run(args: argparse.Namespace) -> int:
    """Execute coordinator run command.
    
    Args:
        args: Parsed command line arguments with:
            - all: Process all repositories (bool)
            - repo: Single repository name (str, optional)
            - log_level: Logging level (str)
            
    Returns:
        int: Exit code (0 for success, 1 for error)
        
    Raises:
        Exception: Any unexpected errors (not caught, let bubble up)
    """
```

## HOW

### Integration Points

**Imports:**
```python
from pathlib import Path
from ..utils.github_operations.issue_manager import IssueManager
from ..utils.github_operations.issue_branch_manager import IssueBranchManager
```

**CLI Argument Parser (in main.py - Step 5):**
```python
# coordinator run command
run_parser = coordinator_subparsers.add_parser(
    "run", help="Monitor and dispatch workflows for GitHub issues"
)
run_group = run_parser.add_mutually_exclusive_group(required=True)
run_group.add_argument("--all", action="store_true", help="Process all repositories")
run_group.add_argument("--repo", type=str, help="Process single repository")
```

**Usage in CLI:**
```python
# In cli/main.py
elif args.command == "coordinator":
    if args.coordinator_subcommand == "test":
        return execute_coordinator_test(args)
    elif args.coordinator_subcommand == "run":
        return execute_coordinator_run(args)
```

## ALGORITHM

```
1. Check if config exists → create if missing, exit for user to configure
2. Validate args: must have --all XOR --repo (enforced by argparse)
3. Determine repo list:
   - If --all: get all repos from config (coordinator.repos.*)
   - If --repo: use single repo name
4. Get Jenkins credentials
5. For each repository:
   a. Load repo config and validate
   b. Create managers: JenkinsClient, IssueManager, IssueBranchManager
   c. Get eligible issues
   d. If no issues: log and continue to next repo
   e. For each eligible issue:
      - Find current bot_pickup label
      - Get workflow config from WORKFLOW_MAPPING
      - Dispatch workflow
      - If error: log and exit 1 (fail-fast)
6. Return 0 (success)
```

## DATA

### Input: Command Line Args
```python
# Single repo mode
args = Namespace(
    command="coordinator",
    coordinator_subcommand="run",
    repo="mcp_coder",
    all=False,
    log_level="INFO"
)

# All repos mode
args = Namespace(
    command="coordinator",
    coordinator_subcommand="run",
    all=True,
    repo=None,
    log_level="DEBUG"
)
```

### Repository List Extraction (--all mode)
```python
# From config.toml:
# [coordinator.repos.mcp_coder]
# ...
# [coordinator.repos.other_repo]
# ...

# Extract repo names:
repo_names = ["mcp_coder", "other_repo"]
```

### Processing Flow
```python
# For repo "mcp_coder":
repo_config = {
    "repo_url": "https://github.com/user/mcp_coder.git",
    "executor_test_path": "MCP_Coder/execute_job",
    "github_credentials_id": "github-pat"
}

eligible_issues = [
    IssueData(number=124, labels=["status-08:ready-pr"]),
    IssueData(number=123, labels=["status-05:plan-ready"])
]

# Dispatch workflow for #124 (create-pr)
# Dispatch workflow for #123 (implement)
# → Success, continue to next repo
```

## Implementation Notes

1. **Config Auto-Creation:**
   ```python
   created = create_default_config()
   if created:
       config_path = get_config_file_path()
       print(f"Created default config file at {config_path}")
       print("Please update it with your Jenkins and repository information.")
       return 1
   ```

2. **Repository List Extraction (--all mode):**
   ```python
   # Read config file and extract all [coordinator.repos.*] sections
   # Use get_config_value() or read TOML directly
   import tomli
   config_path = get_config_file_path()
   with open(config_path, "rb") as f:
       config_data = tomli.load(f)
   
   repos_section = config_data.get("coordinator", {}).get("repos", {})
   repo_names = list(repos_section.keys())
   ```

3. **Manager Initialization:**
   ```python
   # Create project_dir Path from repo URL (use current dir as placeholder)
   project_dir = Path.cwd()  # Or extract from config
   
   issue_manager = IssueManager(project_dir)
   branch_manager = IssueBranchManager(project_dir)
   jenkins_client = JenkinsClient(server_url, username, api_token)
   ```

4. **Error Handling (Fail-Fast):**
   ```python
   for issue in eligible_issues:
       try:
           current_label = next(l for l in issue["labels"] if l in WORKFLOW_MAPPING)
           workflow_config = WORKFLOW_MAPPING[current_label]
           
           dispatch_workflow(
               issue, workflow_config["workflow"], 
               validated_config, jenkins_client, 
               issue_manager, branch_manager, args.log_level
           )
       except Exception as e:
           logger.error(f"Failed processing issue #{issue['number']}: {e}")
           print(f"Error: Failed to process issue #{issue['number']}: {e}", file=sys.stderr)
           return 1  # Fail-fast
   ```

5. **Logging:**
   ```python
   logger.info(f"Processing repository: {repo_name}")
   logger.info(f"Found {len(eligible_issues)} eligible issues")
   logger.info(f"Successfully processed all issues in {repo_name}")
   ```

## LLM Prompt for Implementation

```
Implement Step 4 of the coordinator run feature as described in pr_info/steps/summary.md.

Task: Add main coordinator runner to src/mcp_coder/cli/commands/coordinator.py

Requirements:
1. Write tests in tests/cli/commands/test_coordinator.py:
   - TestExecuteCoordinatorRun class with 6 test methods
   - Test single repo, all repos, no issues, errors, fail-fast
   - Mock all dependencies (config, Jenkins, GitHub, dispatch)

2. Then implement execute_coordinator_run() function:
   - Auto-create config if missing
   - Validate --all XOR --repo requirement
   - Extract repository list (single or all from config)
   - Load Jenkins credentials
   - For each repository:
     * Load and validate repo config
     * Create managers (Jenkins, Issue, Branch)
     * Get eligible issues
     * Dispatch workflows with fail-fast error handling
   - Return appropriate exit codes

3. Run code quality checks:
   - mcp__code-checker__run_pytest_check (fast unit tests only)
   - mcp__code-checker__run_pylint_check
   - mcp__code-checker__run_mypy_check

Follow the exact algorithm in step_4.md.
Reuse existing patterns from execute_coordinator_test().
Handle errors with fail-fast approach (exit 1 on first error).
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
- ✅ Auto-creates config on first run
- ✅ Validates --all XOR --repo requirement
- ✅ Processes single repo correctly
- ✅ Processes all repos correctly
- ✅ Handles no eligible issues gracefully
- ✅ Fail-fast on first error
- ✅ Proper logging and error messages
- ✅ Pylint/mypy checks pass
