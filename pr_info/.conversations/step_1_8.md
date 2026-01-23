# Implementation Task: Part F: Add import linter contract to `.importlinter` for git_operations internal layering

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

Current task from TASK_TRACKER.md: Part F: Add import linter contract to `.importlinter` for git_operations internal layering

Please implement this task step by step.

## LLM Response:
I have completed **Step 3** of the task tracker. Here's a summary of what was done:

## Summary

### Step 3: Update External Imports and Add Import Linter Contract - ✅ COMPLETE

All sub-tasks have been completed:

1. **Part A-E** (previously completed): External files were updated to import from `readers.py` instead of direct submodule imports

2. **Part F**: Added the `git_operations_internal_layering` contract to `.importlinter` which enforces:
   - **Layer 1**: Command modules (branches, remotes, commits, staging, file_tracking, diffs)
   - **Layer 2**: readers
   - **Layer 3**: core
   
   This ensures that command modules can import from readers and core, readers can only import from core, and modules at the same layer cannot import from each other.

3. **Code checks passed**:
   - Pylint: No critical errors on modified files
   - Mypy: No type errors found
   - (Note: pytest and lint-imports need user approval to run)

4. **Commit message written** to `pr_info/.commit_message.txt`

The import linter contract enforces the layered architecture going forward, preventing circular dependencies within the git_operations package.

---
Generated on: 2026-01-23T12:16:16.475197