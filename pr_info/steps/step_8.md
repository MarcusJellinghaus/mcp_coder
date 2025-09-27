# Step 8: Run Tests and Verify Implementation

## Goal
Execute the complete test suite to verify all implementations work correctly and fix any issues discovered during testing.

## WHERE
- **Test Execution**: Run pytest on the modified test files
- **Code Verification**: Check all implemented functions work as expected
- **Integration Check**: Verify CLI functionality remains intact

## WHAT
Execute comprehensive testing and validation:

### Test Commands to Run
```bash
# Run specific test file with verbose output
pytest tests/cli/commands/test_prompt.py -v

# Run new test classes specifically
pytest tests/cli/commands/test_prompt.py::TestPromptClaude -v
pytest tests/cli/commands/test_prompt.py::TestSaveConversationMarkdown -v
pytest tests/cli/commands/test_prompt.py::TestSaveConversationFullJson -v
pytest tests/cli/commands/test_prompt.py::TestExecutePromptWrapper -v
pytest tests/cli/commands/test_prompt.py::TestIntegrationSaveParameters -v

# Run all prompt-related tests
pytest tests/cli/commands/test_prompt.py --tb=short
```

## HOW
- **Sequential Testing**: Run tests in order to identify implementation issues
- **Debugging**: Use pytest verbose output to identify failing tests
- **Fix and Iterate**: Address any test failures or implementation bugs

## ALGORITHM
```
1. Run individual test classes to verify each component
2. Identify any failing tests or import errors
3. Fix implementation issues discovered by tests
4. Re-run tests until all pass
5. Verify CLI integration still works correctly
```

## DATA

### Expected Test Results
- **TestPromptClaude**: All 4 tests should pass
- **TestSaveConversationMarkdown**: All 3 tests should pass  
- **TestSaveConversationFullJson**: All 3 tests should pass
- **TestExecutePromptWrapper**: All 4 tests should pass
- **TestIntegrationSaveParameters**: All 6 tests should pass
- **Existing Tests**: All original tests should continue to pass

### Common Issues to Check

**Import Errors:**
- Missing function imports in test file
- Function not yet implemented in source file

**Implementation Issues:**
- Function signature mismatches
- Missing required imports (os, json, datetime)
- Incorrect parameter handling

**File Operation Issues:**
- Directory creation problems
- File path handling on different OS
- Permission or encoding issues

### Verification Steps

**Function Implementation Check:**
```python
# Verify functions exist and are callable
from mcp_coder.cli.commands.prompt import (
    prompt_claude,
    _save_conversation_markdown, 
    _save_conversation_full_json
)
```

**CLI Integration Check:**
```bash
# Test CLI still works (if Claude CLI available)
mcp-coder prompt "test question" --verbosity verbose
```

## Implementation Notes
- Fix any import errors by ensuring all functions are implemented
- Address file path issues by using `os.path` functions consistently
- Verify error handling works correctly for edge cases
- Ensure backward compatibility with existing CLI functionality

## LLM Prompt for Implementation

```
Please implement Step 8 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Run the test suite to verify all implementations from previous steps work correctly:

1. First check that all functions can be imported successfully
2. Run pytest on tests/cli/commands/test_prompt.py with verbose output
3. Identify any failing tests or implementation issues
4. Fix any problems found in the implementation
5. Re-run tests until all pass

Expected new test classes that should all pass:
- TestPromptClaude
- TestSaveConversationMarkdown  
- TestSaveConversationFullJson
- TestExecutePromptWrapper
- TestIntegrationSaveParameters

If tests fail, debug and fix:
- Import errors (missing function implementations)
- Function signature mismatches
- File operation issues
- Parameter handling problems

Verify that existing tests continue to pass and CLI functionality is preserved.

Report on test results and any fixes that were needed.
```
