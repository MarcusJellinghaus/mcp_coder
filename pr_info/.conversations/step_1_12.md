# Implementation Task: Add file existence check for `pr_info/.commit_message.txt` to `.github/workflows/ci.yml` in `check-forbidden-folders` job

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

Current task from TASK_TRACKER.md: Add file existence check for `pr_info/.commit_message.txt` to `.github/workflows/ci.yml` in `check-forbidden-folders` job

Please implement this task step by step.

## LLM Response:
**Step 3 is now complete.** Here's a summary of what was done:

## Step 3: Update CI Pipeline - Forbidden File Check ✅

### Completed sub-tasks:

1. **Added file existence check** to `.github/workflows/ci.yml`:
   - Added a bash conditional check for `pr_info/.commit_message.txt` in the `check-forbidden-folders` job
   - The check sets `ERROR=1` and displays an error message if the file exists
   - Otherwise displays a success message

2. **Verified YAML syntax** - The YAML structure is valid with proper indentation and formatting

3. **Prepared git commit message** - Written to `pr_info/.commit_message.txt`:
   ```
   ci: add forbidden file check for commit message file
   
   Add file existence check for pr_info/.commit_message.txt to the
   check-forbidden-folders job in CI pipeline. This prevents the
   transient commit message file from being accidentally committed
   to pull requests.
   ```

The CI workflow now blocks PRs that accidentally include the transient commit message file.

---
Generated on: 2026-01-19T17:31:18.055845