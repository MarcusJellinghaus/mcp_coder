# Step 3: Implement Response File Discovery Utility Function

## LLM Prompt
```
Implement the _find_latest_response_file() utility function with strict ISO timestamp validation and user feedback. The function should only accept properly formatted response files and show which file was selected.

Reference: PR_Info/steps/summary.md and PR_Info/steps/Decisions.md - implementing --continue parameter for mcp-coder prompt command.

This is step 3 of 7: Implementing the core utility function with strict validation after TDD from step 2.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Location**: Add function after existing utility functions (after `_build_context_prompt`)
- **Imports**: Add `glob`, `os.path`, `re` to existing imports

## WHAT
Main function signature:
```python
def _find_latest_response_file(responses_dir: str = ".mcp-coder/responses") -> Optional[str]:
    """Find the most recent response file by filename timestamp with strict validation."""
```

## HOW
- **Integration**: Place after existing helper functions, before `execute_prompt()`
- **Strict Validation**: Use regex to validate ISO timestamp pattern
- **User Feedback**: Print selected filename to user (per Decision #6)
- **Error Handling**: Use try-catch for directory access and file operations
- **Logging**: Add debug logging for file discovery process

## ALGORITHM
```
1. CHECK if responses directory exists, return None if not
2. GLOB for "response_*.json" pattern in directory
3. VALIDATE each file matches strict ISO timestamp pattern using regex
4. SORT validated filenames by timestamp (lexicographic sort works for ISO format)
5. SHOW selected filename to user for transparency
6. RETURN latest file path or None if no valid files found
```

## DATA
**Function Implementation**:
```python
def _find_latest_response_file(responses_dir: str = ".mcp-coder/responses") -> Optional[str]:
    """Find the most recent response file by filename timestamp with strict validation.
    
    Args:
        responses_dir: Directory containing response files
        
    Returns:
        Path to latest response file, or None if none found
    """
    # Implementation with strict validation and user feedback
```

**Validation Pattern**:
```python
# ISO timestamp pattern: response_YYYY-MM-DDTHH-MM-SS.json
timestamp_pattern = r"^response_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.json$"
```

**User Feedback**:
```python
# Show selected file to user (Decision #6)
print(f"Found {len(valid_files)} previous sessions, continuing from: {selected_file}")
```

**Return Values**:
- **Success**: `"/path/to/.mcp-coder/responses/response_2025-09-19T14-30-22.json"`
- **No directory/files**: `None` (caller handles info message and continues)
- **No valid files**: `None` (strict validation, caller handles continuation)
- **Error cases**: `None` (with logging)
