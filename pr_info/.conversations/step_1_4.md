# Implementation Task: Add `env_vars` parameter to `ask_llm()` and `prompt_llm()` in `src/mcp_coder/llm/interface.py`

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

Current task from TASK_TRACKER.md: Add `env_vars` parameter to `ask_llm()` and `prompt_llm()` in `src/mcp_coder/llm/interface.py`

Please implement this task step by step.

## LLM Response:
Perfect! Now let me provide the commit message as requested:

## Summary

**Task completed successfully!** ✅

I've implemented Step 4 from the TASK_TRACKER.md:

### Changes Made:

1. **Added `env_vars` parameter to `ask_llm()` in `src/mcp_coder/llm/interface.py`**
   - Updated function signature
   - Updated docstring
   - Threaded parameter to `ask_claude_code()`

2. **Added `env_vars` parameter to `prompt_llm()` in `src/mcp_coder/llm/interface.py`**
   - Updated function signature
   - Updated docstring
   - Threaded parameter to `ask_claude_code_cli()` and `ask_claude_code_api()`

3. **Added `env_vars` parameter to `ask_claude_code()` in `src/mcp_coder/llm/providers/claude/claude_code_interface.py`**
   - Updated function signature
   - Updated docstring
   - Threaded parameter to both CLI and API providers

4. **Updated tests in `tests/llm/test_interface.py`**
   - Added 3 new tests for env_vars functionality
   - Updated all existing test assertions to include `env_vars=None`

5. **Updated tests in `tests/llm/providers/claude/test_claude_code_interface.py`**
   - Added 1 new test for env_vars functionality
   - Updated all existing test assertions to include `env_vars=None`

### Code Quality Checks:
- ✅ **Pylint**: No issues found
- ✅ **Mypy**: No type errors found
- ✅ **Pytest**: All 49 tests passed

All CLAUDE.md requirements followed.

### Commit Message:

```
feat(llm): add env_vars parameter to interface layer functions

Add optional env_vars parameter to ask_llm(), prompt_llm(), and
ask_claude_code() functions to enable environment variable passing
through the interface layer to underlying providers.

Changes:
- Add env_vars parameter to ask_llm() and prompt_llm() in interface.py
- Add env_vars parameter to ask_claude_code() in claude_code_interface.py
- Thread env_vars through all function calls maintaining backward compatibility
- Add comprehensive test coverage for new functionality
- Update all existing tests to verify env_vars=None default behavior

All tests passing (49/49). Code quality checks: pylint ✓, mypy ✓, pytest ✓
```

---
Generated on: 2025-10-06T08:35:41.896009