# Step 3: Implement prompt_claude Core Function

## Goal  
Implement the core `prompt_claude` function by extracting business logic from `execute_prompt`, maintaining all existing functionality.

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Location**: Add new function before `execute_prompt`

## WHAT
Extract the business logic from `execute_prompt` into `prompt_claude` with explicit parameters:

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
- **Add Save Logic**: Add conditional calls to save functions
- **Maintain Behavior**: Preserve exact same functionality and error handling

## ALGORITHM
```
1. Handle continuation logic (continue_from/continue_latest parameters)
2. Call Claude API with enhanced prompt and timeout
3. Store response if store_response=True (existing functionality)
4. Save to markdown file if save_conversation_md provided
5. Save to JSON file if save_conversation_full_json provided
6. Format and print output based on verbosity level
7. Return 0 for success, 1 for errors
```

## DATA

### Key Dependencies (Existing Functions)
```python
ask_claude_code_api_detailed_sync(enhanced_prompt, timeout)
_store_response(response_data, prompt)  # if store_response
_find_latest_response_file()  # if continue_latest
_load_previous_chat(file_path)  # if continue_from
_build_context_prompt(context, prompt)  # for continuation
_format_just_text(response_data)  # for output
_format_verbose(response_data)  # for output
_format_raw(response_data)  # for output

# New functions (to be implemented in next step)
_save_conversation_markdown(response_data, prompt, file_path)
_save_conversation_full_json(response_data, prompt, file_path)
```

## Implementation Notes
- Copy exact logic structure from current `execute_prompt`
- Add conditional save operations based on new parameters
- Maintain all existing error handling and logging
- Preserve return codes: 0 for success, 1 for errors

## LLM Prompt for Implementation

```
Please implement Step 3 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Extract the business logic from execute_prompt into a new prompt_claude function in src/mcp_coder/cli/commands/prompt.py.

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

Copy the exact business logic from execute_prompt:
1. Handle continuation logic (continue_from/continue_latest)
2. Call ask_claude_code_api_detailed_sync
3. Store response if store_response=True 
4. Add conditional calls to _save_conversation_markdown and _save_conversation_full_json (these functions will be implemented in the next step)
5. Format output based on verbosity and print
6. Return 0 for success, 1 for errors

Maintain all existing error handling, logging, and behavior exactly.
```
