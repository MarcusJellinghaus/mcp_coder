# Implementation Task: Add CLI flag usage examples

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

Current task from TASK_TRACKER.md: Add CLI flag usage examples

Please implement this task step by step.

## LLM Response:
Perfect! I have successfully completed the "Add CLI flag usage examples" sub-task from Step 5. Here's what I accomplished:

## Summary

I added comprehensive CLI flag usage examples to the README.md file, enhancing the coordinator command documentation with:

### Added to README.md:
1. **Enhanced Examples Section** - Replaced the single basic example with multiple practical examples showing different flag combinations
2. **CLI Flag Usage Scenarios** - Added detailed explanations of when to use each flag:
   - `--force-refresh` for bypassing cache when fresh data is needed
   - `--log-level DEBUG` for troubleshooting
   - Combined flags for detailed cache bypass logging
3. **Practical Use Cases** - Specific scenarios where each flag combination is most appropriate

### Key improvements:
- **Multiple command examples** showing progression from basic to advanced usage
- **Scenario-based guidance** explaining when each flag is most useful  
- **Practical context** for troubleshooting and different development workflows
- **Clear flag descriptions** with real-world applications

The documentation now provides users with practical guidance on:
- Normal cache usage for regular workflows
- Force refresh scenarios (new issues, labels, troubleshooting)
- Debug logging for cache behavior analysis
- Combining flags for comprehensive troubleshooting

The task has been marked as complete (✅) in the TASK_TRACKER.md, and the next sub-task in Step 5 is "Create troubleshooting section for cache-related issues".

---
Generated on: 2025-12-31T20:11:41.308507