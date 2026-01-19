# Implementation Finalisation Capability - Summary

## Overview

Add a finalisation capability that verifies and completes any remaining unchecked tasks in `TASK_TRACKER.md` before transitioning to code review. This ensures no tasks are left incomplete due to LLM oversight or session boundaries.

## Architectural / Design Changes

### Design Philosophy
- **KISS Principle**: The finalisation logic is entirely prompt-driven - the LLM handles all decisions (checking commits, handling missing step files, running quality checks)
- **No new Python logic modules**: The prompt instructs the LLM what to do; no complex Python code needed
- **Follows existing patterns**: Uses same `ask_llm()` integration as task tracker preparation

### Integration Point
The finalisation step integrates into `run_implement_workflow()` in `src/mcp_coder/workflows/implement/core.py`:

```
Step 4: Process all incomplete tasks (loop) ← existing
Step 5: Run final mypy check ← existing
Step 5.5: Run finalisation ← NEW (before label update)
Step 6: Show final progress summary ← existing
Step 7: Update GitHub issue label ← existing
```

### Key Decisions (from Issue #247)

| Aspect | Decision |
|--------|----------|
| **Commit message tasks** | Auto-mark `[x]` if commits already exist |
| **Step files missing** | Work without them - analyse codebase based on task names |
| **Quality checks** | Run pylint/pytest/mypy only if code changes were made |
| **Single commit** | One commit at end of finalisation |
| **Auto-push** | Only in workflow mode (`update_labels=True`) |
| **All tasks complete** | Skip finalisation entirely |
| **Cannot complete task** | Don't mark done, explain the issue |

## Files to Create/Modify

| Action | File | Purpose |
|--------|------|---------|
| **Create** | `.claude/commands/implementation_finalise.md` | Slash command for manual use |
| **Modify** | `src/mcp_coder/workflows/implement/core.py` | Add finalisation step to workflow |
| **Modify** | `tests/workflows/implement/test_core.py` | Add tests for finalisation integration |

## Dependencies

- Uses existing `ask_llm()` from `mcp_coder.llm.interface`
- Uses existing `has_incomplete_work()` from `mcp_coder.workflow_utils.task_tracker`
- Uses existing `get_full_status()` from `mcp_coder.utils`
- Uses existing `commit_changes()` and `push_changes()` from task_processing module

## Success Criteria

1. ✅ Slash command `/implementation_finalise` available for manual use
2. ✅ Workflow runs finalisation after task loop, before label update
3. ✅ Commit message tasks auto-marked when commits exist
4. ✅ Works when `pr_info/steps/` folder is missing
5. ✅ Quality checks run only if code changes made
6. ✅ Single commit with message written to `pr_info/.commit_message.txt`
7. ✅ Auto-push in workflow mode only
8. ✅ Skips if no incomplete tasks found
