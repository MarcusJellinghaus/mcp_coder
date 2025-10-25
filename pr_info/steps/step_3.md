# Step 3: CLI Command Core Logic (TDD)

## Overview
Implement the main command execution logic for `mcp-coder coordinator test`. This integrates config validation, Jenkins job triggering, and output formatting into a complete command handler.

## LLM Prompt
```
You are implementing Step 3 of the "mcp-coder coordinator test" feature.

Read pr_info/steps/summary.md for context.

Your task: Implement the main coordinator test command execution logic following TDD.

Requirements:
1. Write tests FIRST in tests/cli/commands/test_coordinator.py (extend existing)
2. Add execute_coordinator_test() to src/mcp_coder/cli/commands/coordinator.py
3. Ensure tests pass
4. Run code quality checks

Follow the specifications in this step file exactly.
```

## Phase 3A: Write Tests First (TDD)

### WHERE
File: `tests/cli/commands/test_coordinator.py` (EXTEND EXISTING)

Add new test class to existing file.

### WHAT
Add test class:

```python
class TestExecuteCoordinatorTest:
    """Tests for execute_coordinator_test command function."""
    
    def test_execute_coordinator_test_success() -> None:
        """Test successful command execution."""
        
    def test_execute_coordinator_test_creates_config_if_missing() -> None:
        """Test config file is auto-created on first run."""
        
    def test_execute_coordinator_test_repo_not_found() -> None:
        """Test error when repository not in config."""
        
    def test_execute_coordinator_test_incomplete_repo_config() -> None:
        """Test error when repository config incomplete."""
        
    def test_execute_coordinator_test_missing_jenkins_credentials() -> None:
        """Test error when Jenkins credentials missing."""
        
    def test_execute_coordinator_test_jenkins_api_error() -> None:
        """Test handling of Jenkins API errors."""
        
    def test_execute_coordinator_test_prints_output() -> None:
        """Test that job information is printed to stdout."""
        
    def test_execute_coordinator_test_with_job_url() -> None:
        """Test output when job URL immediately available."""
        
    def test_execute_coordinator_test_without_job_url() -> None:
        """Test output when job URL not yet available."""
```

### HOW
Integration points:
- Import `execute_coordinator_test` from `mcp_coder.cli.commands.coordinator`
- Mock `JenkinsClient` using `@patch`
- Mock `create_default_config` using `@patch`
- Mock `load_repo_config`, `get_jenkins_credentials` if needed
- Use `capsys` fixture to capture stdout
- Create mock `argparse.Namespace` for arguments

### ALGORITHM (Test Logic)
```
1. Create mock args with repo_name="test_repo", branch_name="feature-x"
2. Mock all dependencies (config, jenkins client, etc.)
3. Call execute_coordinator_test(args)
4. Assert return code is 0 for success, 1 for errors
5. Verify JenkinsClient.start_job() called with correct params
6. Capture and verify stdout output
```

### DATA

**execute_coordinator_test() signature**:
```python
def execute_coordinator_test(args: argparse.Namespace) -> int:
    """Execute coordinator test command.
    
    Args:
        args: Parsed arguments with repo_name and branch_name
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
```

**args.Namespace fields**:
- `repo_name: str` - Repository name (e.g., "mcp_coder")
- `branch_name: str` - Git branch to test (e.g., "feature-x")

**Return codes**:
- `0` - Success (job triggered)
- `1` - Error (missing config, validation failed, Jenkins error)

