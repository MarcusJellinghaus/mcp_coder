# Implementation Task: Implement `src/mcp_coder/llm/env.py` with `prepare_llm_environment()` function

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

Current task from TASK_TRACKER.md: Implement `src/mcp_coder/llm/env.py` with `prepare_llm_environment()` function

Please implement this task step by step.

## LLM Response:
Perfect! Now let me provide the commit message as requested:

## Summary

**Step 1 Implementation Complete** ✅

### What was implemented:

1. **Created `src/mcp_coder/llm/env.py`** with `prepare_llm_environment()` function:
   - Integrates with existing `detect_python_environment()` from utils/detection.py
   - Returns dict with `MCP_CODER_PROJECT_DIR` and `MCP_CODER_VENV_DIR`
   - Raises `RuntimeError` if no virtual environment found (strict requirement)
   - Uses OS-native absolute path format via `Path.resolve()`
   - Includes debug logging

2. **Created `tests/llm/test_env.py`** with 5 test cases:
   - `test_prepare_llm_environment_success()` - Valid venv found
   - `test_prepare_llm_environment_no_venv()` - No venv, raises RuntimeError
   - `test_prepare_llm_environment_paths_absolute()` - Verifies absolute paths
   - `test_prepare_llm_environment_paths_os_native()` - Verifies OS-native format
   - `test_prepare_llm_environment_logging()` - Verifies debug logging

3. **All quality checks passed**:
   - ✅ Pylint: No issues
   - ✅ Pytest: 5/5 tests passed
   - ✅ Mypy: No type errors

### Commit Message:

```
Implement environment variable preparation module

Add prepare_llm_environment() function to create MCP_CODER_* environment
variables for portable .mcp.json configuration files.
```

**All CLAUDE.md requirements followed** ✅

---
Generated on: 2025-10-06T08:08:09.068476