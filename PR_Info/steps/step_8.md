# Step 8: Implement Storage Functionality

## LLM Prompt
```
Based on the summary in PR_Info/steps/summary.md, implement Step 8: Add --store-response functionality to make Step 7 tests pass.

Implement the session storage capability:
- Add _store_response() function to save complete sessions
- Update execute_prompt() to handle storage when requested
- Create .mcp-coder/responses/ directory structure
- Save complete session data with timestamp naming for future continuation

Build on existing functionality, adding the storage layer for conversation continuity.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py` (extend existing)
- **Functions**: Add `_store_response()`, update `execute_prompt()`

## WHAT
- **New Function**: `_store_response(response_data: dict, store_path: str = None) -> str`
- **Enhanced Logic**: Handle storage flag in execute_prompt()
- **Directory Management**: Create `.mcp-coder/responses/` directory if needed
- **File Naming**: Use timestamp-based naming for unique session files

## HOW
- **Storage Integration**: Check args.store_response flag, call _store_response() after API call
- **Directory Creation**: Use os.makedirs() to ensure response directory exists
- **JSON Storage**: Save complete session data as JSON with proper formatting
- **Timestamp Naming**: Generate filename like `response_2025-09-18T14-30-22.json`

## ALGORITHM
```
1. In execute_prompt(): Check args.store_response flag
2. If storing, call _store_response() after getting API response
3. _store_response() implementation:
   - Create .mcp-coder/responses/ directory if not exists
   - Generate timestamp-based filename
   - Create complete session JSON with prompt + response + metadata
   - Write JSON file and return file path
4. Continue with normal output formatting and display
```

## DATA
- **Input**: Enhanced `argparse.Namespace` with `store_response` attribute
- **Storage Location**: `.mcp-coder/responses/response_ISO-TIMESTAMP.json`
- **JSON Structure**:
  ```json
  {
    "prompt": "user's original prompt",
    "response_data": {complete API response},
    "metadata": {
      "timestamp": "2025-09-18T14:30:22Z",
      "working_directory": "/path/to/project", 
      "model": "claude-3-5-sonnet"
    }
  }
  ```
- **Return**: File path of stored session for potential user reference
