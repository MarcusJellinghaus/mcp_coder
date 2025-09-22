# Step 2: Implement Response File Discovery Utility Function

## LLM Prompt
```
Implement the _find_latest_response_file() utility function in the prompt command module. The function should find the most recent response_*.json file by sorting filenames with ISO timestamps.

Reference: PR_Info/steps/summary.md - implementing --continue-from-last parameter for mcp-coder prompt command.

This is step 2 of 6: Implementing the core utility function after TDD from step 1.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Location**: Add function after existing utility functions (after `_build_context_prompt`)
- **Imports**: Add `glob`, `os.path` to existing imports

## WHAT
Main function signature:
```python
def _find_latest_response_file(responses_dir: str = ".mcp-coder/responses") -> Optional[str]:
    """Find the most recent response file by filename timestamp."""
```

## HOW
- **Integration**: Place after existing helper functions, before `execute_prompt()`
- **Error Handling**: Use try-catch for directory access and file operations
- **Logging**: Add debug logging for file discovery process
- **Type Hints**: Follow existing code patterns with proper typing

## ALGORITHM
```
1. CHECK if responses directory exists, return None if not
2. GLOB for "response_*.json" pattern in directory
3. FILTER valid response files (proper naming pattern)
4. SORT filenames by timestamp (lexicographic sort works for ISO format)
5. RETURN latest file path or None if no valid files found
```

## DATA
**Function Implementation**:
```python
def _find_latest_response_file(responses_dir: str = ".mcp-coder/responses") -> Optional[str]:
    """Find the most recent response file by filename timestamp.
    
    Args:
        responses_dir: Directory containing response files
        
    Returns:
        Path to latest response file, or None if none found
    """
    # Implementation here...
```

**Internal Data Structures**:
```python
# File pattern matching
pattern = os.path.join(responses_dir, "response_*.json")
matching_files: List[str] = glob.glob(pattern)

# Sorting (ISO timestamp allows lexicographic sorting)
sorted_files: List[str] = sorted(matching_files, reverse=True)
```

**Return Values**:
- **Success**: `"/path/to/.mcp-coder/responses/response_2025-09-19T14-30-22.json"`
- **No directory**: `None`
- **No files**: `None`
- **Error cases**: `None` (with logging)
