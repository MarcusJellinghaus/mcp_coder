# Implementation Task: Create `tests/cli/commands/test_define_labels.py` from old test file

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

Current task from TASK_TRACKER.md: Create `tests/cli/commands/test_define_labels.py` from old test file

Please implement this task step by step.

## LLM Response:
## Summary

I have completed **Step 3: Move and Update Tests** with all sub-tasks:

### Changes Made:

1. **Created `tests/cli/commands/test_define_labels.py`** - New test file copied from `tests/workflows/test_define_labels.py` with the following updates:
   - Updated all imports from `workflows.define_labels` to `mcp_coder.cli.commands.define_labels`
   - Updated `resolve_project_dir` import to `mcp_coder.workflows.utils`
   - Updated all mock patches from `@patch("workflows.define_labels.LabelsManager")` to `@patch("mcp_coder.cli.commands.define_labels.LabelsManager")`
   - Removed `TestArgumentParsing` class (argument parsing now handled by `main.py`)
   - Updated `TestResolveProjectDir` tests to expect `ValueError` instead of `SystemExit`
   - Updated `TestApplyLabels.test_apply_labels_api_error_raises_runtime_error` to expect `RuntimeError` instead of `SystemExit`
   - Added minimal `TestExecuteDefineLabels` class with 2 tests for CLI wiring

2. **Updated `tests/workflows/implement/test_core.py`** - Changed all tests that expect `SystemExit` from `resolve_project_dir` to expect `ValueError`:
   - `test_resolve_project_dir_invalid_path_raises_value_error`
   - `test_resolve_project_dir_not_directory_raises_value_error`
   - `test_resolve_project_dir_no_git_raises_value_error`
   - `test_resolve_project_dir_permission_error_raises_value_error`
   - `test_resolve_project_dir_resolve_error_raises_value_error`
   - `test_error_recovery_workflow`

### Prepared Git Commit Message:

```
Move define_labels tests to CLI commands and update exception handling

- Create tests/cli/commands/test_define_labels.py from workflows test file
- Update imports to new module paths (mcp_coder.cli.commands.define_labels)
- Update mock patches to new module paths
- Remove TestArgumentParsing class (now handled by main.py argparse)
- Update TestResolveProjectDir to expect ValueError instead of SystemExit
- Update TestApplyLabels to expect RuntimeError instead of SystemExit
- Add minimal TestExecuteDefineLabels class for CLI wiring tests
- Update tests/workflows/implement/test_core.py to expect ValueError

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---
Generated on: 2026-01-08T22:09:10.771720