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

### Files to update (14 files)

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

**Utils __init__:**
19. `src/mcp_coder/utils/__init__.py` — Remove `from .github_operations import PullRequestManager` and its `__all__` entry

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
