# Step 4: Test Workflow Integration

## Objective
Test the complete workflow integration by running the implement script and verifying it works with existing mcp-coder functionality.

## WHERE
- Test execution from project root
- Verify `pr_info/.conversations/` directory creation
- Check integration with existing modules

## WHAT
### Main Testing Activities
- Manual execution test of `workflows/implement.bat`
- Verify task tracker integration
- Test prompt retrieval functionality
- Validate conversation storage
- Confirm formatter and commit integration

## HOW
### Integration Points Testing
```python
# Test areas
- Task tracker: get_incomplete_tasks() returns expected data
- Prompt manager: get_prompt() retrieves template successfully  
- LLM interface: ask_llm() completes without errors
- Formatters: format_code() processes files correctly
- Git operations: commit command executes successfully
```

## ALGORITHM
```
1. Create test task in pr_info/TASK_TRACKER.md if needed
2. Run workflows/implement.bat from project root
3. Verify each step executes successfully with timestamp output
4. Check conversation file created in .conversations/
5. Verify code formatting and commit completion
```

## DATA
### Test Validation Points
- **Task Detection**: Script identifies incomplete tasks correctly
- **Prompt Access**: Successfully retrieves implementation prompt template
- **LLM Response**: Receives and processes LLM response
- **File Creation**: `pr_info/.conversations/step_N.md` created with content
- **Formatting**: Code files processed by black/isort
- **Commit**: Git commit created with auto-generated message

### Expected Outputs
- Console output with timestamps for each step
- New conversation file with LLM interaction
- Formatted source code
- New git commit

## Implementation Notes
- This is manual testing - not unit tests (keeping it simple)
- Focus on end-to-end workflow functionality
- Verify error messages are helpful if something fails
- Test with actual pr_info structure if available

## LLM Prompt
```
Please look at pr_info/steps/summary.md and implement Step 4.

Test the workflow integration:
1. Ensure there's at least one incomplete task in pr_info/TASK_TRACKER.md for testing
2. Run the implement workflow manually 
3. Verify each step executes correctly with proper output
4. Check that conversation files are created
5. Validate that formatting and commit operations work
6. Fix any integration issues found

This is manual testing - just verify the workflow works end-to-end with existing mcp-coder functionality.
Focus only on Step 4 testing and fixes.
```
