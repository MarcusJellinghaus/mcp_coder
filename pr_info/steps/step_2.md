# Step 2: Add Tests for Save Conversation Functions  

## Goal
Implement tests for markdown and JSON save functions before implementing the actual save functionality, following TDD principles.

## WHERE
- **File**: `tests/cli/commands/test_prompt.py`
- **Sections**: Add new test classes after `TestPromptClaude`

## WHAT
Add two test classes to verify file save operations:

### Test Classes and Methods
```python
class TestSaveConversationMarkdown:
    def test_save_conversation_markdown_basic(self) -> None
    def test_save_conversation_markdown_with_tool_interactions(self) -> None
    def test_save_conversation_markdown_creates_directory(self) -> None

class TestSaveConversationFullJson:
    def test_save_conversation_full_json_basic(self) -> None
    def test_save_conversation_full_json_complete_structure(self) -> None
    def test_save_conversation_full_json_creates_directory(self) -> None
```

## HOW
- **Integration**: Add test classes to existing test file
- **Imports**: Add `tempfile` import for temporary directories
- **File Operations**: Use real file operations in temporary directories
- **Assertions**: Verify file creation and content structure

## ALGORITHM
```
1. Create temporary directory for test files
2. Prepare mock response data with session info
3. Call save function with test data and temp file path
4. Verify file exists and contains expected content
5. Clean up temporary files automatically (tempfile.TemporaryDirectory)
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

### Test Response Data Structure
```python
test_response_data = {
    "text": "This is Claude's response.",
    "session_info": {
        "session_id": "test-session-123", 
        "model": "claude-sonnet-4",
        "tools": ["file_writer", "code_analyzer"]
    },
    "result_info": {
        "duration_ms": 1500,
        "cost_usd": 0.025,
        "usage": {"input_tokens": 10, "output_tokens": 8}
    },
    "api_metadata": {"request_id": "req-456"},
    "raw_messages": [
        {"role": "user", "content": "Test question"},
        {"role": "assistant", "content": "Test answer", "tool_calls": [...]}
    ]
}
```

### Expected File Content Validations

**Markdown File:**
- Contains `# Conversation with Claude`
- Has user prompt and Claude response sections
- Includes session summary with metrics
- Shows tool interactions if present

**JSON File:**
- Has `conversation_metadata`, `user_input`, `claude_response`, `analysis` sections
- Contains complete response data preservation
- Includes performance summary calculations
- Valid JSON structure

## Implementation Notes
- Tests should fail initially (save functions don't exist yet)
- Use `tempfile.TemporaryDirectory()` for isolated file operations
- Test both happy path and edge cases (nested directories)
- Verify content structure, not exact formatting

## LLM Prompt for Implementation

```
Please implement Step 2 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Add comprehensive tests for two new save functions to tests/cli/commands/test_prompt.py:

1. _save_conversation_markdown(response_data, prompt, file_path) -> None
2. _save_conversation_full_json(response_data, prompt, file_path) -> None

Add test classes TestSaveConversationMarkdown and TestSaveConversationFullJson with methods to test:

For Markdown:
- Basic file creation with standard conversation structure
- Handling of tool interactions in the content
- Automatic parent directory creation

For JSON:
- Complete conversation data structure preservation  
- All required sections (conversation_metadata, user_input, claude_response, analysis)
- Automatic parent directory creation

Use tempfile.TemporaryDirectory for test isolation. Tests should verify file existence and content structure.

The functions should be imported from: mcp_coder.cli.commands.prompt
```
