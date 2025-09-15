# Step 4: Fix Import Statements and Test Discovery

## Objective

Update import statements in moved test files and ensure pytest can discover and run all tests in the new directory structure.

## Context

Reference the **summary** (`pr_info/steps/summary.md`) for complete project context. This step depends on Steps 1-3 completing successfully (directories created, files moved, new tests created).

## Implementation Details

### WHERE
Update import statements in moved test files:
- `tests/llm_providers/claude/test_claude_client.py`
- `tests/llm_providers/claude/test_claude_client_integration.py`
- `tests/llm_providers/claude/test_claude_code_api.py`
- `tests/llm_providers/claude/test_claude_code_cli.py`
- `tests/llm_providers/claude/test_claude_executable_finder.py`

And verify test discovery works for all test files.

### WHAT
**Main Functions**:
- Import statement analysis and correction
- Test discovery validation with pytest
- Path resolution verification
- Import error detection and fixing

**Import Updates Needed**:
```python
# Before (in root tests/)
from mcp_coder.llm_providers.claude.claude_client import ask_claude

# After (in tests/llm_providers/claude/)
from mcp_coder.llm_providers.claude.claude_client import ask_claude
# (Same - absolute imports should work from any location)
```

### HOW
**Integration Points**:
- Use `pytest --collect-only` to verify test discovery
- Check for import errors with `python -m pytest --collect-only`
- Validate that relative paths work correctly
- Ensure all tests can be run individually and as a suite

### ALGORITHM
**Core Logic (5-6 lines)**:
```python
for test_file in moved_test_files:
    imports = extract_imports(test_file)
    updated_imports = validate_and_fix_imports(imports)
    update_file_imports(test_file, updated_imports)
    verify_test_runs(test_file)
```

### DATA
**Return Values**:
- Updated files: `List[Path]`
- Import fixes applied: `Dict[Path, List[str]]`
- Test discovery results: `TestDiscoveryReport`

**Data Structures**:
- Import mapping dictionaries
- Test discovery status objects
- Error reporting structures

## LLM Implementation Prompt

Please review the implementation plan in PR_Info, especially the summary and steps/step_4.md.

**Task**: Fix import statements and ensure test discovery works correctly after the restructuring.

**Requirements**:
1. Examine all moved test files for import statement issues
2. Fix any broken imports caused by file relocation
3. Verify pytest can discover all tests in new structure
4. Test that all existing tests still pass
5. Ensure both individual test files and full test suite run correctly
6. Check that imports work from the new directory locations

**Process**:
1. Run `pytest --collect-only` to check test discovery
2. Identify any import errors or test collection failures
3. Fix import statements in moved files as needed
4. Re-run test discovery to confirm all tests are found
5. Execute a subset of tests to verify functionality
6. Run the full test suite to ensure everything works

**Validation Steps**:
- All tests discoverable by pytest in new locations
- No import errors when running tests
- Test execution works from new directory structure
- Full test suite passes (same number of tests as before)

**Note**: Most imports should already work correctly since Python uses absolute imports by default, but some edge cases may need adjustment.

Please implement the necessary import fixes and validate that the test restructuring maintains full functionality.

## Acceptance Criteria

- [ ] All moved test files have correct import statements
- [ ] Pytest discovers all tests in new directory structure
- [ ] No import errors when running individual test files
- [ ] Full test suite runs and passes (same test count as before)
- [ ] Test discovery works from both root directory and subdirectories
- [ ] All existing test functionality preserved after restructuring
