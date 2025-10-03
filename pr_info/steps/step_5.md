# Step 5: Implement CLI Command Interface with Tests

## Objective
Create the CLI command interface that integrates the implement workflow into the main CLI system.

## LLM Prompt
```
Implement Step 5 from the summary (pr_info/steps/summary.md): Create CLI command interface with comprehensive tests.

Create CLI integration following existing patterns from src/mcp_coder/cli/commands/commit.py:
- tests/cli/commands/test_implement.py (test-first approach)
- src/mcp_coder/cli/commands/implement.py
- Update src/mcp_coder/cli/main.py and commands/__init__.py

Mock the core workflow module. Follow existing CLI patterns for argument parsing and error handling.

Reference the summary document for architecture and ensure CLI integration matches existing commands.
```

## Implementation Details

### WHERE
- `tests/cli/commands/test_implement.py`
- `src/mcp_coder/cli/commands/implement.py`
- `src/mcp_coder/cli/main.py` (modify)
- `src/mcp_coder/cli/commands/__init__.py` (modify)

### WHAT
**Main functions:**
```python
def execute_implement(args: argparse.Namespace) -> int
def add_implement_parser(subparsers) -> None
```

### HOW
- Follow patterns from `execute_commit_auto`
- Add CLI argument parsing for `--project-dir`, `--log-level`, `--llm-method`
- Mock `run_implement_workflow` in tests
- Update main CLI router

### ALGORITHM
```
1. Test-first: Mock workflow module in CLI tests
2. Create CLI command following existing patterns
3. Add argument parser with same options as original script
4. Update main CLI to route implement command
5. Export command in __init__.py
```

### DATA
**Arguments:**
- `--project-dir` (optional Path)
- `--log-level` (DEBUG|INFO|WARNING|ERROR|CRITICAL)
- `--llm-method` (claude_code_cli|claude_code_api)

**Return:** `int` exit code

## Files Created/Modified
- `tests/cli/commands/test_implement.py`
- `src/mcp_coder/cli/commands/implement.py`
- `src/mcp_coder/cli/main.py` (add implement command)
- `src/mcp_coder/cli/commands/__init__.py` (export implement)

## Success Criteria
- CLI command `mcp-coder implement --help` works
- All CLI arguments properly parsed and validated
- Integration with existing CLI infrastructure
- 80%+ test coverage focused on core CLI integration
