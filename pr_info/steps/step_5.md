# Step 5: CLI Integration

## Reference
**Implementation Plan:** See `pr_info/steps/summary.md` for complete architectural overview.

## Objective
Wire up `coordinator run` command in CLI parser and routing logic.

## WHERE

**Test File:**
- `tests/cli/test_main.py`
- Add tests to existing test class or create new `TestCoordinatorRunCommand`

**Implementation Files:**
1. `src/mcp_coder/cli/main.py` - Add command routing
2. `tests/cli/commands/test_coordinator.py` - Add CLI argument validation tests

## WHAT

### Test Cases

```python
class TestCoordinatorRunCommand:
    """Tests for coordinator run CLI integration."""
    
    @patch("mcp_coder.cli.main.execute_coordinator_run")
    def test_coordinator_run_with_repo_argument() -> None:
        """Test CLI routing for --repo mode."""
        # Parse args: coordinator run --repo mcp_coder
        # Verify execute_coordinator_run called with correct args
        
    @patch("mcp_coder.cli.main.execute_coordinator_run")
    def test_coordinator_run_with_all_argument() -> None:
        """Test CLI routing for --all mode."""
        # Parse args: coordinator run --all
        # Verify execute_coordinator_run called with correct args
        
    @patch("mcp_coder.cli.main.execute_coordinator_run")
    def test_coordinator_run_with_log_level() -> None:
        """Test log level pass-through."""
        # Parse args: coordinator run --repo mcp_coder --log-level DEBUG
        # Verify args.log_level == "DEBUG"
        
    def test_coordinator_run_requires_all_or_repo() -> None:
        """Test error when neither --all nor --repo provided."""
        # Parse args: coordinator run (no --all or --repo)
        # Verify argparse raises error
        
    def test_coordinator_run_all_and_repo_mutually_exclusive() -> None:
        """Test error when both --all and --repo provided."""
        # Parse args: coordinator run --all --repo mcp_coder
        # Verify argparse raises error
```

### CLI Changes

**In `src/mcp_coder/cli/main.py`:**

1. **Add import:**
```python
from .commands.coordinator import execute_coordinator_test, execute_coordinator_run
```

2. **Add subcommand parser in `create_parser()`:**
```python
# coordinator run command
run_parser = coordinator_subparsers.add_parser(
    "run", 
    help="Monitor and dispatch workflows for GitHub issues"
)

# Mutually exclusive group: --all OR --repo (one required)
run_group = run_parser.add_mutually_exclusive_group(required=True)
run_group.add_argument(
    "--all",
    action="store_true",
    help="Process all repositories from config"
)
run_group.add_argument(
    "--repo",
    type=str,
    metavar="NAME",
    help="Process single repository (e.g., mcp_coder)"
)
```

3. **Add routing in `main()`:**
```python
elif args.command == "coordinator":
    if hasattr(args, "coordinator_subcommand"):
        if args.coordinator_subcommand == "test":
            return execute_coordinator_test(args)
        elif args.coordinator_subcommand == "run":
            return execute_coordinator_run(args)
        else:
            logger.error(f"Unknown coordinator subcommand: {args.coordinator_subcommand}")
            print(f"Error: Unknown coordinator subcommand '{args.coordinator_subcommand}'")
            return 1
    else:
        logger.error("Coordinator subcommand required")
        print("Error: Please specify a coordinator subcommand (e.g., 'test', 'run')")
        return 1
```

## HOW

### Integration Points

**Existing Pattern:**
The `coordinator test` command already exists with similar structure:
```python
# coordinator test command
test_parser = coordinator_subparsers.add_parser(
    "test", help="Trigger Jenkins integration test for repository"
)
test_parser.add_argument("repo_name", ...)
test_parser.add_argument("--branch-name", required=True, ...)
```

**New Pattern (coordinator run):**
```python
# coordinator run command
run_parser = coordinator_subparsers.add_parser(
    "run", help="Monitor and dispatch workflows for GitHub issues"
)
run_group = run_parser.add_mutually_exclusive_group(required=True)
run_group.add_argument("--all", action="store_true", ...)
run_group.add_argument("--repo", type=str, ...)
```

### Command Line Examples

