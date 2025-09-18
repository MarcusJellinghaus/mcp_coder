# Step 7: Add Storage Functionality Tests

## LLM Prompt
```
Based on the summary in PR_Info/steps/summary.md, implement Step 7: Add tests for the --store-response functionality.

Create tests for the session storage capability:
- Test storing complete session data to .mcp-coder/responses/ directory
- Test file creation with proper timestamp naming
- Test JSON structure of stored session data
- Use the same test patterns established in previous steps

This adds the foundation for conversation continuity and detailed debugging storage.
```

## WHERE
- **File**: `tests/cli/commands/test_prompt.py` (extend existing)
- **Test Addition**: Add to existing test module

## WHAT
- **New Test Function**: `test_store_response()`
- **Test Logic**: Mock args with store_response flag, verify file creation and content
- **File System Mocking**: Mock file operations to test storage behavior

## HOW
- **Mock Setup**: Mock args with `store_response=True`
- **File System Mocking**: Mock file creation and directory operations
- **Content Verification**: Check stored JSON structure includes prompt, response, metadata
- **Path Verification**: Verify files stored in `.mcp-coder/responses/` with timestamp naming

## ALGORITHM
```
1. Setup mock args with prompt and store_response=True
2. Mock file system operations (os.makedirs, file write)
3. Mock ask_claude_code_api_detailed_sync with complete response
4. Call execute_prompt function  
5. Verify file operations called correctly:
   - Directory creation (.mcp-coder/responses/)
   - File written with timestamp naming
   - JSON content includes prompt, response, metadata
```

## DATA
- **Input**: `argparse.Namespace` with `prompt` and `store_response=True`
- **Mock Operations**: File system operations for directory and file creation
- **Expected JSON Structure**:
  - `prompt`: Original user prompt
  - `response_data`: Complete API response
  - `metadata`: Timestamp, working directory, model info
- **File Path**: `.mcp-coder/responses/response_YYYY-MM-DDTHH-MM-SS.json`
- **Assertions**: Verify file operations and JSON content structure
