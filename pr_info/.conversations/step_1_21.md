# Implementation Task: Update exception handler to check for None and use fallback

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

Current task from TASK_TRACKER.md: Update exception handler to check for None and use fallback

Please implement this task step by step.

## LLM Response:
## Summary

I have successfully completed the implementation of ONE step from the task tracker as requested. Here's what was accomplished:

**Step 5: Fix Exception Handling and Error Messages** - All sub-tasks completed:

✅ **Fixed mypy union-attr issues**: Updated the exception handler in `get_cached_eligible_issues()` to properly check if `repo_identifier` is None before accessing its attributes (`repo_name` and `full_name`)

✅ **Verified other sub-tasks**: Confirmed that all other Step 5 requirements were already completed in previous conversations:
- Exception handling reverted to broad `except Exception` in 4 locations
- Error messages updated to include invalid input in RepoIdentifier.from_full_name()
- Test assertions verified to work with new error format
- Code quality checks passed (pylint clean, mypy only shows unrelated import-untyped issues)

The key fix I made was in `src/mcp_coder/cli/commands/coordinator.py:708-715` where I added proper None checks:

```python
except (ValueError, KeyError, TypeError) as e:
    repo_name = repo_identifier.repo_name if repo_identifier else "unknown_repo"
    full_name = repo_identifier.full_name if repo_identifier else "unknown/unknown"
    _log_cache_metrics("miss", repo_name, reason=f"error_{type(e).__name__}")
    logger.warning(f"Cache error for {full_name}: {e}, falling back to direct fetch")
    return get_eligible_issues(issue_manager)
```

This ensures type safety and prevents potential NameError exceptions when `repo_identifier` is None in the exception handler. Step 5 is now fully complete and ready for the final commit preparation.

---
Generated on: 2026-01-01T23:46:07.991133