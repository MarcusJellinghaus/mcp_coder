# Step 4: Integrate Mypy Check Into Workflow

## WHERE  
- File: `workflows/implement.py`
- Function: `process_single_task()`

## WHAT
Integrate `check_and_fix_mypy()` into the main workflow after LLM response.

### Integration Point:
- **After**: LLM response and initial conversation save
- **Before**: `run_formatters()` call
- **Modification**: Update conversation content with mypy fix attempts

## HOW
- **Call**: `check_and_fix_mypy(project_dir, conversation_parts)`
- **Logging**: Add log step for mypy checking
- **Conversation**: Update conversation_content with mypy attempts before final save

## ALGORITHM
```
1. After LLM response, before formatters:
2. Call check_and_fix_mypy(project_dir, conversation_parts)  
3. Log mypy check result
4. Update final conversation_content with any fix attempts
5. Continue with existing workflow (formatters, commit, push)
```

## DATA
### Modified Variables:
- **conversation_content**: Updated with mypy fix attempts
- **conversation_parts**: List to accumulate all conversation pieces

### Integration Flow:
```
LLM Response → Save Initial → Mypy Check+Fix → Update Conversation → Formatters → Commit → Push
```

## LLM Prompt for This Step

```
Reference: pr_info/steps/summary.md

Implement Step 4: Integrate mypy checking into the main workflow.

Modify the process_single_task() function in workflows/implement.py to:

1. After the LLM responds and initial conversation is prepared
2. Before running formatters
3. Call check_and_fix_mypy() function
4. Update the conversation_content with any mypy fix attempts
5. Continue with existing workflow

The integration should be minimal - just insert the mypy check at the right point and ensure any fix attempts are included in the final conversation log.

Add appropriate logging using the existing log_step() function.
```
