# Implementation Task: `implementation_review.md` uses dynamic base branch for diff

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
- Write commit message to `pr_info/.commit_message.txt`
- Do NOT commit - just write the message to the file

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: `implementation_review.md` uses dynamic base branch for diff

Please implement this task step by step.

## LLM Response:
Step 3 is now complete. Here's a summary of what was accomplished:

## Step 3 Complete: Update Slash Commands for Dynamic Base Branch

### Changes Made:

1. **`.claude/commands/implementation_review.md`**
   - Added base branch detection: `BASE_BRANCH=$(mcp-coder gh-tool get-base-branch)`
   - Updated diff command to use `${BASE_BRANCH}...HEAD` instead of `main...HEAD`

2. **`.claude/commands/rebase.md`**
   - Updated title from "Rebase Branch onto Main" to "Rebase Branch onto Base Branch"
   - Added new "Determine Base Branch" section with detection command
   - Updated rebase command to use `origin/${BASE_BRANCH}` instead of `origin/main`

3. **`.claude/commands/check_branch_status.md`**
   - Updated table text from "onto main" to "onto base branch"

### All Sub-tasks Completed:
- [x] `implementation_review.md` uses dynamic base branch for diff
- [x] `rebase.md` uses dynamic base branch for rebase
- [x] `check_branch_status.md` text updated (no hardcoded "main")
- [x] All markdown formatting preserved
- [x] Commands remain functional with same allowed-tools

Commit message written to `pr_info/.commit_message.txt`.

---
Generated on: 2026-01-31T18:54:29.109227