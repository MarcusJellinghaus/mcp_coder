# Step 6: Run Tests and Verify Implementation

## Goal
Execute the test suite to verify all implementations work correctly and fix any issues discovered.

## WHERE
- **Test Execution**: Run pytest on the modified test files
- **Code Verification**: Check all implemented functions work as expected

## WHAT
Execute testing and validation:

### Test Commands
```bash
# Run specific test file with verbose output
pytest tests/cli/commands/test_prompt.py -v

# Run just the new tests to verify they pass
pytest tests/cli/commands/test_prompt.py::test_execute_prompt_calls_prompt_claude_with_correct_parameters -v
pytest tests/cli/commands/test_prompt.py::test_execute_prompt_parameter_mapping_with_defaults -v
pytest tests/cli/commands/test_prompt.py::test_save_conversation_markdown_basic -v
pytest tests/cli/commands/test_prompt.py::test_save_conversation_full_json_basic -v

# Run all existing tests to ensure no regressions
pytest tests/cli/commands/test_prompt.py::TestExecutePrompt -v
```

## HOW
- **Sequential Testing**: Run new tests first, then existing tests
- **Debugging**: Use pytest verbose output to identify any failures
- **Fix and Iterate**: Address any issues discovered

## ALGORITHM
```
1. Run new tests to verify refactoring components work
2. Run existing tests to ensure no regressions
3. Fix any implementation issues discovered
4. Re-run tests until all pass
5. Verify CLI integration still works
```

## DATA

### Expected Results
- **New Tests**: 4 new test methods should pass
- **Existing Tests**: All 20+ existing tests should continue to pass  
- **No Regressions**: CLI functionality should work unchanged

### Common Issues to Check
- **Import Errors**: Missing function implementations
- **Function Signature Mismatches**: Parameter name/type errors
- **File Operation Issues**: Directory creation or path handling
- **Parameter Mapping**: Incorrect argparse.Namespace handling

## Implementation Notes
- Fix any import errors by ensuring all functions are implemented
- Address parameter mapping issues in the CLI wrapper
- Verify file operations work correctly across different OS
- Ensure backward compatibility with existing CLI usage

## LLM Prompt for Implementation

```
Please implement Step 6 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Run the test suite to verify the refactoring works correctly:

1. Check that all functions can be imported successfully
2. Run pytest on tests/cli/commands/test_prompt.py with verbose output
3. Verify the 4 new test methods pass
4. Verify all existing TestExecutePrompt tests continue to pass (no regressions)
5. Fix any issues found

Expected: 
- 4 new test methods for parameter mapping and save functions
- 20+ existing test methods should all still pass
- No breaking changes to CLI functionality

If tests fail, debug and fix:
- Import errors (missing implementations)
- Function signature mismatches
- Parameter mapping issues
- File operation problems

Report on test results and any fixes needed.
```
