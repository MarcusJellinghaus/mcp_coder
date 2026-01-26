# CI Fix Attempt 2

I've fixed the circular import issue. Here's a summary of the changes:

## Summary

**Problem:** The CI pipeline was failing due to a circular import. The chain was:
- `mcp_coder.utils.__init__` imports `branch_status`
- `branch_status` imports `has_incomplete_work` from `mcp_coder.workflow_utils.task_tracker`
- Python loads `workflow_utils.__init__.py` first, which eagerly imports from `commit_operations`
- `commit_operations` imports from `llm.interface`
- But `llm.interface` was already being loaded through another path, causing a partially initialized module error

**Solution:** Modified `src/mcp_coder/workflow_utils/__init__.py` to use lazy imports for `commit_operations` functions via Python's `__getattr__` module-level function. This defers the import of `commit_operations` (and its LLM dependencies) until those functions are actually accessed at runtime, rather than at module initialization time.

**Changes made:**
- `src/mcp_coder/workflow_utils/__init__.py`:
  - Removed eager imports of `commit_operations` functions
  - Added `TYPE_CHECKING` block for static analysis
  - Added `__getattr__` function for lazy loading of `generate_commit_message_with_llm`, `parse_llm_commit_response`, and `strip_claude_footers`
  - Added `has_incomplete_work` to the exports (it was being imported by `branch_status` but not explicitly exported)

**Quality checks:**
- ✅ Pylint passes (pre-existing issues in `branch_status.py` unrelated to this change)
- ✅ All 1720 tests pass
- ✅ Mypy passes for the modified file (pre-existing issues in `branch_status.py` unrelated to this change)