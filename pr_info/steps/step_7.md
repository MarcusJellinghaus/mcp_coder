# Step 7: Add Integration Tests for Save Features

## Goal
Add comprehensive integration tests that verify the complete workflow of saving conversations to both markdown and JSON formats.

## WHERE
- **File**: `tests/cli/commands/test_prompt.py` 
- **Section**: Add new test class `TestIntegrationSaveParameters`

## WHAT
Add integration test class to verify end-to-end save functionality:

### Test Methods
```python
class TestIntegrationSaveParameters:
    def test_prompt_claude_saves_markdown_file(self) -> None
    def test_prompt_claude_saves_json_file(self) -> None  
    def test_prompt_claude_saves_both_files(self) -> None
    def test_execute_prompt_integration_with_save_parameters(self) -> None
    def test_save_parameters_with_none_values(self) -> None
    def test_save_with_file_permission_error(self) -> None
```

## HOW
- **Integration**: Test complete workflow from function call to file creation
- **Real Files**: Use `tempfile.TemporaryDirectory()` for actual file operations
- **Mock API**: Mock Claude API while testing real file I/O
- **Error Cases**: Test file permission errors and edge cases

## ALGORITHM
```
1. Create temporary directory for test files
2. Mock Claude API with comprehensive response data
3. Call prompt_claude or execute_prompt with save parameters
4. Verify files were created with expected content
5. Validate file structure and data integrity
```

## DATA

### Test Response Data
```python
integration_response = {
    "text": "Integration test response text",
    "session_info": {
        "session_id": "integration-test-session",
        "model": "claude-sonnet-4", 
        "tools": ["integration_tool", "test_tool"]
    },
    "result_info": {
        "duration_ms": 2000,
        "cost_usd": 0.035,
        "usage": {"input_tokens": 15, "output_tokens": 12}
    },
    "api_metadata": {"request_id": "integration-req-123"},
    "raw_messages": [
        {"role": "user", "content": "Integration test prompt"},
        {"role": "assistant", "content": "Integration response", "tool_calls": [...]}
    ]
}
```

### Test Scenarios

**Single File Save Tests:**
- Save only markdown file
- Save only JSON file  
- Verify content structure and completeness

**Dual File Save Test:**
- Save both markdown and JSON simultaneously
- Verify both files created correctly
- Validate content consistency between formats

**CLI Integration Test:**
- Test through `execute_prompt` wrapper
- Verify parameter mapping works end-to-end
- Confirm argparse.Namespace handling

**Error Handling Tests:**
- Test with `None` values (no files created)
- Test file permission errors
- Verify graceful error handling

### Validation Checks

**Markdown File Validation:**
```python
assert "Integration test prompt" in md_content
assert "Integration test response text" in md_content  
assert "integration-test-session" in md_content
assert "2.00s" in md_content  # Duration formatting
assert "$0.0350" in md_content  # Cost formatting
```

**JSON File Validation:**
```python
assert data["user_input"]["prompt"] == "Integration test prompt"
assert data["claude_response"]["text"] == "Integration test response text"
assert data["claude_response"]["session_info"]["session_id"] == "integration-test-session"
assert data["analysis"]["performance_summary"]["duration_seconds"] == 2.0
```

## Implementation Notes
- Use real file operations in temporary directories
- Mock only the Claude API, not file system operations
- Test both success and error conditions
- Verify content structure without being overly specific about formatting

## LLM Prompt for Implementation

```
Please implement Step 7 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Add comprehensive integration tests for the save features to tests/cli/commands/test_prompt.py.

Create test class TestIntegrationSaveParameters with methods to test:

1. prompt_claude saving markdown files (test_prompt_claude_saves_markdown_file)
2. prompt_claude saving JSON files (test_prompt_claude_saves_json_file)  
3. prompt_claude saving both file types simultaneously (test_prompt_claude_saves_both_files)
4. execute_prompt wrapper integration (test_execute_prompt_integration_with_save_parameters)
5. None parameter handling (test_save_parameters_with_none_values)
6. Error handling for permission errors (test_save_with_file_permission_error)

Use tempfile.TemporaryDirectory for test isolation. Mock ask_claude_code_api_detailed_sync but use real file operations.

For each test:
- Create comprehensive mock response data
- Verify files are created at expected paths
- Validate file content structure and key data elements
- Test both individual and combined save operations

Include error case testing for file permission issues and verify graceful handling.
```
