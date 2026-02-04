# Step 10d: Delete Old Files and Final Verification

## LLM Prompt
```
Implement Step 10d of Issue #306 (see pr_info/steps/summary.md for context).
Delete the old issue_manager.py, issue_branch_manager.py, and issue_cache.py files.
Run all verification checks to confirm the refactoring is complete.
```

## WHERE

### Files to Delete (3 files)

1. `src/mcp_coder/utils/github_operations/issue_manager.py`
2. `src/mcp_coder/utils/github_operations/issue_branch_manager.py`
3. `src/mcp_coder/utils/github_operations/issue_cache.py`

## HOW

```bash
# Delete old files
rm src/mcp_coder/utils/github_operations/issue_manager.py
rm src/mcp_coder/utils/github_operations/issue_branch_manager.py
rm src/mcp_coder/utils/github_operations/issue_cache.py
```

Or use git:
```bash
git rm src/mcp_coder/utils/github_operations/issue_manager.py
git rm src/mcp_coder/utils/github_operations/issue_branch_manager.py
git rm src/mcp_coder/utils/github_operations/issue_cache.py
```

## VERIFICATION

Run ALL checks to confirm the refactoring is complete:

```bash
# 1. Import structure
./tools/lint_imports.bat  # or .sh

# 2. Module boundaries
./tools/tach_check.bat  # or .sh

# 3. MCP tools (REQUIRED)
mcp__code-checker__run_pylint_check
mcp__code-checker__run_mypy_check
mcp__code-checker__run_pytest_check
```

## DEPENDENCIES
- Steps 10a, 10b, and 10c must be complete

## ACCEPTANCE CRITERIA (from Issue)

After this step, verify:
- [ ] All files under 500 lines (branch_manager.py at 506 is acceptable)
- [ ] All imports updated (no legacy paths)
- [ ] No re-exports from parent `__init__.py` for issue-related code
- [ ] `lint-imports` passes
- [ ] `tach check` passes
- [ ] All tests pass
- [ ] No functional changes (move only)

## NOTES
- This is the FINAL step of the refactoring
- After deletion, the old files cannot be recovered except from git history
- If any check fails, DO NOT proceed - investigate and fix first
