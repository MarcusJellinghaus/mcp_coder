# Step 4: Update Integration Tests and API Tests

## LLM Prompt
```
Based on the refactor summary in `pr_info2/steps/summary.md` and the completed directory-based formatters from Steps 1-3, implement Step 4 using TDD: Update the integration tests and main API tests to work with the new directory-based approach while maintaining the same test coverage and expectations. The public API behavior should remain unchanged from the user perspective.
```

## WHERE
- `tests/formatters/test_integration.py` - **START HERE: Update integration tests (TDD)**
- `tests/formatters/test_main_api.py` - Update combined API tests after integration tests

## WHAT
### Tests to Update (Not Remove)
```python
# In test_integration.py - Update expectations
def test_complete_formatting_workflow_with_exit_codes():
    """Update to expect directory-based formatter calls"""

def test_step0_code_samples_from_analysis():
    """Update to work with directory-based execution"""

# In test_main_api.py - Update mocking
def test_format_code_runs_both_formatters_sequentially():
    """Update mocks to expect directory-based calls"""
```

## HOW
### Integration Points
- Update test mocks to expect directory commands instead of file commands
- Verify that integration tests still validate real formatter execution
- Ensure API tests properly mock the new directory-based formatter functions
- Maintain same test coverage levels and assertions

### Dependencies (Test Updates)
```python
# Update test mocks and expectations
from unittest.mock import patch, Mock
import tempfile
from pathlib import Path
```

## ALGORITHM
```
1. Update integration test setup to create directory structures
2. Modify test expectations to match directory-based command patterns
3. Update API test mocks to expect directory parameters
4. Verify same test coverage with simplified implementation
5. Run tests to ensure all scenarios still work
```

## DATA
### Updated Test Patterns
```python
# OLD: File-by-file test expectations
mock_execute.assert_called_with(["black", "--check", "/path/to/file.py"])

# NEW: Directory-based test expectations  
mock_execute.assert_called_with(["black", "--check", "/path/to/directory"])
```

### Mock Return Values (Updated)
```python
# Mock for successful directory formatting with output parsing
mock_execute_command.return_value = Mock(
    return_code=0,
    stdout="reformatted /path/to/file1.py\nreformatted /path/to/file2.py\n",
    stderr=""
)
```

### Test Data (Same Scenarios, Different Implementation)
- Same test files and directory structures
- Same expected `FormatterResult` outcomes
- Same error scenarios and edge cases
- Updated to expect directory-based execution

## Tests Required (TDD - Focused Testing)
1. **Integration workflow test (1 test)**
   - Test end-to-end directory-based execution
   - Verify both formatters work together with output parsing
   - Ensure file change detection works through single-phase approach

2. **API combination test (1 test)**
   - Test combined API calls individual formatters correctly
   - Verify error handling and result aggregation
   - Mock directory-based formatter calls

3. **Error handling integration test (1 test)**
   - Test fail-fast behavior across multiple directories
   - Verify proper error propagation from formatters to API
   - Ensure clean error reporting

## Verification Steps
1. All integration tests pass with directory-based execution
2. API tests properly mock directory-based formatter calls
3. Same level of test coverage maintained
4. Real integration tests still validate actual tool execution
5. Performance improvement observable (less Python file scanning)

## Key Principle
**Maintain identical test coverage and validation** while updating the underlying implementation expectations to match directory-based formatter execution.
