# Step 3: Verify and Fix Remaining Tests Across All Suites

> **Context**: Read `pr_info/steps/summary.md` for architectural overview of issue #264.
> **Prerequisite**: Steps 1 and 2 must be complete.

## Goal

Run the full test suite and fix any remaining test failures caused by the changes in steps 1 and 2. This step catches any mocks, imports, or assertions that were missed.

## Approach

Run all tests, identify failures, fix them. This is a verification/cleanup step, not a feature step.

---

## Part A: Run full unit test suite

### HOW
Run pytest excluding integration tests:
```
pytest -n auto -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"
```

### Expected failure categories

1. **Import errors**: Any file still importing `get_linked_branch_for_issue` from `vscodeclaude`
2. **Mock path errors**: Tests mocking the old function path instead of `get_branch_with_pr_fallback`
3. **ValueError assertions**: Tests asserting `ValueError` is raised (should now expect `None`)
4. **Missing parameters**: Tests calling `_prepare_restart_branch` without new `repo_owner`/`repo_name` params

---

## Part B: Fix test files as needed

### Files most likely to need fixes

| File | Likely issue |
|------|--------------|
| `tests/workflows/vscodeclaude/test_issues.py` | `get_linked_branch_for_issue` tests to remove/update |
| `tests/workflows/vscodeclaude/test_orchestrator_launch.py` | Mock paths for branch resolution |
| `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` | Mock paths for branch resolution, `_prepare_restart_branch` params |
| `tests/cli/commands/coordinator/test_commands.py` | Mock paths for intervention mode |
| `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` | May mock `get_linked_branch_for_issue` |

### WHAT to fix in each case

**Import errors**: Replace `get_linked_branch_for_issue` imports with direct mock of `IssueBranchManager.get_branch_with_pr_fallback`

**Mock path changes**:
```python
# Old mock path:
@patch("mcp_coder.workflows.vscodeclaude.session_launch.get_linked_branch_for_issue")
# or
@patch("mcp_coder.workflows.vscodeclaude.issues.get_linked_branch_for_issue")

# New mock path:
@patch.object(IssueBranchManager, "get_branch_with_pr_fallback")
# or
@patch("mcp_coder.utils.github_operations.issues.branch_manager.IssueBranchManager.get_branch_with_pr_fallback")
```

**ValueError assertions**:
```python
# Old:
mock_get_branch.side_effect = ValueError("multiple branches")

# New:
mock_get_branch.return_value = None  # ambiguous/missing = None
```

**Parameter updates**:
```python
# Old:
_prepare_restart_branch(folder_path, status, branch_manager, issue_number)

# New:
_prepare_restart_branch(folder_path, status, branch_manager, issue_number, repo_owner, repo_name)
```

---

## Part C: Run tests again, verify all pass

Run the same pytest command. All tests should pass. If any remain broken, fix iteratively.

---

## Part D: Run code quality checks

### Pylint
Verify no new lint issues from the changes (unused imports, etc.)

### Mypy
Verify type annotations are consistent (especially `Optional[str]` return types and removed `ValueError` in docstrings)

---

## LLM Prompt for Step 3

```
You are implementing Step 3 of issue #264 for the mcp-coder project.
Read pr_info/steps/summary.md for full context, then read this step file (pr_info/steps/step_3.md).
Steps 1 and 2 are already complete.

Your task: Run the full test suite and fix any remaining failures.

1. Run pytest (excluding integration tests) and review all failures
2. Fix each failure — most will be stale mocks or imports of the removed
   get_linked_branch_for_issue function
3. Re-run tests until all pass
4. Run pylint and mypy checks, fix any issues

Key constraints:
- Do NOT change production logic — only fix tests and type issues
- Mock the correct path: IssueBranchManager.get_branch_with_pr_fallback
- Replace ValueError side_effects with return_value=None
- Update _prepare_restart_branch test calls with repo_full_name param
```
