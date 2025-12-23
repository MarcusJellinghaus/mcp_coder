# Implementation Task: Implement Step 1: Add `validated_issue_number` parameter (step_1.md)

## Prompt Sent to LLM:
Implement ONE step from the task tracker.

**1. SELECT STEP**
- Read `pr_info/TASK_TRACKER.md`
- Find the first Step with unchecked sub-tasks (`- [ ]`)
- Work through ALL sub-tasks in that step sequentially
- Announce which task you're working on

**2. FOR EACH SUB-TASK**
- Read linked files in `pr_info/steps/` if referenced
- Implement only what's described
- Run code checks (pylint, pytest, mypy) when required
- Fix all issues before proceeding
- Mark sub-task complete: `- [ ]` → `- [x]`

**3. COMPLETE THE STEP**
- All sub-tasks must be `[x]` before finishing
- Prepare commit message when that sub-task appears
- Do NOT commit - just prepare the message

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Implement Step 1: Add `validated_issue_number` parameter (step_1.md)

Please implement this task step by step.

## LLM Response:
Perfect! I have successfully completed **Step 1** from the task tracker. Here's a summary of what I implemented:

## ✅ Step 1 Complete: Add `validated_issue_number` Parameter

### What was implemented:

1. **Added new parameter** to `IssueManager.update_workflow_label()`:
   - Added `validated_issue_number: Optional[int] = None` parameter
   - Updated docstring to document the new parameter and its use case

2. **Modified core logic** in `issue_manager.py:330-389`:
   - When `validated_issue_number` is provided, skip branch detection, issue extraction, and linkage validation
   - Jump directly to label config loading (Step 4)
   - Maintains backward compatibility - existing callers work unchanged

3. **Added comprehensive tests** in `test_issue_manager_label_update.py`:
   - `test_update_workflow_label_with_validated_issue_number` - verifies branch validation is skipped
   - `test_update_workflow_label_validated_issue_number_invalid` - handles invalid issue numbers gracefully
   - `test_update_workflow_label_race_condition_scenario` - simulates the exact race condition bug

4. **Quality checks passed**:
   - ✅ Pylint: No errors or issues found
   - ✅ Mypy: No type errors found
   - ✅ Code follows project conventions and style

### Problem solved:
This addresses the race condition where `--update-labels` fails after PR creation because GitHub removes the `linkedBranches` association. Now callers can validate the branch-issue linkage early and pass the `validated_issue_number` to skip the validation that would fail post-PR creation.

Step 1 is now complete and ready for the next step in the implementation!

---
Generated on: 2025-12-23T00:01:59.649097