### Test Example Structure
```python
@patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
@patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
@patch("mcp_coder.cli.commands.coordinator.load_repo_config")
@patch("mcp_coder.cli.commands.coordinator.create_default_config")
def test_execute_coordinator_test_success(
    mock_create_config: MagicMock,
    mock_load_repo: MagicMock,
    mock_get_creds: MagicMock,
    mock_jenkins_class: MagicMock,
    capsys: pytest.CaptureFixture,
) -> None:
    """Test successful command execution."""
    # Setup
    args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")
    
    # Config already exists
    mock_create_config.return_value = False
    
    # Repo config is valid
    mock_load_repo.return_value = {
        "repo_url": "https://github.com/user/repo.git",
        "test_job_path": "MCP/test-job",
        "github_credentials_id": "github-pat",
    }
    
    # Jenkins credentials available
    mock_get_creds.return_value = ("http://jenkins:8080", "user", "token")
    
    # Mock Jenkins client
    mock_client = MagicMock()
    mock_jenkins_class.return_value = mock_client
    mock_client.start_job.return_value = 12345
    
    # Mock job status with URL
    from mcp_coder.utils.jenkins_operations.models import JobStatus
    mock_client.get_job_status.return_value = JobStatus(
        status="queued",
        build_number=None,
        duration_ms=None,
        url="https://jenkins:8080/queue/item/12345/",
    )
    
    # Execute
    result = execute_coordinator_test(args)
    
    # Verify
    assert result == 0
    
    # Verify JenkinsClient created with credentials
    mock_jenkins_class.assert_called_once_with(
        "http://jenkins:8080", "user", "token"
    )
    
    # Verify job started with correct params
    mock_client.start_job.assert_called_once_with(
        "MCP/test-job",
        {
            "REPO_URL": "https://github.com/user/repo.git",
            "BRANCH_NAME": "feature-x",
            "GITHUB_CREDENTIALS_ID": "github-pat",
        },
    )
    
    # Verify output printed
    captured = capsys.readouterr()
    assert "Job triggered: MCP/test-job - test - queue: 12345" in captured.out
    assert "https://jenkins:8080/queue/item/12345/" in captured.out
```

## Phase 3B: Implement Functionality

### WHERE
File: `src/mcp_coder/cli/commands/coordinator.py` (EXTEND EXISTING)

Add to existing file after helper functions.

### WHAT
Add main command function:

```python
def execute_coordinator_test(args: argparse.Namespace) -> int:
    """Execute coordinator test command.
    
    Args:
        args: Parsed command line arguments with:
            - repo_name: Repository name to test
            - branch_name: Git branch to test
            
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
```

### HOW
Integration points:
- Import `argparse` (already imported)
- Import `create_default_config` from `...utils.user_config`
- Import `JenkinsClient` (already imported)
- Import `JobStatus` from `...utils.jenkins_operations.models`
- Use helper functions from Step 2: `load_repo_config`, `validate_repo_config`, `get_jenkins_credentials`, `format_job_output`
- Print output using `print()` function

### ALGORITHM
```
1. Try to create default config (auto-create on first run)
2. Load repository config using load_repo_config()
3. Validate config using validate_repo_config()
4. Get Jenkins credentials using get_jenkins_credentials()
5. Create JenkinsClient with credentials
6. Build job parameters dict (REPO_URL, BRANCH_NAME, GITHUB_CREDENTIALS_ID)
7. Start Jenkins job, get queue_id
8. Call get_job_status() once to try to get URL
9. Format and print output using format_job_output()
10. Return 0 for success
11. Catch all exceptions, print error, return 1
```

### DATA

**Input** (args fields):
- `repo_name: str`
- `branch_name: str`

**Job parameters passed to Jenkins**:
```python
{
    "REPO_URL": str,              # From repo config
    "BRANCH_NAME": str,           # From args
    "GITHUB_CREDENTIALS_ID": str, # From repo config
}
```

**Output** (printed to stdout):
```
Job triggered: MCP_Coder/test-job - test - queue: 12345
https://jenkins.example.com/queue/item/12345/
```
or with build URL:
```
Job triggered: MCP_Coder/test-job - test - queue: 12345
https://jenkins.example.com/job/MCP_Coder/test-job/42/
```

**Return codes**:
- `0` - Job triggered successfully
- `1` - Any error (printed to stderr with full traceback per issue spec)

### Implementation Skeleton

