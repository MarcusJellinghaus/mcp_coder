# Step 2: Add Tests for Save Conversation Functions

## Goal
Add minimal tests for the two new save functions before implementing them, following TDD principles.

## WHERE
- **File**: `tests/cli/commands/test_prompt.py`
- **Section**: Add new test methods after Step 1 tests

## WHAT
Add 2 test methods to verify file save operations:

### Test Methods
```python
def test_save_conversation_markdown_basic(self) -> None
def test_save_conversation_full_json_basic(self) -> None
```

## HOW
- **Integration**: Add test methods to existing test file
- **File Operations**: Use `tempfile.TemporaryDirectory()` for isolated testing
- **Assertions**: Verify file creation and basic content structure

## ALGORITHM
```
1. Create temporary directory for test files
2. Prepare mock response data with session info
3. Call save function with test data and temp file path
4. Verify file exists and contains expected key content
5. Clean up automatically with TemporaryDirectory
```

## DATA

### Function Signatures to Test
```python
def _save_conversation_markdown(
    response_data: Dict[str, Any],
    prompt: str,
    file_path: str
) -> None

def _save_conversation_full_json(
    response_data: Dict[str, Any],
    prompt: str, 
    file_path: str
) -> None
```

### Test Response Data
```python
test_response_data = {
    "text": "This is Claude's response.",
    "session_info": {
        "session_id": "test-session-123",
        "model": "claude-sonnet-4", 
        "tools": ["file_writer"]
    },
    "result_info": {
        "duration_ms": 1500,
        "cost_usd": 0.025,
        "usage": {"input_tokens": 10, "output_tokens": 8}
    },
    "raw_messages": []
}
```

### Expected Validations
- **Markdown**: Contains prompt, response, session info
- **JSON**: Contains structured data with conversation sections

## Implementation Notes
- Tests should fail initially (save functions don't exist yet)
- Use `tempfile.TemporaryDirectory()` for test isolation  
- Verify file existence and basic content structure
- Keep tests simple - focus on core functionality

## LLM Prompt for Implementation

```
Please implement Step 2 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Add 2 minimal test methods to tests/cli/commands/test_prompt.py for the new save functions:

1. test_save_conversation_markdown_basic() - Test markdown file creation and basic content
2. test_save_conversation_full_json_basic() - Test JSON file creation and structure

Use tempfile.TemporaryDirectory for test isolation. Tests should verify:
- File is created at the expected path
- File contains key elements (prompt, response, session info)  
- Basic content structure is correct

The functions to test:
- _save_conversation_markdown(response_data, prompt, file_path) -> None
- _save_conversation_full_json(response_data, prompt, file_path) -> None

Keep tests minimal and focused on core save functionality. Tests should fail initially since functions don't exist yet.
```
