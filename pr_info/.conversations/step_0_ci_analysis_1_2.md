# CI Failure Analysis

The CI pipeline failed due to a circular import error that prevents pytest from collecting 57 test modules. The error manifests as "ImportError: cannot import name 'get_prompt' from partially initialized module 'mcp_coder.prompt_manager' (most likely due to a circular import)".

The circular dependency chain is: `mcp_coder/__init__.py` imports from `prompt_manager.py`, which imports from `utils/data_files.py`, which triggers `utils/__init__.py` to import from `branch_status.py`. The `branch_status.py` module imports from `workflow_utils/task_tracker.py`, which triggers `workflow_utils/__init__.py` to import from `commit_operations.py`. Finally, `commit_operations.py` at line 14 imports `get_prompt` from `..prompt_manager`, completing the circular dependency back to the still-initializing `prompt_manager` module.

The files involved in this circular import are: `src/mcp_coder/__init__.py`, `src/mcp_coder/prompt_manager.py`, `src/mcp_coder/utils/__init__.py`, `src/mcp_coder/utils/branch_status.py`, `src/mcp_coder/workflow_utils/__init__.py`, and `src/mcp_coder/workflow_utils/commit_operations.py`.

To fix this issue, the circular dependency must be broken. The most straightforward approach is to move the `get_prompt` import in `commit_operations.py` from a top-level import to a local import inside the function that uses it (`generate_commit_message_with_llm`). This defers the import until runtime when all modules are fully initialized, breaking the circular dependency chain during module loading.