**Valid usage:**
```bash
# Process all repositories
mcp-coder coordinator run --all

# Process single repository
mcp-coder coordinator run --repo mcp_coder

# With custom log level
mcp-coder coordinator run --repo mcp_coder --log-level DEBUG
mcp-coder --log-level DEBUG coordinator run --all
```

**Invalid usage (argparse will error):**
```bash
# Missing required argument
mcp-coder coordinator run
# Error: one of the arguments --all --repo is required

# Both arguments provided
mcp-coder coordinator run --all --repo mcp_coder
# Error: argument --repo: not allowed with argument --all
```

## ALGORITHM

```
1. Add import for execute_coordinator_run in main.py
2. In create_parser():
   - Add coordinator run subparser
   - Add mutually exclusive group (--all | --repo)
   - Set required=True on group
3. In main():
   - Add elif branch for coordinator_subcommand == "run"
   - Call execute_coordinator_run(args)
   - Return exit code
4. Write tests for CLI routing
5. Run code quality checks
```

## DATA

### Parsed Arguments (--repo mode)
```python
Namespace(
    command="coordinator",
    coordinator_subcommand="run",
    all=False,
    repo="mcp_coder",
    log_level="INFO"
)
```

### Parsed Arguments (--all mode)
```python
Namespace(
    command="coordinator",
    coordinator_subcommand="run",
    all=True,
    repo=None,
    log_level="DEBUG"
)
```

## Implementation Notes

1. **Mutually Exclusive Group:**
   - `required=True` ensures one argument is provided
   - `add_mutually_exclusive_group()` prevents both from being used together
   - Argparse handles validation automatically

2. **Existing Coordinator Parser:**
   ```python
   # Already exists in main.py
   coordinator_parser = subparsers.add_parser(
       "coordinator", help="Coordinator commands for repository testing"
   )
   coordinator_subparsers = coordinator_parser.add_subparsers(
       dest="coordinator_subcommand",
       help="Available coordinator commands",
       metavar="SUBCOMMAND",
   )
   
   # Add run subparser to existing coordinator_subparsers
   run_parser = coordinator_subparsers.add_parser("run", ...)
   ```

3. **Log Level Inheritance:**
   - Main parser has `--log-level` argument
   - Automatically available in args for all subcommands
   - Pass through to execute_coordinator_run via `args.log_level`

4. **Testing Strategy:**
   - Test CLI routing in `tests/cli/test_main.py`
   - Test argument validation in `tests/cli/commands/test_coordinator.py`
   - Mock execute_coordinator_run to verify it's called correctly

## LLM Prompt for Implementation

```
Implement Step 5 of the coordinator run feature as described in pr_info/steps/summary.md.

Task: Wire up coordinator run command in CLI

Requirements:
1. Modify src/mcp_coder/cli/main.py:
   - Import execute_coordinator_run
   - Add coordinator run subparser in create_parser()
   - Add mutually exclusive group (--all | --repo, required)
   - Add routing in main() function
   
2. Write tests in tests/cli/test_main.py or tests/cli/commands/test_coordinator.py:
   - Test CLI routing for --repo mode
   - Test CLI routing for --all mode
   - Test log level pass-through
   - Test argparse validates mutually exclusive requirement
   
3. Manual verification:
   - Run: mcp-coder coordinator run --help
   - Verify help text shows --all and --repo options
   - Verify mutual exclusion works
   
4. Run code quality checks:
   - mcp__code-checker__run_pytest_check (fast unit tests only)
   - mcp__code-checker__run_pylint_check
   - mcp__code-checker__run_mypy_check

Follow the exact integration points in step_5.md.
Reuse existing coordinator parser structure.
```

## Test Execution

**Run fast unit tests only:**
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"],
    show_details=False
)
```

**Manual CLI test:**
```bash
# Check help text
mcp-coder coordinator run --help

# Test validation (should error)
mcp-coder coordinator run
mcp-coder coordinator run --all --repo mcp_coder

# Test routing (should fail with config error if not set up)
mcp-coder coordinator run --repo mcp_coder
```

## Success Criteria

- ✅ All 5 tests pass
- ✅ CLI routes to execute_coordinator_run correctly
- ✅ Argparse validates --all XOR --repo requirement
- ✅ Log level passed through correctly
- ✅ Help text shows correct options
- ✅ Manual CLI test works
- ✅ Pylint/mypy checks pass
