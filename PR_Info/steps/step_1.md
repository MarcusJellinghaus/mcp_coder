# Step 1: Create Prompt Command Tests

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md, implement Step 1: Create comprehensive tests for the prompt command functionality.

Create tests that validate:
- Successful prompt execution with mocked Claude CLI
- Input validation for empty/invalid prompts  
- Error handling when Claude CLI fails
- Argument parsing from command line

Follow the existing test patterns in tests/cli/commands/test_help.py and use pytest with proper mocking.
```

## WHERE
- **File**: `tests/cli/commands/test_prompt.py`
- **Test Module**: New test file following existing test structure

## WHAT
- **Test Functions**:
  - `test_execute_prompt_success()` - Mock successful Claude CLI call
  - `test_execute_prompt_empty_input()` - Validate input rejection
  - `test_execute_prompt_claude_error()` - Handle Claude CLI failures
  - `test_prompt_argument_parsing()` - Verify argument extraction

## HOW
- **Imports**: `pytest`, `argparse`, `unittest.mock`
- **Mocking**: Mock `ask_claude_code_cli` function
- **Fixtures**: Use `capsys` for output capture
- **Integration**: Follow existing test patterns

## ALGORITHM
```
FOR each test scenario:
  1. Setup mock arguments/environment
  2. Mock external dependencies (Claude CLI)
  3. Call execute_prompt function
  4. Assert expected return code
  5. Verify output/error messages
```

## DATA
- **Input**: `argparse.Namespace` with prompt attribute
- **Return**: Exit codes (0=success, 1=user error, 2=system error)
- **Mocks**: Claude CLI responses, error conditions
- **Assertions**: Exit codes, console output, error messages
