# Implementation Task: Add `env_vars` parameter to `ask_claude_code_cli()` in `src/mcp_coder/llm/providers/claude/claude_code_cli.py`

## Prompt Sent to LLM:
Please look at `pr_info/TASK_TRACKER.md` and pick the next task that should be done.
Please let me know on which task you are working on.
Please implement!
Please verify your implementation running the various checks of the MCP server and by solving potential issues (and repeat).
Please do not invent extra complexity not mentioned in the project plan.
Please let me know in case you encounter any issues or need a decision.
Please provide a short concise commit message stating the step name in the title. Do NOT perform a commit!

Once you are done, please check again that task description on `pr_info/TASK_TRACKER.md` to ensure that everything is done.
Once everything is done, please mark the task as done.
Please work only on one task. Do not pick further tasks.

Please also take a look at the tests\readme.md and only run those tests that are required in your context -i.e. avoid slow integration tests.

Current task from TASK_TRACKER.md: Add `env_vars` parameter to `ask_claude_code_cli()` in `src/mcp_coder/llm/providers/claude/claude_code_cli.py`

Please implement this task step by step.

## LLM Response:
Excellent! I've successfully completed Step 2. Let me provide a summary and the commit message:

## Step 2 Implementation Complete ✅

All CLAUDE.md requirements followed.

### Changes Made:
1. **Added `env_vars` parameter** to `ask_claude_code_cli()` in `src/mcp_coder/llm/providers/claude/claude_code_cli.py:167`
2. **Passed `env_vars` to CommandOptions** at line 216 with `env=env_vars`
3. **Updated docstring** to document the new parameter at line 180
4. **Added comprehensive tests** in `tests/llm/providers/claude/test_claude_code_cli.py`:
   - `test_ask_claude_code_cli_with_env_vars()` - verifies env_vars are passed correctly
   - `test_ask_claude_code_cli_without_env_vars()` - verifies backward compatibility

### Test Results:
- ✅ Pytest: 18 tests passed
- ✅ Pylint: No issues found
- ✅ Mypy: No type errors found

### Commit Message:
```
feat(llm): add env_vars parameter to CLI provider

Add env_vars parameter to ask_claude_code_cli() to support environment
variable propagation for MCP server subprocess execution.

Changes:
- Add env_vars: dict[str, str] | None parameter to ask_claude_code_cli()
- Pass env_vars to CommandOptions in subprocess execution
- Add tests for env_vars parameter and backward compatibility
- Update function docstring

Tests: All checks pass (pylint, pytest, mypy)
```

---
Generated on: 2025-10-06T08:17:30.881005