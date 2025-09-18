# Step 1: Create Basic Prompt Command Tests

## LLM Prompt
```
Based on the summary in PR_Info/steps/summary.md, implement Step 1: Create tests for basic prompt command functionality.

Create tests for the core prompt execution:
- Test successful prompt execution with mocked Claude API detailed function
- Test API error handling when Claude API fails

Follow the existing test patterns in tests/cli/commands/test_help.py and use pytest with proper mocking.
This is the foundation for the TDD approach - implement only the basic test structure.
```

## WHERE
- **File**: `tests/cli/commands/test_prompt.py`
- **Test Module**: New test file following existing test structure

## WHAT
- **Test Functions**:
  - `test_basic_prompt_success()` - Mock successful Claude API detailed call with just-text output
  - `test_prompt_api_error()` - Handle Claude API failures gracefully

## HOW
- **Imports**: `pytest`, `argparse`, `unittest.mock`
- **Mocking**: Mock `ask_claude_code_api_detailed_sync` function
- **Fixtures**: Use `capsys` for output capture
- **Integration**: Follow existing test patterns from other command tests

## ALGORITHM
```
FOR each test scenario:
  1. Setup mock arguments with basic prompt
  2. Mock ask_claude_code_api_detailed_sync function
  3. Call execute_prompt function
  4. Assert expected return code (0 for success)
  5. Verify basic output presence (Claude response visible)
```

## DATA
- **Input**: `argparse.Namespace` with prompt attribute
- **Return**: Exit codes (0=success, non-zero=error) 
- **Mocks**: Basic Claude API response with minimal structure
- **Assertions**: Exit codes, presence of Claude response in output
- **Scope**: Basic functionality only - no verbosity levels yet
