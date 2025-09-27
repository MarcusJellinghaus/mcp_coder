# Step 4: Implement prompt_claude Core Function

## Goal
Implement the core `prompt_claude` function with explicit parameters, moving the business logic from `execute_prompt` while maintaining all existing functionality.

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Location**: Add new function after utility functions, before `execute_prompt`

## WHAT
Implement the core function with explicit parameters:

### Function Signature
```python
def prompt_claude(
    prompt: str,
    verbosity: str = "just-text",
    timeout: int = 30,
    store_response: bool = False,
    continue_from: Optional[str] = None,
    continue_latest: bool = False,
    save_conversation_md: Optional[str] = None,
    save_conversation_full_json: Optional[str] = None
) -> int:
```

## HOW
- **Extract Logic**: Move existing logic from `execute_prompt` to `prompt_claude`
- **Add Save Logic**: Integrate new save functionality with conditional calls
- **Error Handling**: Maintain existing try/catch structure

## ALGORITHM
```
1. Handle continuation logic (continue_from/continue_latest)
2. Call Claude API with enhanced prompt and timeout
3. Store response if store_response=True (existing functionality)
4. Save to markdown file if save_conversation_md provided
5. Save to JSON file if save_conversation_full_json provided
6. Format and print output based on verbosity level
```

## DATA

### Input Parameters
- **prompt**: User's question/prompt for Claude
- **verbosity**: Output format ("just-text", "verbose", "raw")
- **timeout**: API timeout in seconds
- **store_response**: Boolean for existing storage functionality
- **continue_from**: Path to previous session file
- **continue_latest**: Boolean to use latest session file
- **save_conversation_md**: Full path for markdown save
- **save_conversation_full_json**: Full path for JSON save

### Return Values
- **Success**: `0` - Normal execution completed
- **Error**: `1` - Exception occurred (API error, file error, etc.)

### Function Dependencies
```python
# Existing functions to use
ask_claude_code_api_detailed_sync(enhanced_prompt, timeout)
_store_response(response_data, prompt)  # if store_response
_find_latest_response_file()  # if continue_latest
_load_previous_chat(file_path)  # if continue_from
_build_context_prompt(context, prompt)  # for continuation
_format_just_text(response_data)  # for output
_format_verbose(response_data)  # for output  
_format_raw(response_data)  # for output

# New functions to call
_save_conversation_markdown(response_data, prompt, file_path)
_save_conversation_full_json(response_data, prompt, file_path)
```

## Implementation Notes
- Copy existing logic from current `execute_prompt` 
- Add conditional save calls for new parameters
- Maintain exact same error handling and logging
- Preserve all existing functionality and behavior

## LLM Prompt for Implementation

```
Please implement Step 4 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Implement the prompt_claude function in src/mcp_coder/cli/commands/prompt.py.

Move the core business logic from the existing execute_prompt function into this new function with explicit parameters.

Function signature:
```python
def prompt_claude(
    prompt: str,
    verbosity: str = "just-text",
    timeout: int = 30,
    store_response: bool = False,
    continue_from: Optional[str] = None,
    continue_latest: bool = False,
    save_conversation_md: Optional[str] = None,
    save_conversation_full_json: Optional[str] = None
) -> int:
```

The function should:
1. Handle continuation logic (continue_from/continue_latest parameters)
2. Call ask_claude_code_api_detailed_sync with the prompt and timeout
3. Store response if store_response=True (existing _store_response functionality)
4. Save to markdown if save_conversation_md path provided (call _save_conversation_markdown)
5. Save to JSON if save_conversation_full_json path provided (call _save_conversation_full_json)
6. Format output based on verbosity and print to stdout
7. Return 0 for success, 1 for errors

Copy the existing logic structure from execute_prompt, maintaining all error handling, logging, and existing functionality. Add the new save operations as conditional calls based on the parameters.
```
