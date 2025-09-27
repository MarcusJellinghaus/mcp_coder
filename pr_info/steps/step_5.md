# Step 5: Create Windows Batch Wrapper and Integration Tests

## WHERE
- **Implementation**: `workflows/create_PR.bat` (new file)
- **Integration Tests**: `tests/test_create_pr_integration.py` (new file)

## WHAT
Create Windows command wrapper and comprehensive integration tests for the complete workflow.

### Batch File Requirements
- Simple wrapper following existing `implement.bat` pattern
- Handle command-line arguments pass-through
- Proper error code propagation

## HOW

### Integration Points
- **Copy Pattern**: Use `workflows/implement.bat` as exact template
- **Python Execution**: Call `create_PR.py` with argument forwarding
- **Integration Tests**: Test with real git repository (using test fixtures)
- **Error Handling**: Verify exit codes and error messages

### Batch File Structure
```batch
@echo off
python workflows/create_PR.py %*
```

### Integration Test Areas
- Prerequisites validation (dirty git, incomplete tasks)
- Git diff generation with real repository
- LLM integration with mocked responses
- File cleanup operations
- GitHub API integration (mocked)

## ALGORITHM (Pseudocode)

### Batch Wrapper
```
1. Execute Python script with all arguments
2. Propagate exit code
```

### Integration Tests
```
1. Setup test git repository with branches
2. Create test task tracker with incomplete tasks
3. Test prerequisite failures
4. Test successful workflow with mocks
5. Verify final state (PR created, files cleaned)
```

## LLM Prompt

### Context
You are implementing Step 5 (final step) of the Create Pull Request Workflow. Review the summary document in `pr_info/steps/summary.md` for full context. This step completes the implementation with Windows support and integration testing.

### Task
Create Windows batch wrapper and comprehensive integration tests to validate the complete workflow.

### Requirements
1. **Batch File**: Create `workflows/create_PR.bat`:
   - Copy exact pattern from `workflows/implement.bat`
   - Ensure proper argument forwarding
   - Test with sample arguments
2. **Integration Tests**: Create `tests/test_create_pr_integration.py`:
   - Use real git repository setup (pytest fixtures)
   - Mock external services (GitHub API, LLM calls)
   - Test complete workflow end-to-end
   - Test all error scenarios and edge cases
3. **Validation**: Ensure complete implementation:
   - All previous step functions work together
   - Proper error handling throughout workflow
   - Clean user experience with clear messages
4. **Documentation**: Update any necessary README or docs

### Expected Output
- Simple 3-line batch file
- Comprehensive integration test suite (~100 lines)
- Verification that all steps work together
- Ready-to-deploy workflow tool

### Success Criteria
- Batch file works on Windows with argument passing
- Integration tests cover all workflow scenarios
- Complete workflow runs successfully
- All error cases handled gracefully
- Tool ready for production use