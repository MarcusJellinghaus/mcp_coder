# Step 2: Complete Mypy Integration

## WHERE
- File: `workflows/implement.py`

## WHAT
Implement `check_and_fix_mypy()` function and integrate it into the main workflow.

### Function Signature:
```python
def check_and_fix_mypy(project_dir: Path, conversation_content: list) -> bool:
    """Run mypy check and attempt fixes if issues found. Returns True if clean."""
```

## HOW
- **Function**: Add `check_and_fix_mypy()` before `process_single_task()` function  
- **Integration**: Call from `process_single_task()` after LLM response, before formatters
- **Smart retry**: Only count retries when mypy feedback is identical to previous attempts

## ALGORITHM
```
1. Run mypy check via MCP run_mypy_check()
2. If no errors, return True  
3. If errors found, retry loop:
   - Get mypy fix prompt and call ask_llm()
   - Append fix attempt to conversation_content
   - Re-run mypy check
   - Only increment retry counter if feedback identical to previous
   - Stop after 3 identical feedbacks
4. Integrate into process_single_task() after LLM response
5. Return final mypy status (True if clean)
```

## DATA
### Parameters:
- **project_dir**: `Path` - Project directory for mypy check
- **conversation_content**: `list[str]` - Conversation log to append to

### Return Value:
- **bool**: `True` if mypy clean, `False` if issues remain

### Internal Variables:
- **max_identical_attempts**: `3`
- **previous_outputs**: `list[str]` to track feedback history
- **mypy_result**: `str` from MCP tool

## LLM Prompt for This Step

```
Reference: pr_info/steps/summary.md

Implement Step 2: Complete mypy integration into workflows/implement.py

Tasks:
1. Add check_and_fix_mypy() function with smart retry logic:
   - Uses MCP run_mypy_check() tool
   - Smart retry: only counts retries when mypy feedback is identical
   - Stops after 3 identical feedbacks (no progress being made)
   - Appends each fix attempt to conversation_content

2. Integrate into process_single_task() workflow:
   - Call after LLM response and conversation save
   - Call before run_formatters()
   - Update conversation_content with fix attempts

Use existing patterns: MCP function calls, ask_llm(), conversation logging.
```
