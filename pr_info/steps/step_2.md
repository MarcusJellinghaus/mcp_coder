# Step 2: Implement strip_claude_footers() Function

## LLM Prompt

```
Based on the summary in `pr_info/steps/summary.md` and the tests from Step 1, implement the `strip_claude_footers()` function in `src/mcp_coder/utils/commit_operations.py`. 

The function must pass all the tests implemented in Step 1. Follow the KISS principle - use simple string operations, no regex patterns. The function should work backwards from the end of the message to remove Claude Code footers.
```

## WHERE: File Location
- **File**: `src/mcp_coder/utils/commit_operations.py`
- **Location**: Add function after existing functions, before main `generate_commit_message_with_llm()`
- **Module**: Existing `mcp_coder.utils.commit_operations` module

## WHAT: Function Signature

```python
def strip_claude_footers(message: str) -> str:
    """Remove Claude Code footer lines from commit message.
    
    Removes lines starting with 🤖 (robot emoji) and exact matches for
    'Co-Authored-By: Claude <noreply@anthropic.com>' from the end of the message.
    Also cleans up trailing blank lines.
    
    Args:
        message: The commit message to clean
        
    Returns:
        Cleaned commit message with Claude footers removed
    """
```

## HOW: Implementation Details

### No New Imports Needed
- Use only Python built-in string operations
- Function is self-contained within existing module

### Integration Preparation
- Function will be called from `generate_commit_message_with_llm()` in Step 3
- No changes to function signature of existing functions

## ALGORITHM: Core Logic (Simple Backward Iteration)

```
1. IF message is empty/None, RETURN unchanged
2. SPLIT message into lines array
3. WHILE last line is footer or empty:
   - CHECK if line starts with '🤖'
   - CHECK if line equals 'Co-Authored-By: Claude <noreply@anthropic.com>'  
   - CHECK if line is empty/whitespace
   - REMOVE last line if any condition matches
4. JOIN lines back to string and RETURN
```

## DATA: Function Behavior

### Input/Output Examples

**Input:** Message with both footers
```
"feat: add feature\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
```
**Output:** Clean message
```
"feat: add feature"
```

**Input:** Message with no footers
```
"feat: clean commit"
```
**Output:** Unchanged
```
"feat: clean commit"
```

**Input:** Empty/None
```
"" or None
```
**Output:** Unchanged
```
"" or original None
```

### Footer Patterns to Match
1. **Robot Emoji Pattern**: Any line that `strip().startswith('🤖')`
2. **Co-Authored Pattern**: Exact match `strip() == 'Co-Authored-By: Claude <noreply@anthropic.com>'`
3. **Empty Lines**: Any line where `strip() == ''`

### Key Implementation Points
- **Work Backwards**: Remove from end only using `lines.pop()` 
- **Independent Patterns**: Handle both footer types in same loop
- **Preserve Content**: Only remove from end, never from middle
- **Handle Edge Cases**: Empty strings, None values, whitespace-only lines

## Success Criteria
- [ ] Function implemented with simple, readable logic
- [ ] All tests from Step 1 pass
- [ ] No regex patterns used (KISS principle)
- [ ] Function handles edge cases gracefully
- [ ] Docstring clearly explains behavior
- [ ] No disruption to existing functions in the module