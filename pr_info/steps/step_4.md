# Step 4 — Update all consumer imports to use shim

> **Reference**: See `pr_info/steps/summary.md` for full context (Issue #833, part 5 of 5).

## Goal

Switch every import of `mcp_coder.utils.github_operations.*` (except `label_config`, already moved in Step 2) to `mcp_coder.mcp_workspace_github`. This is a pure import path change — no behavior changes.

## WHERE

All files in `src/` that import from `mcp_coder.utils.github_operations`. Each file's specific changes listed below.

## WHAT

### Import mapping

| Old import path | New import path |
|----------------|-----------------|
| `mcp_coder.utils.github_operations` | `mcp_coder.mcp_workspace_github` |
| `mcp_coder.utils.github_operations.issues` | `mcp_coder.mcp_workspace_github` |
| `mcp_coder.utils.github_operations.issues.cache` | `mcp_coder.mcp_workspace_github` |
| `mcp_coder.utils.github_operations.pr_manager` | `mcp_coder.mcp_workspace_github` |
| `mcp_coder.utils.github_operations.ci_results_manager` | `mcp_coder.mcp_workspace_github` |
| `mcp_coder.utils.github_operations.github_utils` | `mcp_coder.mcp_workspace_github` |
| `mcp_coder.utils.github_operations.labels_manager` | `mcp_coder.mcp_workspace_github` |

### Files to update (25 files)

**CLI commands:**
1. `src/mcp_coder/cli/commands/define_labels.py` — `IssueData`, `IssueEventType`, `IssueManager`, `LabelsManager`
2. `src/mcp_coder/cli/commands/set_status.py` — `IssueManager`
3. `src/mcp_coder/cli/commands/check_branch_status.py` — `CIResultsManager`, `CIStatusData`, `PullRequestManager`
4. `src/mcp_coder/cli/commands/coordinator/core.py` — `parse_github_url`, `IssueBranchManager`, `IssueData`, `IssueManager`, `get_all_cached_issues`
5. `src/mcp_coder/cli/commands/coordinator/issue_stats.py` — `IssueData`, `IssueManager`

**Workflows:**
6. `src/mcp_coder/workflows/create_plan/core.py` — `IssueData`, `IssueManager`
7. `src/mcp_coder/workflows/create_plan/prerequisites.py` — `IssueBranchManager`, `IssueData`, `IssueManager`
8. `src/mcp_coder/workflows/create_pr/core.py` — `IssueBranchManager`, `PullRequestData`, `PullRequestManager`, `IssueManager` (lazy import on line ~662)
9. `src/mcp_coder/workflows/implement/core.py` — `IssueManager`
10. `src/mcp_coder/workflows/implement/ci_operations.py` — `CIResultsManager`, `CIStatusData`

**VSCodeClaude:**
11. `src/mcp_coder/workflows/vscodeclaude/issues.py` — `RepoIdentifier`, `IssueBranchManager`, `IssueData`, `IssueManager`, `get_all_cached_issues`
12. `src/mcp_coder/workflows/vscodeclaude/cleanup.py` — `IssueData`, `IssueManager`, `get_all_cached_issues`
13. `src/mcp_coder/workflows/vscodeclaude/config.py` — `get_authenticated_username`
14. `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — `IssueBranchManager`, `IssueData`, `IssueManager`, `get_all_cached_issues`
15. `src/mcp_coder/workflows/vscodeclaude/session_restart.py` — `IssueBranchManager`, `IssueData`, `IssueManager`, `get_all_cached_issues`
16. `src/mcp_coder/workflows/vscodeclaude/status.py` — `IssueData`, `IssueManager`

**Checks:**
17. `src/mcp_coder/checks/branch_status.py` — `CIResultsManager`, `IssueData`, `IssueManager`

**Workflow utils:**
18. `src/mcp_coder/workflow_utils/failure_handling.py` — `IssueManager`

**Package init:**
19. `src/mcp_coder/__init__.py` — imports `CommentData`, `IssueData`, `IssueManager` from `.utils.github_operations.issues` and `LabelData` from `.utils.github_operations.labels_manager`. Change to import from `.mcp_workspace_github`

**Utils __init__:**
20. `src/mcp_coder/utils/__init__.py` — Remove `from .github_operations import PullRequestManager` and its `__all__` entry

**Additional CLI commands:**
21. `src/mcp_coder/cli/commands/gh_tool.py` — imports `IssueBranchManager`, `IssueManager` from `...utils.github_operations.issues.*`
22. `src/mcp_coder/cli/commands/coordinator/commands.py` — imports `RepoIdentifier`, `IssueBranchManager`, `IssueData`, `IssueManager`, `get_all_cached_issues`, `update_issue_labels_in_cache` from `....utils.github_operations`

**Additional workflows:**
23. `src/mcp_coder/workflows/vscodeclaude/helpers.py` — imports `IssueData` from `...utils.github_operations.issues`

**Additional workflow utils:**
24. `src/mcp_coder/workflow_utils/base_branch.py` — imports `IssueData`, `IssueManager`, `PullRequestManager` from `mcp_coder.utils.github_operations.*`

**Additional checks:**
25. `src/mcp_coder/checks/ci_log_parser.py` — imports `CIResultsManager` in TYPE_CHECKING block

### Test files to update (~30 files)

Test files that import from `mcp_coder.utils.github_operations` must also be updated to import from `mcp_coder.mcp_workspace_github`. After making source changes, grep `tests/` for remaining `github_operations` imports (excluding `tests/utils/github_operations/` which is deleted in Step 6).

Key test directories with affected files:
- `tests/checks/` — `test_branch_status.py`
- `tests/cli/commands/` — `test_define_labels*.py`, `test_set_status*.py`, `test_gh_tool*.py`
- `tests/cli/commands/coordinator/` — `test_commands.py`, `test_core.py`, `test_integration.py`, `test_issue_stats.py`
- `tests/integration/` — `test_execution_dir_integration.py`
- `tests/workflows/create_plan/` — `test_main.py`, `test_prerequisites.py`, `test_prompt_execution.py`
- `tests/workflows/implement/` — `test_ci_check.py`
- `tests/workflows/vscodeclaude/` — `test_cache_aware.py`, `test_cleanup.py`, `test_helpers.py`, `test_issues.py`, `test_session_launch*.py`, `test_session_restart*.py`, `test_status_display.py`, etc.
- `tests/workflow_utils/` — `test_base_branch.py`

**Important**: Mock targets in tests must also be updated. For example, `@patch("mcp_coder.utils.github_operations.issues.IssueManager")` → `@patch("mcp_coder.mcp_workspace_github.IssueManager")`. However, some mocks should target the **consumer module's import** instead, depending on test patterns.

Use `grep -r "github_operations" tests/ --include="*.py"` to find all affected files. Exclude `tests/utils/github_operations/` from the update (those are deleted in Step 6).

## HOW

For each file:
1. Replace the old `from ...utils.github_operations...` import line(s)
2. Add equivalent `from ...mcp_workspace_github import ...` (or `from mcp_coder.mcp_workspace_github import ...`)
3. Use relative imports where the file already uses relative imports for sibling modules, absolute otherwise

**Important**: Use the grep-verified list above. After making changes, grep for any remaining `github_operations` imports in `src/` to catch anything missed.

## ALGORITHM

No algorithm — pure import path substitution.

## DATA

No data structure changes.

## Commit

```
refactor: switch github_operations imports to shim
```

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement step 4 from pr_info/steps/step_4.md.

Update all imports from mcp_coder.utils.github_operations to mcp_coder.mcp_workspace_github.
Do NOT change any behavior — only import paths.
After changes, grep src/ for any remaining "github_operations" imports (excluding the local
files themselves which will be deleted in step 6).
Run all checks (pylint, mypy, pytest unit tests) after implementation.
```
