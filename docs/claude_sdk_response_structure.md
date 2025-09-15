# Claude Code SDK Response Structure Documentation

## Overview

The Claude Code SDK returns a stream of different message types when making API calls. This document explains the response structure and how our implementation parses it.

## Official Documentation

For complete SDK documentation, see: https://docs.anthropic.com/en/docs/claude-code/sdk/sdk-python

## Response Message Types

The SDK returns three main message types in sequence:

### 1. SystemMessage
Contains session metadata and configuration information.

**Structure:**
```python
SystemMessage(
    subtype='init',
    data={
        'type': 'system',
        'subtype': 'init',
        'cwd': '/path/to/working/directory',
        'session_id': 'unique-session-id',
        'tools': ['Task', 'Bash', 'Read', 'Write', ...],
        'mcp_servers': [
            {'name': 'checker', 'status': 'connected'},
            {'name': 'filesystem', 'status': 'connected'}
        ],
        'model': 'claude-sonnet-4-20250514',
        'permissionMode': 'default',
        'apiKeySource': 'environment',
        'output_style': 'default'
    }
)
```

**Key Information:**
- `session_id`: Unique identifier for the conversation session
- `model`: The Claude model being used
- `tools`: List of available tools (file operations, web search, etc.)
- `mcp_servers`: Model Context Protocol servers and their status
- `cwd`: Current working directory
- `permissionMode`: Permission level for tool usage

### 2. AssistantMessage
Contains Claude's actual response in content blocks.

**Structure:**
```python
AssistantMessage(
    content=[
        TextBlock(text="19")  # Claude's response text
    ]
)
```

**Content Block Types:**
- `TextBlock`: Contains the actual text response
- `ToolUseBlock`: Tool usage requests (when Claude uses tools)
- `ToolResultBlock`: Results from tool execution

**Parsing:**
Our implementation extracts text from `TextBlock` objects and concatenates them to form the final response string.

### 3. ResultMessage
Contains final results, cost, and usage statistics.

**Structure:**
```python
ResultMessage(
    subtype='success',
    duration_ms=2801,
    duration_api_ms=3641,
    is_error=False,
    num_turns=1,
    session_id='same-session-id',
    total_cost_usd=0.058779649999999996,
    usage={
        'input_tokens': 4,
        'cache_creation_input_tokens': 15235,
        'cache_read_input_tokens': 4802,
        'output_tokens': 5,
        'server_tool_use': {'web_search_requests': 0},
        'service_tier': 'standard',
        'cache_creation': {
            'ephemeral_1h_input_tokens': 0,
            'ephemeral_5m_input_tokens': 15235
        }
    },
    result='19'  # Sometimes contains the final result
)
```

**Key Information:**
- `total_cost_usd`: Cost of the API call in USD
- `duration_ms`: Total duration including processing
- `duration_api_ms`: API-only duration
- `usage`: Detailed token usage breakdown
- `num_turns`: Number of conversation turns
- `is_error`: Whether the call resulted in an error

## Our Implementation

### Simple Response (`ask_claude_code_api`)
Returns only the text content from `AssistantMessage.TextBlock` objects as a concatenated string.

```python
result = ask_claude_code_api("What is 2+2?")
# Returns: "4"
```

### Detailed Response (`ask_claude_code_api_detailed_sync`)
Returns comprehensive information including session metadata, cost, and raw messages.

```python
result = ask_claude_code_api_detailed_sync("What is 2+2?")
# Returns:
{
    'text': '4',
    'session_info': {
        'session_id': 'abc123',
        'model': 'claude-sonnet-4',
        'tools': ['Task', 'Bash', 'Read', ...],
        'mcp_servers': [{'name': 'checker', 'status': 'connected'}],
        'cwd': '/path/to/project',
        'api_key_source': 'environment'
    },
    'result_info': {
        'duration_ms': 2801,
        'duration_api_ms': 3641,
        'cost_usd': 0.058779,
        'usage': {...},
        'num_turns': 1,
        'is_error': False
    },
    'raw_messages': [SystemMessage(...), AssistantMessage(...), ResultMessage(...)]
}
```

## Type Checking and Fallbacks

Our implementation includes robust type checking:

1. **Import-based checking**: Uses proper `isinstance()` checks when SDK types are available
2. **String-based fallback**: Uses `type(message).__name__` when imports fail
3. **Attribute-based parsing**: Checks for common attributes as final fallback

## Debug Information

When making API calls, debug information is printed showing:
- Session ID and model used
- Cost and duration information
- Available tools and MCP servers

## Error Handling

The implementation handles various error scenarios:
- Import errors (SDK not installed)
- Authentication errors
- Timeout errors
- Network/connection errors
- Malformed responses

All errors are converted to standard `subprocess` exceptions for consistency with CLI version.
