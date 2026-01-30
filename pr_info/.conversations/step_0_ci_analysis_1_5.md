# CI Failure Analysis

The CI unit-tests job failed with 10 test failures across two distinct issues:

**Issue 1: Tests patching non-existent `prompt_llm` attribute (4 failures)**

The `TestSessionIdOutputFormat` test class in `tests/cli/commands/test_prompt.py` has 4 tests that fail with `AttributeError: <module 'mcp_coder.cli.commands.prompt' ...> does not have the attribute 'prompt_llm'`. These tests use `@patch("mcp_coder.cli.commands.prompt.prompt_llm")` but the `prompt_llm` function is imported inside the `execute_prompt` function body (within an `if output_format == "session-id":` block) rather than at the module level. When patching attempts to access `mcp_coder.cli.commands.prompt.prompt_llm`, it fails because the function is imported from `...llm.interface` only at runtime inside the function.

To fix this, the tests should either patch the function at its source (`mcp_coder.llm.interface.prompt_llm`) or the import should be moved to the module level in `src/mcp_coder/cli/commands/prompt.py` so the patch target exists at the module level.

**Issue 2: Linux V2 templates not implemented (6 failures)**

The `TestRegenerateSessionFiles` test class in `tests/utils/vscodeclaude/test_orchestrator_regenerate.py` has 6 tests that fail with `NotImplementedError: Linux V2 templates not yet implemented. See Step 17 for Linux support.` The tests run on Linux CI runners but call `regenerate_session_files()` which internally calls `create_startup_script()` in `src/mcp_coder/utils/vscodeclaude/workspace.py:457`. This function explicitly raises `NotImplementedError` for non-Windows platforms.

To fix this, either: (1) implement Linux V2 templates as planned in Step 17, (2) skip these tests on Linux using `@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-only test")`, or (3) mock the `platform.system()` call in the tests to simulate Windows behavior.