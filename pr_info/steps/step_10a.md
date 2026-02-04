# Step 10a: Update Source File Imports

## LLM Prompt
```
Implement Step 10a of Issue #306 (see pr_info/steps/summary.md for context).
Update all SOURCE file imports to use the new issues/ package path.
Do NOT modify test files or delete old files yet.
Run verification checks after completion.
```

## WHERE

### Files to Modify (Source - 13 files, excluding parent __init__.py)

1. `src/mcp_coder/__init__.py`
2. `src/mcp_coder/workflow_utils/branch_status.py`
3. `src/mcp_coder/workflow_utils/base_branch.py`
4. `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`
5. `src/mcp_coder/workflows/vscodeclaude/issues.py`
6. `src/mcp_coder/workflows/vscodeclaude/status.py`
7. `src/mcp_coder/workflows/vscodeclaude/helpers.py`
8. `src/mcp_coder/workflows/create_plan.py`
9. `src/mcp_coder/workflows/create_pr/core.py`
10. `src/mcp_coder/workflows/implement/core.py`
11. `src/mcp_coder/cli/commands/set_status.py`
12. `src/mcp_coder/cli/commands/coordinator/commands.py`
13. `src/mcp_coder/cli/commands/coordinator/core.py`

**Note:** `github_operations/__init__.py` is handled in Step 10c (removing exports).

## WHAT

### Import Replacements

| Old Import | New Import |
|------------|------------|
| `from mcp_coder.utils.github_operations.issue_manager import X` | `from mcp_coder.utils.github_operations.issues import X` |
| `from mcp_coder.utils.github_operations.issue_branch_manager import X` | `from mcp_coder.utils.github_operations.issues import X` |
| `from mcp_coder.utils.github_operations.issue_cache import X` | `from mcp_coder.utils.github_operations.issues import X` |

## HOW

For each of the 13 source files:
1. Find imports from old paths (`issue_manager`, `issue_branch_manager`, `issue_cache`)
2. Replace with new `.issues` path
3. Keep imported names unchanged

## VERIFICATION

After updating all source files, run:
```bash
# MCP tools
mcp__code-checker__run_pylint_check
mcp__code-checker__run_mypy_check
mcp__code-checker__run_pytest_check  # Should pass - old files still exist
```

**Why checks should pass:** Both old and new paths work because old files still exist.

## DEPENDENCIES
- Steps 1-9 must be complete

## NOTES
- Do NOT touch test files yet (Step 10b)
- Do NOT delete old files yet (Step 10d)
- Do NOT modify parent `__init__.py` yet (Step 10c)
