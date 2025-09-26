# Step 5: End-to-End Integration Test

## WHERE
- File: `tests/test_workflow_integration.py` (new file)

## WHAT
Create integration test that verifies the complete workflow with mypy checking.

### Test Function:
```python
def test_implement_workflow_with_mypy_integration()
```

## HOW
- **Test Scope**: Full workflow from task selection through mypy checking to formatters
- **Mocking**: Mock file operations, git operations, LLM calls, MCP tools
- **Verification**: Ensure mypy check runs at correct workflow position

## ALGORITHM
```
1. Setup mock incomplete task and project directory
2. Mock LLM response that introduces type errors
3. Mock mypy finding errors, then LLM fixing them
4. Verify mypy check called after LLM, before formatters
5. Verify conversation includes mypy fix attempts
```

## DATA
### Test Scenario:
- **Task**: Mock implementation task from task tracker
- **LLM Response 1**: Code with type errors
- **Mypy Result 1**: Errors found
- **LLM Response 2**: Fixed code  
- **Mypy Result 2**: Clean

### Verification Points:
- Mypy check called in correct order
- Fix attempts logged to conversation
- Workflow continues to formatters/commit

## LLM Prompt for This Step

```
Reference: pr_info/steps/summary.md

Implement Step 5: Create end-to-end integration test.

Create tests/test_workflow_integration.py that tests the complete workflow including the new mypy checking feature.

The test should:
1. Mock a complete workflow run with an implementation task
2. Simulate mypy finding type errors after LLM implementation
3. Simulate LLM successfully fixing the type errors
4. Verify mypy check runs at the correct point in workflow
5. Verify conversation logging includes mypy fix attempts
6. Verify workflow continues normally after mypy checking

Use comprehensive mocking to avoid external dependencies (git, file system, LLM API, MCP tools).
This validates the complete integration works correctly.
```
