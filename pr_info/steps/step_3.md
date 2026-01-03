# Step 3: Integrate Footer Stripping into Commit Message Generation

## LLM Prompt

```
Based on the summary in `pr_info/steps/summary.md` and the function implemented in Step 2, integrate the `strip_claude_footers()` function into the existing commit message generation flow in `generate_commit_message_with_llm()`. 

Make minimal changes to the existing function - add only one line to call the footer stripping after parsing. Also update existing tests to handle the new footer stripping behavior.
```

## WHERE: File Locations
- **Source File**: `src/mcp_coder/utils/commit_operations.py` 
- **Integration Point**: `generate_commit_message_with_llm()` function, line ~152 (after `parse_llm_commit_response()`)
- **Test File**: `tests/utils/test_commit_operations.py`
- **Test Updates**: Existing `TestGenerateCommitMessageWithLLM` test methods

## WHAT: Integration Changes Required

### Source Code Change
**Exact Integration Point** (after line ~152):
```python
# Step 5: Parse and validate LLM response
logger.debug("Parsing LLM response into commit message")
try:
    commit_message, _ = parse_llm_commit_response(response)
    
    # NEW LINE: Strip Claude Code footers from commit message
    commit_message = strip_claude_footers(commit_message)
    
    if not commit_message or not commit_message.strip():
        # ... existing validation continues
```

### Test Updates Required
**Update Test Mocks**: Existing tests that mock `parse_llm_commit_response()` should return messages with footers to verify stripping works.

## HOW: Implementation Details

### Source Integration
- **Single Line Addition**: One function call after parsing, before validation
- **No Function Signature Changes**: Existing function parameters unchanged
- **Preserve Error Handling**: Existing try/catch blocks remain intact
- **Maintain Logging**: Existing debug logs unchanged

### Test Updates
```python
# Update mock return values to include footers
mock_ask_llm.return_value = "feat: add new feature\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
```

## ALGORITHM: Integration Flow

```
1. EXISTING: Parse LLM response into commit_message, body
2. NEW: Strip Claude footers from commit_message  
3. EXISTING: Validate commit_message not empty
4. EXISTING: Validate first line not empty
5. EXISTING: Return success, commit_message, None
```

## DATA: Integration Impact

### Before Integration
**LLM Response →** `parse_llm_commit_response()` **→** Validation **→** Return

### After Integration  
**LLM Response →** `parse_llm_commit_response()` **→** `strip_claude_footers()` **→** Validation **→** Return

### Test Data Updates

**Original Mock Response:**
```
"feat: add new feature"
```

**Updated Mock Response (with footers):**
```
"feat: add new feature\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
```

**Expected Final Result:**
```
"feat: add new feature"
```

### Error Handling Preservation
- **Empty Message After Stripping**: Existing empty message validation catches this
- **Parse Errors**: Existing exception handling unchanged
- **Footer Stripping Errors**: Function is safe and won't throw exceptions

## Success Criteria
- [ ] Single line added to `generate_commit_message_with_llm()`
- [ ] Integration point is after parsing, before validation
- [ ] All existing tests still pass
- [ ] Updated test mocks include footer data to verify stripping
- [ ] No changes to existing function signatures
- [ ] No disruption to existing error handling
- [ ] End-to-end functionality verified: LLM response with footers → clean commit message