```python
def execute_coordinator_test(args: argparse.Namespace) -> int:
    """Execute coordinator test command."""
    try:
        # Auto-create config on first run
        from ...utils.user_config import create_default_config
        
        created = create_default_config()
        if created:
            logger.info("Created default config file. Please update with your credentials.")
            print("Created default config file at ~/.mcp_coder/config.toml")
            print("Please update it with your Jenkins and repository information.")
            return 1  # Exit to let user configure
        
        # Load and validate repository config
        repo_config = load_repo_config(args.repo_name)
        validate_repo_config(args.repo_name, repo_config)
        
        # Get Jenkins credentials
        server_url, username, api_token = get_jenkins_credentials()
        
        # Create Jenkins client
        client = JenkinsClient(server_url, username, api_token)
        
        # Build job parameters
        params = {
            "REPO_URL": repo_config["repo_url"],
            "BRANCH_NAME": args.branch_name,
            "GITHUB_CREDENTIALS_ID": repo_config["github_credentials_id"],
        }
        
        # Start job
        queue_id = client.start_job(repo_config["test_job_path"], params)
        
        # Try to get job URL (may not be available immediately)
        try:
            status = client.get_job_status(queue_id)
            job_url = status.url
        except Exception as e:
            logger.debug(f"Could not get job status: {e}")
            job_url = None
        
        # Format and print output
        output = format_job_output(repo_config["test_job_path"], queue_id, job_url)
        print(output)
        
        return 0
        
    except ValueError as e:
        # User-facing errors (config issues)
        print(f"Error: {e}", file=sys.stderr)
        logger.error(f"Configuration error: {e}")
        return 1
        
    except Exception as e:
        # Let all other exceptions bubble up with full traceback
        # (per issue spec: "Let exceptions bubble up naturally for debugging")
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise
```

### Additional Imports Needed
Add to top of file:
```python
import sys
from ...utils.user_config import create_default_config
from ...utils.jenkins_operations.models import JobStatus
```

## Phase 3C: Verify Implementation

### Manual Verification Steps
1. Run tests: `pytest tests/cli/commands/test_coordinator.py::TestExecuteCoordinatorTest -v`
2. Verify all tests pass
3. Check test coverage

### Expected Test Output
```
tests/cli/commands/test_coordinator.py::TestExecuteCoordinatorTest::test_execute_coordinator_test_success PASSED
tests/cli/commands/test_coordinator.py::TestExecuteCoordinatorTest::test_execute_coordinator_test_creates_config_if_missing PASSED
tests/cli/commands/test_coordinator.py::TestExecuteCoordinatorTest::test_execute_coordinator_test_repo_not_found PASSED
tests/cli/commands/test_coordinator.py::TestExecuteCoordinatorTest::test_execute_coordinator_test_incomplete_repo_config PASSED
tests/cli/commands/test_coordinator.py::TestExecuteCoordinatorTest::test_execute_coordinator_test_missing_jenkins_credentials PASSED
tests/cli/commands/test_coordinator.py::TestExecuteCoordinatorTest::test_execute_coordinator_test_jenkins_api_error PASSED
tests/cli/commands/test_coordinator.py::TestExecuteCoordinatorTest::test_execute_coordinator_test_prints_output PASSED
tests/cli/commands/test_coordinator.py::TestExecuteCoordinatorTest::test_execute_coordinator_test_with_job_url PASSED
tests/cli/commands/test_coordinator.py::TestExecuteCoordinatorTest::test_execute_coordinator_test_without_job_url PASSED

9 passed
```

## Phase 3D: Code Quality Checks

Run mandatory code quality checks:

```python
# Pylint
mcp__code-checker__run_pylint_check()

# Pytest (fast unit tests)
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not jenkins_integration and not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)

# Mypy
mcp__code-checker__run_mypy_check()
```

All checks must pass before proceeding to Step 4.

## Success Criteria

- ✅ All 9 new tests pass (total ~24 tests in file)
- ✅ Config auto-created on first run
- ✅ Repository config loaded and validated
- ✅ Jenkins credentials loaded with env var priority
- ✅ Jenkins job triggered with correct parameters
- ✅ Job status queried once for URL
- ✅ Output formatted and printed correctly
- ✅ Exit code 0 on success, 1 on user errors
- ✅ Exceptions bubble up for system errors (per spec)
- ✅ Pylint: No errors
- ✅ Pytest: All tests pass
- ✅ Mypy: No type errors

## Files Modified

### Extended:
- `tests/cli/commands/test_coordinator.py` - Add `TestExecuteCoordinatorTest` class (~120-150 lines)
- `src/mcp_coder/cli/commands/coordinator.py` - Add `execute_coordinator_test()` (~60-80 lines)

### Total New Lines: ~180-230 lines

## Next Step
After all checks pass, proceed to **Step 4: CLI Integration**.
