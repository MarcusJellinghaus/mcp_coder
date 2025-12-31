# Implementation Task: Create troubleshooting section for cache-related issues

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

Current task from TASK_TRACKER.md: Create troubleshooting section for cache-related issues

Please implement this task step by step.

## LLM Response:
Excellent! I have successfully completed the sub-task "Create troubleshooting section for cache-related issues". 

## Summary

I implemented a comprehensive troubleshooting section for cache-related issues in the README.md file. The section includes:

1. **5 common problem scenarios** with step-by-step solutions:
   - Stale data issues (with `--force-refresh` solution)
   - Cache file corruption (with manual cache cleanup commands)
   - API rate limiting (with cache usage recommendations)
   - Permission issues (with directory creation commands)
   - Multiple repository conflicts (with specific debugging approach)

2. **Configuration examples** showing different cache refresh intervals for various use cases (active development, stable repositories)

3. **Platform-specific cache file locations** for Linux/macOS and Windows

The troubleshooting section provides practical, actionable solutions that users can follow when encountering cache-related problems with the coordinator command. It integrates seamlessly with the existing cache documentation and follows the same style and format as the rest of the README.

The sub-task has been marked as completed in both my todo list and the TASK_TRACKER.md file.

---
Generated on: 2025-12-31T20:12:51.494383