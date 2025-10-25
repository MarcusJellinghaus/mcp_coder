# Step 4: CLI Integration (TDD)

## Overview
Integrate the coordinator test command into the main CLI by adding argument parsing and command routing. This makes the command accessible via `mcp-coder coordinator test`.

## LLM Prompt
```
You are implementing Step 4 of the "mcp-coder coordinator test" feature.

Read pr_info/steps/summary.md for context.

Your task: Integrate coordinator command into main CLI following TDD.

Requirements:
1. Write tests FIRST in tests/cli/test_main.py (extend existing)
2. Update src/mcp_coder/cli/main.py with coordinator subparser
3. Ensure tests pass
4. Run code quality checks

Follow the specifications in this step file exactly.
```

## Phase 4A: Write Tests First (TDD)

### WHERE
File: `tests/cli/test_main.py` (EXTEND EXISTING)

Add new test class to existing file.

### WHAT
Add test class for CLI integration:

```python
class TestCoordinatorCommand:
    """Tests for coordinator command CLI integration."""
    
    def test_coordinator_test_command_parsing() -> None:
        """Test that coordinator test command is parsed correctly."""
        
    def test_coordinator_test_requires_branch_name() -> None:
        """Test that --branch-name is required."""
        
    def test_coordinator_test_executes_handler() -> None:
        """Test that coordinator test calls execute_coordinator_test."""
        
    def test_coordinator_test_with_log_level() -> None:
        """Test coordinator test respects --log-level flag."""
        
    def test_coordinator_no_subcommand_shows_error() -> None:
        """Test that coordinator without subcommand shows error."""
```

### HOW
Integration points:
- Import test utilities from existing test file
- Mock `execute_coordinator_test` using `@patch`
- Use `create_parser()` from `main.py` to test argument parsing
- Test both successful parsing and error cases

### ALGORITHM (Test Logic)
```
1. Create parser using create_parser()
2. Parse test args: ["coordinator", "test", "repo_name", "--branch-name", "feature-x"]
3. Assert args.command == "coordinator"
4. Assert args.coordinator_subcommand == "test"
5. Assert args.repo_name == "repo_name"
6. Assert args.branch_name == "feature-x"
7. Mock execute_coordinator_test and call main()
8. Verify execute_coordinator_test was called with correct args
```

### DATA

**CLI syntax**:
```bash
mcp-coder coordinator test <repo_name> --branch-name <branch> [--log-level LEVEL]
```

**Parsed args should have**:
- `command: str` = "coordinator"
- `coordinator_subcommand: str` = "test"
- `repo_name: str` - positional argument
- `branch_name: str` - required option
- `log_level: str` - optional (default "INFO")

### Test Example Structure
```python
def test_coordinator_test_command_parsing() -> None:
    """Test that coordinator test command is parsed correctly."""
    # Setup
    from mcp_coder.cli.main import create_parser
    
    parser = create_parser()
    
    # Execute
    args = parser.parse_args([
        "coordinator", "test", "mcp_coder",
        "--branch-name", "feature-x"
    ])
    
    # Verify
    assert args.command == "coordinator"
    assert args.coordinator_subcommand == "test"
    assert args.repo_name == "mcp_coder"
    assert args.branch_name == "feature-x"
    assert args.log_level == "INFO"  # default


@patch("mcp_coder.cli.main.execute_coordinator_test")
def test_coordinator_test_executes_handler(
    mock_execute: MagicMock
) -> None:
    """Test that coordinator test calls execute_coordinator_test."""
    # Setup
    mock_execute.return_value = 0
    
    # Execute
    with patch("sys.argv", [
        "mcp-coder", "coordinator", "test", "mcp_coder",
        "--branch-name", "feature-x"
    ]):
        from mcp_coder.cli.main import main
        result = main()
    
    # Verify
    assert result == 0
    mock_execute.assert_called_once()
    
    # Check args passed to handler
    call_args = mock_execute.call_args[0][0]
    assert call_args.repo_name == "mcp_coder"
    assert call_args.branch_name == "feature-x"
```

## Phase 4B: Implement Functionality

### WHERE
File: `src/mcp_coder/cli/main.py` (MODIFY EXISTING)

Modify in two places:
1. Add import at top
2. Add coordinator subparser in `create_parser()`
3. Add routing in `main()`

### WHAT

**Add import** (after existing command imports):
```python
from .commands.coordinator import execute_coordinator_test
```

