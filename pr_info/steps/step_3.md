# Step 3: Implement Mypy Check Function

## WHERE
- File: `workflows/implement.py`

## WHAT
Add `check_and_fix_mypy()` function to handle mypy checking with fix attempts.

### Function Signature:
```python
def check_and_fix_mypy(project_dir: Path, conversation_content: list) -> bool:
    """Run mypy check and attempt fixes if issues found. Returns True if clean."""
```

## HOW
- **Import**: Add MCP tool import at top of file
- **Function**: Add before `process_single_task()` function
- **Integration**: Will be called from `process_single_task()` in next step

## ALGORITHM
```
1. Run mypy check via MCP run_mypy_check()
2. If no errors, return True
3. If errors found, loop up to 3 times:
   - Get mypy fix prompt and call ask_llm()
   - Append fix attempt to conversation_content
   - Re-run mypy check
4. Return final mypy status (True if clean)
```

## DATA
### Parameters:
- **project_dir**: `Path` - Project directory for mypy check
- **conversation_content**: `list[str]` - Conversation log to append to

### Return Value:
- **bool**: `True` if mypy clean, `False` if issues remain

### Internal Variables:
- **max_attempts**: `3`
- **attempt_count**: `int` counter
- **mypy_result**: `str` from MCP tool

## LLM Prompt for This Step

```
Reference: pr_info/steps/summary.md

Implement Step 3: Add mypy check function to workflows/implement.py

Add the check_and_fix_mypy() function that:
1. Uses the MCP run_mypy_check() tool available in this environment
2. If mypy errors found, attempts to fix them using ask_llm() with the mypy fix prompt
3. Tries max 3 fix attempts, then gives up
4. Appends each fix attempt to conversation_content list
5. Returns True if mypy is clean, False otherwise

Import needed: The MCP tools are already available in this environment via function calls.

The tests from Step 2 should now pass. This implements the core mypy checking logic.
```
