# Implementation Task: Add integration test `test_env_vars_propagation()` in `tests/llm/providers/claude/test_claude_integration.py`

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

Current task from TASK_TRACKER.md: Add integration test `test_env_vars_propagation()` in `tests/llm/providers/claude/test_claude_integration.py`

Please implement this task step by step.

## LLM Response:
I need permission to write to the test file. Once granted, I'll add the integration test for environment variable propagation.

The test will:
1. Call `ask_llm()` with the CLI method, which internally calls `prepare_llm_environment()` to set up `MCP_CODER_PROJECT_DIR` and `MCP_CODER_VENV_DIR` environment variables
2. Call `ask_llm()` with the API method to test the same for the API path
3. Verify both calls succeed, which proves the environment variables were properly propagated to the Claude Code subprocess/SDK

This integration test complements the unit tests already added in Steps 1-6 that verify the env_vars parameter threading with mocks.

---
Generated on: 2025-10-06T09:32:19.042255