**Add to create_parser()** (after create-pr parser):
```python
# Coordinator commands - Jenkins-based integration testing
coordinator_parser = subparsers.add_parser(
    "coordinator", 
    help="Coordinator commands for repository testing"
)
coordinator_subparsers = coordinator_parser.add_subparsers(
    dest="coordinator_subcommand",
    help="Available coordinator commands",
    metavar="SUBCOMMAND",
)

# coordinator test command
test_parser = coordinator_subparsers.add_parser(
    "test",
    help="Trigger Jenkins integration test for repository"
)
test_parser.add_argument(
    "repo_name",
    help="Repository name from config (e.g., mcp_coder)"
)
test_parser.add_argument(
    "--branch-name",
    required=True,
    help="Git branch to test (e.g., feature-x, main)"
)
```

**Add to main()** (after create-pr routing):
```python
elif args.command == "coordinator":
    if hasattr(args, "coordinator_subcommand") and args.coordinator_subcommand == "test":
        return execute_coordinator_test(args)
    else:
        logger.error("Coordinator subcommand required")
        print("Error: Please specify a coordinator subcommand (e.g., 'test')")
        return 1
```

### HOW
Integration points:
- Import `execute_coordinator_test` from `.commands.coordinator`
- Add coordinator parser to existing `create_parser()` function
- Add coordinator routing to existing `main()` function
- Follow existing command pattern (similar to create-pr)

### ALGORITHM
```
1. In create_parser(): Create coordinator parent parser
2. Create subparsers for coordinator (test, future commands)
3. Create test subparser with repo_name (positional) and --branch-name (required)
4. In main(): Check if command == "coordinator"
5. Check coordinator_subcommand == "test"
6. Call execute_coordinator_test(args) and return result
```

### DATA

**Parser structure**:
```
mcp-coder
├── coordinator
│   └── test <repo_name> --branch-name <branch>
├── create-pr
├── implement
└── ...
```

**args after parsing**:
```python
Namespace(
    command="coordinator",
    coordinator_subcommand="test",
    repo_name="mcp_coder",
    branch_name="feature-x",
    log_level="INFO"  # inherited from parent parser
)
```

### Implementation Details

**Location in create_parser()**: Add after create-pr parser (around line 130-140)

**Location in main()**: Add after create-pr routing (around line 210-220)

**Pattern to follow**: Look at existing create-pr implementation as reference

## Phase 4C: Verify Implementation

### Manual Verification Steps
1. Run tests: `pytest tests/cli/test_main.py::TestCoordinatorCommand -v`
2. Verify all tests pass
3. Test manually from command line (with mocked config):
   ```bash
   mcp-coder coordinator test mcp_coder --branch-name feature-x
   ```

### Expected Test Output
```
tests/cli/test_main.py::TestCoordinatorCommand::test_coordinator_test_command_parsing PASSED
tests/cli/test_main.py::TestCoordinatorCommand::test_coordinator_test_requires_branch_name PASSED
tests/cli/test_main.py::TestCoordinatorCommand::test_coordinator_test_executes_handler PASSED
tests/cli/test_main.py::TestCoordinatorCommand::test_coordinator_test_with_log_level PASSED
tests/cli/test_main.py::TestCoordinatorCommand::test_coordinator_no_subcommand_shows_error PASSED

5 passed
```

### Manual CLI Test
```bash
# Should show help
$ mcp-coder coordinator --help

# Should show error (missing --branch-name)
$ mcp-coder coordinator test mcp_coder

# Should work (assuming config exists)
$ mcp-coder coordinator test mcp_coder --branch-name feature-x
```

## Phase 4D: Code Quality Checks

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

All checks must pass before proceeding to Step 5.

## Success Criteria

- ✅ All 5 CLI integration tests pass
- ✅ Command parsing works correctly
- ✅ --branch-name is required
- ✅ --log-level is optional (inherited from parent)
- ✅ execute_coordinator_test is called with correct args
- ✅ Error shown when subcommand missing
- ✅ Manual CLI test works
- ✅ Help text shows coordinator command
- ✅ Pylint: No errors
- ✅ Pytest: All tests pass
- ✅ Mypy: No type errors

## Files Modified

### Modified:
- `tests/cli/test_main.py` - Add `TestCoordinatorCommand` class (~80-100 lines)
- `src/mcp_coder/cli/main.py` - Add coordinator parser and routing (~25-30 lines)

### Total New Lines: ~105-130 lines

## End-to-End CLI Flow

After this step, the complete flow is:

```bash
$ mcp-coder coordinator test mcp_coder --branch-name feature-x
```

1. CLI parser parses arguments
2. main() routes to execute_coordinator_test()
3. execute_coordinator_test() loads config
4. Validates repository config
5. Gets Jenkins credentials
6. Triggers Jenkins job
7. Prints output with URL
8. Returns exit code 0

## Next Step
After all checks pass, proceed to **Step 5: Documentation & Integration Tests**.
