# Step 4: Implement Save Conversation Functions  

## Goal
Implement the markdown and JSON save functions to enable conversation persistence.

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Location**: Add new functions before `prompt_claude`

## WHAT
Implement two save functions:

### Function Signatures
```python
def _save_conversation_markdown(
    response_data: Dict[str, Any],
    prompt: str,
    file_path: str
) -> None:

def _save_conversation_full_json(
    response_data: Dict[str, Any],
    prompt: str,
    file_path: str
) -> None:
```

## HOW
- **File Operations**: Use `os.makedirs()` for directory creation
- **Markdown Generation**: Build structured markdown with prompt, response, metrics
- **JSON Serialization**: Use existing `_serialize_message_for_json` for complex objects

## ALGORITHM

### Markdown Save
```
1. Create parent directories if needed
2. Extract response text, session info, metrics
3. Build markdown with sections: prompt, response, summary, tools
4. Write to file
```

### JSON Save  
```
1. Create parent directories if needed
2. Build data structure: metadata, user_input, claude_response, analysis
3. Use _serialize_message_for_json for serialization
4. Write formatted JSON to file
```

## DATA

### Markdown Structure
```markdown
# Conversation with Claude

**Date:** 2025-01-01 12:00:00
**Session ID:** session-123

## User Prompt
[prompt]

## Claude's Response
[response]

## Session Summary  
- **Duration:** X.XXs
- **Cost:** $X.XXXX
- **Tokens:** X input, X output
```

### JSON Structure
```json
{
  "prompt": "User's question",
  "response_data": {
    // Complete response_data from ask_claude_code_api_detailed_sync stored as-is
    "text": "Claude's response",
    "session_info": {...},
    "result_info": {...},
    "raw_messages": [...]
  },
  "metadata": {
    "timestamp": "2025-01-01T12:00:00Z",
    "working_directory": "/current/dir",
    "model": "claude-sonnet-4"
  }
}
```

## Implementation Notes
- Use `os.makedirs(os.path.dirname(file_path), exist_ok=True)` for directories
- Handle missing data gracefully with `.get()` and defaults
- Use existing `_serialize_message_for_json` helper for JSON serialization

## LLM Prompt for Implementation

```
Please implement Step 4 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Implement the two save functions in src/mcp_coder/cli/commands/prompt.py:

1. _save_conversation_markdown(response_data, prompt, file_path) -> None
2. _save_conversation_full_json(response_data, prompt, file_path) -> None

Both functions should:
- Create parent directories using os.makedirs(os.path.dirname(file_path), exist_ok=True)
- Use best-effort error handling: log failures but don't raise exceptions
- Extract data from response_data using .get() with defaults

For markdown:
- Create readable format with sections for prompt, response, session summary
- Include metrics (duration, cost, tokens) in human-readable form

For JSON:
- Use the same structure as existing _store_response function (prompt, response_data, metadata)
- Store the complete response_data from ask_claude_code_api_detailed_sync as-is
- Use existing _serialize_message_for_json for proper serialization
- Use json.dump with indent=2

Implement best-effort error handling - save operations should not fail the overall command.
```
