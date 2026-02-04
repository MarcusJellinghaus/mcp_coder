# Step 10b: Update Test File Imports

## LLM Prompt
```
Implement Step 10b of Issue #306 (see pr_info/steps/summary.md for context).
Update all TEST file imports to use the new issues/ package path.
Run verification checks after completion.
```

## WHERE

### Files to Modify (Tests - 9 files)

1. `tests/utils/github_operations/test_issue_manager.py`
2. `tests/utils/github_operations/test_issue_manager_integration.py`
3. `tests/utils/github_operations/test_issue_manager_label_update.py`
4. `tests/utils/github_operations/test_issue_branch_manager.py`
5. `tests/utils/github_operations/test_issue_branch_manager_integration.py`
6. `tests/utils/github_operations/test_issue_cache.py`
7. `tests/utils/github_operations/conftest.py`
8. `tests/utils/github_operations/test_github_utils.py`
9. `tests/workflows/test_issue_stats.py`

## WHAT

### Import Replacements

| Old Import | New Import |
|------------|------------|
| `from mcp_coder.utils.github_operations.issue_manager import X` | `from mcp_coder.utils.github_operations.issues import X` |
| `from mcp_coder.utils.github_operations.issue_branch_manager import X` | `from mcp_coder.utils.github_operations.issues import X` |
| `from mcp_coder.utils.github_operations.issue_cache import X` | `from mcp_coder.utils.github_operations.issues import X` |

### Special Case: `_parse_base_branch`

Per Decision #3, this internal function should be imported from the submodule:
```python
# Old
from mcp_coder.utils.github_operations.issue_manager import _parse_base_branch

# New
from mcp_coder.utils.github_operations.issues.manager import _parse_base_branch
```

## HOW

For each of the 9 test files:
1. Find imports from old paths (`issue_manager`, `issue_branch_manager`, `issue_cache`)
2. Replace with new `.issues` path (or `.issues.manager` for `_parse_base_branch`)
3. Keep imported names unchanged

## VERIFICATION

After updating all test files, run:
```bash
# MCP tools
mcp__code-checker__run_pylint_check
mcp__code-checker__run_mypy_check
mcp__code-checker__run_pytest_check  # Should pass - old files still exist
```

**Why checks should pass:** Both old and new paths work because old files still exist.

## DEPENDENCIES
- Step 10a must be complete

## NOTES
- Do NOT delete old files yet (Step 10d)
- Do NOT modify parent `__init__.py` yet (Step 10c)
