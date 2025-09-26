# Step 2: Create Mypy Integration Test

## WHERE
- File: `tests/test_mypy_integration.py` (new file)

## WHAT
Create comprehensive test for mypy checking functionality before implementing it.

### Test Functions:
1. `test_mypy_check_clean_code()` - Test when no mypy errors
2. `test_mypy_check_with_errors()` - Test when mypy finds issues  
3. `test_mypy_fix_loop()` - Test fix attempt loop with max retries

## HOW
- **Test Framework**: Use pytest with existing patterns
- **Mocking**: Mock MCP `run_mypy_check()` and `ask_llm()` calls
- **Test Data**: Create sample mypy outputs (clean vs with errors)

## ALGORITHM
```
1. Setup test fixtures for clean/error mypy outputs
2. Test clean mypy case (no fixes needed)
3. Test error case with successful fix
4. Test max retry limit (3 attempts)
5. Verify conversation logging works
```

## DATA
### Test Inputs:
- **Clean mypy output**: `"Mypy check completed. No type errors found."`
- **Error mypy output**: `"Mypy found type issues that need attention:\n\nsrc/file.py:10: error: ..."`
- **Max retries**: `3`

### Return Values:
- **Success case**: `True` (no more errors)
- **Max retries**: `False` (gave up after 3 attempts)

## LLM Prompt for This Step

```
Reference: pr_info/steps/summary.md  

Implement Step 2: Create test file for mypy integration functionality.

Create tests/test_mypy_integration.py with comprehensive tests for the mypy checking feature that will be implemented in the next step.

The tests should cover:
1. Successful mypy check (no errors found)
2. Mypy errors found and successfully fixed
3. Max retry behavior (3 attempts then give up)
4. Conversation logging of fix attempts

Use mocking to simulate MCP run_mypy_check() and ask_llm() responses.
Follow existing test patterns in the tests/ directory.
Use pytest framework.

This is TDD - write the tests first before implementing the actual functionality.
```
