# Step 5: Implement Save Conversation Functions

## Goal
Implement the markdown and JSON save functions to enable conversation persistence with different output formats.

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Location**: Add new functions after existing utility functions, before `prompt_claude`

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
- **File Operations**: Use `os.makedirs()` for directory creation, standard file I/O
- **Markdown Generation**: Build structured markdown with sections for prompt, response, metrics
- **JSON Serialization**: Use existing `_serialize_message_for_json` for complex objects
- **Integration**: Called conditionally from `prompt_claude` function

## ALGORITHM

### Markdown Save Algorithm
```
1. Create parent directories if they don't exist
2. Extract key data: response text, session info, metrics
3. Build markdown with structured sections (header, prompt, response, summary)
4. Add tool interactions section if any tool calls made
5. Write complete markdown content to file
```

### JSON Save Algorithm
```
1. Create parent directories if they don't exist  
2. Build comprehensive data structure with metadata, input, response, analysis
3. Include performance calculations and tool interaction summaries
4. Serialize using existing _serialize_message_for_json helper
5. Write formatted JSON to file with proper indentation
```

## DATA

### Markdown File Structure
```markdown
# Conversation with Claude

**Date:** 2025-01-01 12:00:00
**Model:** claude-sonnet-4
**Session ID:** session-123

## User Prompt
[Original user prompt]

## Claude's Response  
[Claude's response text]

## Session Summary
- **Duration:** X.XXs
- **Cost:** $X.XXXX
- **Tokens:** X input, X output
- **Tools Used:** tool1, tool2

## Tool Interactions
- tool_name: {parameters}
```

### JSON File Structure
```json
{
  "conversation_metadata": {
    "timestamp": "2025-01-01T12:00:00Z",
    "working_directory": "/current/dir", 
    "format_version": "1.0",
    "description": "Complete conversation with all Claude API data"
  },
  "user_input": {
    "prompt": "User's question",
    "timestamp": "2025-01-01T12:00:00Z"
  },
  "claude_response": {
    "text": "Claude's response",
    "session_info": {...},
    "result_info": {...},
    "api_metadata": {...},
    "raw_messages": [...]
  },
  "analysis": {
    "tool_interactions": [...],
    "performance_summary": {
      "duration_seconds": 1.5,
      "cost_usd": 0.025,
      "token_usage": {...},
      "tools_used": [...]
    }
  }
}
```

### Dependencies
- **Existing Functions**: `_extract_tool_interactions(raw_messages)`
- **Standard Library**: `os.makedirs()`, `json.dump()`, `datetime.now()`
- **Existing Utilities**: `_serialize_message_for_json` for complex object serialization

## Implementation Notes
- Use `os.path.dirname()` and `os.makedirs(exist_ok=True)` for directory creation
- Handle missing data gracefully with `.get()` and default values
- Maintain consistency with existing code style and error handling patterns
- Add appropriate logging for successful file operations

## LLM Prompt for Implementation

```
Please implement Step 5 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Implement two save functions in src/mcp_coder/cli/commands/prompt.py:

1. _save_conversation_markdown(response_data, prompt, file_path) -> None
2. _save_conversation_full_json(response_data, prompt, file_path) -> None

Both functions should:
- Create parent directories automatically using os.makedirs(os.path.dirname(file_path), exist_ok=True)
- Handle the response_data structure from ask_claude_code_api_detailed_sync

For markdown:
- Create structured markdown with sections for prompt, response, session summary
- Include tool interactions if present (use existing _extract_tool_interactions function)
- Format metrics (duration, cost, tokens) in human-readable form

For JSON:
- Build comprehensive structure with conversation_metadata, user_input, claude_response, analysis
- Include performance summary calculations (duration_seconds = duration_ms/1000)
- Use existing _serialize_message_for_json for proper serialization
- Use json.dump with indent=2 for formatting

Extract data from response_data using .get() with appropriate defaults for missing fields.
```
