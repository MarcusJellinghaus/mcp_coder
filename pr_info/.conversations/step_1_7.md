# Implementation Task: Search for all patches containing "vscodeclaude" in tests/

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

Current task from TASK_TRACKER.md: Search for all patches containing "vscodeclaude" in tests/

Please implement this task step by step.

## LLM Response:
Now I've completed the first sub-task. Let me summarize what I found:

## Summary: Search for vscodeclaude patches in tests/

I searched all test files and found the following files containing `vscodeclaude` references that need patch updates:

### Tests in `tests/utils/vscodeclaude/` (12 files)

All these files have imports and patches from `mcp_coder.utils.vscodeclaude.*` that need to be updated to `mcp_coder.workflows.vscodeclaude.*`:

1. **test_cleanup.py** - 6 patches on `mcp_coder.utils.vscodeclaude.cleanup.*` and `sessions.*`
2. **test_config.py** - 4 patches on `mcp_coder.utils.vscodeclaude.config._get_coordinator`
3. **test_helpers.py** - Imports only (no patches), from `mcp_coder.utils.vscodeclaude.helpers`
4. **test_issues.py** - 6 patches on `mcp_coder.utils.vscodeclaude.issues._get_coordinator` and `get_all_cached_issues`
5. **test_orchestrator_compatibility.py** - Imports only from `mcp_coder.utils.vscodeclaude.orchestrator`
6. **test_orchestrator_launch.py** - 2 patches on `mcp_coder.utils.vscodeclaude.orchestrator.subprocess.Popen`
7. **test_orchestrator_regenerate.py** - Imports from `mcp_coder.utils.vscodeclaude.orchestrator`
8. **test_orchestrator_sessions.py** - 12+ patches on `mcp_coder.utils.vscodeclaude.orchestrator.*`
9. **test_sessions.py** - 8+ patches on `mcp_coder.utils.vscodeclaude.sessions.*`
10. **test_status.py** - 8+ patches on `mcp_coder.utils.vscodeclaude.status.*`
11. **test_types.py** - Imports only from `mcp_coder.utils.vscodeclaude.types`
12. **test_workspace.py** - 6+ patches on `mcp_coder.utils.vscodeclaude.workspace.*`

### Tests in `tests/cli/commands/coordinator/` (1 file)

13. **test_vscodeclaude_cli.py** - Imports from `mcp_coder.cli.commands.coordinator.vscodeclaude_templates` (templates are in CLI layer, not moving)

### Already Updated

14. **test_core.py** - Already patching `mcp_coder.utils.user_config.get_cache_refresh_minutes` (correct location)

The first sub-task is complete. The next step is to search for `get_cache_refresh_minutes` patches, which I can see is already done correctly in `test_core.py`.

---
Generated on: 2026-01-31T12:06:29.275042