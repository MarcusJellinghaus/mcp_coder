# Step 1 — Create shim `mcp_workspace_github.py` + smoke tests

> **Reference**: See `pr_info/steps/summary.md` for full context (Issue #833, part 5 of 5).

## Goal

Create the thin shim module that re-exports all GitHub operations symbols from `mcp_workspace.github_operations`. Add smoke tests following the existing `mcp_workspace_git.py` pattern.

## Prerequisite check

Before creating the shim, verify `mcp_workspace.github_operations` is installed:
```python
import mcp_workspace.github_operations
```
If not available, update the mcp_workspace dependency first.

## WHERE

- `src/mcp_coder/mcp_workspace_github.py` (new)
- `tests/test_mcp_workspace_github_smoke.py` (new)

## WHAT

### Shim module: `mcp_workspace_github.py`

Pure re-exports from `mcp_workspace.github_operations`. No logic, no factories.

**Symbols to re-export** (verify against actual `mcp_workspace.github_operations` exports):
- Classes: `BaseGitHubManager`, `PullRequestManager`, `LabelsManager`, `CIResultsManager`, `IssueManager`, `IssueBranchManager`
- Dataclass: `RepoIdentifier`
- Functions: `get_authenticated_username`, `parse_github_url`, `get_repo_full_name`, `format_github_https_url`, `generate_branch_name_from_issue`
- TypedDicts: `LabelData`, `PullRequestData`, `CIStatusData`, `IssueData`, `CommentData`, `EventData`, `BranchCreationResult`, `StepData`, `JobData`, `RunData`, `CacheData`
- Enums: `IssueEventType`
- Functions: `create_empty_issue_data`, `get_all_cached_issues`, `update_issue_labels_in_cache`, `filter_runs_by_head_sha`, `aggregate_conclusion`, `parse_base_branch`
- Cache internals (used by tests): `_get_cache_file_path`, `_load_cache_file`, `_save_cache_file`, `_log_stale_cache_entries`

**Important**: Check the actual `mcp_workspace.github_operations` package to confirm which symbols are available. The shim should only export what mcp_workspace provides. Adapt the list above based on what's actually importable.

### Smoke tests: `test_mcp_workspace_github_smoke.py`

Follow the pattern of `tests/test_mcp_workspace_git_smoke.py`:
- `test_shim_importable()` — module imports without error
- `test_key_symbols_accessible()` — key classes/functions importable and not None
- `test_all_exports_defined()` — `__all__` has expected count

## HOW

```python
# Pattern from mcp_workspace_git.py:
from mcp_workspace.github_operations import SomeClass
from mcp_workspace.github_operations.submodule import AnotherClass

__all__ = ["SomeClass", "AnotherClass", ...]
```

## ALGORITHM

No algorithm — pure re-exports.

## DATA

No new data structures — re-exports existing ones.

## Commit

```
feat: add mcp_workspace_github shim with smoke tests
```

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement step 1 from pr_info/steps/step_1.md.

First verify mcp_workspace.github_operations is installed by checking its __init__.py exports.
Then create the shim and smoke tests. Follow the existing mcp_workspace_git.py pattern exactly.
Run all checks (pylint, mypy, pytest unit tests) after implementation.
```
