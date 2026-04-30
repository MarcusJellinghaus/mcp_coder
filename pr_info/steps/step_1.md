# Step 1 — Data layer: `mcp_coder/services/branch_info.py`

## LLM Prompt

> Implement Step 1 of the iCoder branch-info-bar feature (issue #844).
> Read `pr_info/steps/summary.md` for the architectural context.
> This step creates the new `mcp_coder/services/` top-level package with a pure
> data-layer module that returns a `BranchInfo` dataclass. It also wires the
> new package into `tach.toml` and `.importlinter`. **TDD**: write the tests
> first, then the implementation. End the step with one commit; all three
> checks (pylint, pytest, mypy) must pass.

## WHERE

```
src/mcp_coder/services/__init__.py            (new, empty package marker)
src/mcp_coder/services/py.typed                (new, empty marker)
src/mcp_coder/services/branch_info.py          (new)
tests/services/__init__.py                     (new, empty)
tests/services/test_branch_info.py             (new)
tach.toml                                      (modify)
.importlinter                                  (modify)
```

## WHAT

```python
# src/mcp_coder/services/branch_info.py
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass(frozen=True)
class BranchInfo:
    is_git_repo: bool
    branch_name: str | None              # None if not a git repo
    is_dirty: bool                       # False when not a git repo
    issue_number: int | None             # None if branch has no issue suffix
    issue_title: str | None              # None if not in cache or fetch failed
    issue_status_label: str | None       # e.g. "status-04:plan-review"; None if unknown
    cache_last_checked: datetime | None  # from cache file; None when cache miss

def get_branch_info(project_dir: Path) -> BranchInfo: ...
def get_pr_for_branch(project_dir: Path, issue_number: int) -> int | None: ...
```

## HOW

- `get_branch_info` calls (via `mcp_coder.mcp_workspace_git`):
  `is_git_repository`, `get_current_branch_name`, `extract_issue_number_from_branch`.
- For dirty check, run `git status --porcelain` via
  `mcp_coder.utils.subprocess_runner.execute_subprocess` with `cwd=project_dir`
  (matches pattern in `workflows/vscodeclaude/status.py:get_folder_git_status`).
- For issue lookup, call `get_all_cached_issues(RepoIdentifier, issue_manager=...)`
  from `mcp_coder.mcp_workspace_github`. Wrap in try/except — on any error, leave
  `issue_*` fields as `None`. Hard failures must NOT raise from this function.
- Cache `last_checked` is read from the cache JSON file at
  `~/.mcp_coder/coordinator_cache/{owner-repo}.issues.json`. Use the existing
  `_get_cache_file_path` and `_load_cache_file` helpers re-exported from
  `mcp_coder.mcp_workspace_github`.
- `get_pr_for_branch` constructs `IssueBranchManager(repo_url=...)` and calls
  `get_branch_with_pr_fallback(...)`. Returns the PR number parsed out of the
  resolved branch metadata, or `None`. Lets exceptions propagate (caller
  decides what to do).
- Tach: add `[[modules]]` entry for `mcp_coder.services` at the application
  layer (alongside `mcp_coder.checks`). Add it to the `depends_on` list of
  `mcp_coder.icoder` and `mcp_coder.cli`.
- import-linter: add `mcp_coder.services` to the `layered_architecture` `layers`
  block at the same line as `mcp_coder.checks` (separated by `|`).

## ALGORITHM

```
get_branch_info(project_dir):
    if not is_git_repository(project_dir):
        return BranchInfo(is_git_repo=False, branch_name=None, ...all None)
    branch = get_current_branch_name(project_dir)
    is_dirty = run("git status --porcelain", cwd=project_dir).stdout.strip() != ""
    issue_number = extract_issue_number_from_branch(branch)
    title, label, last_checked = None, None, None
    if issue_number:
        try:
            cache_file = _get_cache_file_path(repo_id)
            data = _load_cache_file(cache_file)
            last_checked = parse_iso(data["last_checked"])
            issue = get_all_cached_issues(repo_id, issue_manager).get(issue_number)
            title = issue["title"]; label = first label starting with "status-"
        except Exception: pass
    return BranchInfo(True, branch, is_dirty, issue_number, title, label, last_checked)
```

## DATA

- `BranchInfo` (frozen dataclass) — see `WHAT` above.
- `get_pr_for_branch` returns `int | None` — the PR number when a linked PR is
  found, else `None`.

## Tests (TDD — write first)

In `tests/services/test_branch_info.py`:

1. `test_no_git_repo_returns_empty_branchinfo` — patch `is_git_repository` to
   return False; assert all fields None except `is_git_repo=False`,
   `is_dirty=False`.
2. `test_branch_without_issue_number` — patch git calls to return branch
   `"main"`; assert `issue_number is None`, no GH calls attempted.
3. `test_branch_with_issue_populates_from_cache` — patch git +
   `get_all_cached_issues` to return a dict with the issue; patch
   `_load_cache_file` to return `{"last_checked": "2026-04-30T10:00:00+00:00",
   "issues": {...}}`; assert `issue_title`, `issue_status_label`, and
   `cache_last_checked` populated.
4. `test_gh_failure_keeps_branch_fields_returns_none_for_issue` — patch
   `get_all_cached_issues` to raise; assert branch+dirty still set, issue
   fields all None, no exception raised.
5. `test_dirty_detection_uses_porcelain_output` — patch
   `execute_subprocess` to return `" M file.py\n"`; assert `is_dirty=True`.
6. `test_get_pr_for_branch_returns_pr_number` — patch
   `IssueBranchManager.get_branch_with_pr_fallback` to return a branch name
   matching e.g. `pr-123-...`; assert `123` returned. (If the helper instead
   returns PR-number directly, test for that.)

Run: `mcp__tools-py__run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration and not llm_integration and not textual_integration"])`.
Then pylint + mypy. Single commit when all green.
