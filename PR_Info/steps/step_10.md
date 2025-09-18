# Step 10: Implement Continuation Functionality

## LLM Prompt
```
Based on the summary in PR_Info/steps/summary.md, implement Step 10: Add --continue-from functionality to make Step 9 tests pass.

Implement the session continuation capability:
- Add _load_previous_chat() function to load stored sessions
- Update execute_prompt() to handle continuation context
- Integrate previous session context with new prompts
- Maintain conversation continuity for follow-up questions

Build on existing functionality, adding the continuation layer for iterative debugging.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py` (extend existing)
- **Functions**: Add `_load_previous_chat()`, update `execute_prompt()`

## WHAT
- **New Function**: `_load_previous_chat(file_path: str) -> dict`
- **Enhanced Logic**: Handle continuation parameter in execute_prompt()
- **Context Integration**: Combine previous session with new prompt
- **Error Handling**: Basic file existence and JSON parsing (minimal per KISS)

## HOW
- **Continuation Check**: Check args.continue_from parameter in execute_prompt()
- **File Loading**: Read and parse stored session JSON file
- **Context Building**: Extract previous conversation and combine with new prompt
- **API Integration**: Pass enhanced context to ask_claude_code_api_detailed_sync()

## ALGORITHM
```
1. In execute_prompt(): Check args.continue_from parameter
2. If continuing, call _load_previous_chat() to get context
3. _load_previous_chat() implementation:
   - Read JSON file from specified path
   - Parse stored session data
   - Extract previous prompt and response for context
   - Return context dictionary
4. Combine previous context with new prompt
5. Call API with enhanced context/prompt
6. Continue with normal storage and output formatting
```

## DATA
- **Input**: Enhanced `argparse.Namespace` with `continue_from` attribute
- **File Reading**: Load JSON from `.mcp-coder/responses/` or specified path
- **Context Structure**: 
  ```python
  {
    "previous_prompt": "original prompt",
    "previous_response": "Claude's response", 
    "metadata": {...}
  }
  ```
- **Enhanced Prompt**: Combine previous context with new prompt for API call
- **Integration**: Works with all verbosity levels and storage options
- **Error Handling**: Let file/JSON errors crash (following KISS principle)
