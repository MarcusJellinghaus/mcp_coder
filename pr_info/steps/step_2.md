# Step 2: Update CLI Argument Parsing

## LLM Prompt
```
You are implementing Step 2 of the execution-dir feature.

Reference documents:
- Summary: pr_info/steps/summary.md
- Previous step: pr_info/steps/step_1.md (completed)
- This step: pr_info/steps/step_2.md

Task: Add --execution-dir argument to CLI parsers for all affected commands.

Follow Test-Driven Development:
1. Read this step document completely
2. Update tests first
3. Add CLI arguments
4. Verify all tests pass

Apply KISS principle - keep argument definitions consistent across commands.
```

## Objective
Add `--execution-dir` CLI argument to all commands that invoke Claude (prompt, commit auto, implement, create-plan, create-pr).

## WHERE
**Modified file:**
- File: `src/mcp_coder/cli/main.py`
- Function: `create_parser()`
- Affected parsers: `prompt_parser`, `auto_parser`, `implement_parser`, `create_plan_parser`, `create_pr_parser`

**Test file:**
- File: `tests/cli/test_main.py`
- Test class: `TestExecutionDirArgument` (new)

## WHAT

### Argument Specification
Add this argument to each affected command parser:

```python
parser.add_argument(
    "--execution-dir",
    type=str,
    default=None,
    help="Working directory for Claude subprocess (default: current directory)",
)
```

### Commands to Update
1. `prompt` command
2. `commit auto` command  
3. `implement` command
4. `create-plan` command
5. `create-pr` command

## HOW

### Integration Points

**In `create_parser()` function:**
```python
def create_parser() -> argparse.ArgumentParser:
    # ... existing code ...
    
    # For prompt command
    prompt_parser = subparsers.add_parser("prompt", ...)
    # ... existing arguments ...
    prompt_parser.add_argument("--execution-dir", ...)  # ADD THIS
    
    # For commit auto command
    auto_parser = commit_subparsers.add_parser("auto", ...)
    # ... existing arguments ...
    auto_parser.add_argument("--execution-dir", ...)  # ADD THIS
    
    # Repeat for implement, create-plan, create-pr
```

## ALGORITHM

```
FOR EACH command_parser IN [prompt, auto, implement, create_plan, create_pr]:
    ADD argument "--execution-dir":
        type = str
        default = None
        help = "Working directory for Claude subprocess (default: current directory)"
```

## DATA

### Input Parsing
After parsing, `args` namespace will contain:
```python
args.execution_dir: str | None
# None → Use current working directory (default)
# str → Use specified directory
```

### Validation
- Path validation happens in command handlers (next steps)
- CLI parser only captures the argument value

## Test Requirements

### Test Cases
1. **Test default None value** → When flag not provided
2. **Test explicit path** → When `--execution-dir /path` provided
3. **Test with relative path** → When `--execution-dir ./subdir` provided
4. **Test with each command** → Verify all 5 commands accept the flag
5. **Test help text** → Verify help shows the flag

### Test Structure
```python
class TestExecutionDirArgument:
    """Tests for --execution-dir CLI argument."""
    
    def test_execution_dir_defaults_to_none(self):
        """--execution-dir should default to None when not specified."""
        
    def test_execution_dir_accepts_absolute_path(self):
        """--execution-dir should accept absolute paths."""
        
    def test_execution_dir_accepts_relative_path(self):
        """--execution-dir should accept relative paths."""
        
    def test_execution_dir_on_prompt_command(self):
        """Verify --execution-dir works with prompt command."""
        
    def test_execution_dir_on_commit_auto(self):
        """Verify --execution-dir works with commit auto command."""
        
    def test_execution_dir_on_implement(self):
        """Verify --execution-dir works with implement command."""
        
    def test_execution_dir_on_create_plan(self):
        """Verify --execution-dir works with create-plan command."""
        
    def test_execution_dir_on_create_pr(self):
        """Verify --execution-dir works with create-pr command."""
```

## Implementation Notes

### KISS Principles Applied
- Identical argument definition across all commands
- Simple string type (validation in handlers)
- Clear, concise help text
- No complex parsing logic

### Why This Design
1. **Consistency**: Same argument name and behavior everywhere
2. **Discoverability**: Appears in `--help` for each command
3. **Flexibility**: Accepts both absolute and relative paths
4. **Optional**: Default None = use CWD (intuitive)

### Affected Commands Context
Each command that invokes Claude needs this flag because:
- `prompt`: Direct Claude interaction
- `commit auto`: Uses LLM to generate commit message
- `implement`: Runs implementation workflow with LLM
- `create-plan`: Generates implementation plan via LLM
- `create-pr`: Creates PR summary via LLM

## Verification Steps
1. Run tests: `pytest tests/cli/test_main.py::TestExecutionDirArgument -v`
2. Verify all 8 test cases pass
3. Test help output: `mcp-coder prompt --help` (should show --execution-dir)
4. Run existing CLI tests: `pytest tests/cli/test_main.py -v`
5. Run mypy: `mypy src/mcp_coder/cli/main.py`

## Dependencies
- Standard library: `argparse`
- No new dependencies

## Estimated Complexity
- Lines of code: ~20 lines (5 commands × 4 lines each)
- Test lines: ~100 lines
- Complexity: Low (repetitive argument addition)

## Example Usage After Implementation
```bash
# Default behavior - Claude runs in current directory
mcp-coder prompt "Hello" --project-dir /path/to/project

# Explicit execution directory
mcp-coder prompt "Hello" --project-dir /path/to/project --execution-dir /workspace

# Relative execution directory
mcp-coder implement --project-dir /path/to/project --execution-dir ./local
```
