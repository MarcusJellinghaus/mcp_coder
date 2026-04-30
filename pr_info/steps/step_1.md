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
src/mcp_coder/mcp_workspace_github.py          (modify — Boy Scout: rename
                                                all four cache-helper
                                                public re-exports:
                                                `_get_cache_file_path` →
                                                `get_cache_file_path`,
                                                `_load_cache_file` →
                                                `load_cache_file`,
                                                `_save_cache_file` →
                                                `save_cache_file`,
                                                `_log_stale_cache_entries`
                                                → `log_stale_cache_entries`
                                                in the shim's import block
                                                and `__all__`. Upstream
                                                private names in
                                                `mcp_coder_utils` stay
                                                unchanged — only the shim
                                                exposes the public alias.
                                                Boy Scout rename covers
                                                all four cache shim
                                                re-exports for consistency.)
tests/cli/commands/coordinator/test_core.py   (modify — existing call
                                                sites for all four
                                                helpers: imports + usages
                                                + module docstring +
                                                test class docstrings +
                                                test method names that
                                                embed the helper name.
                                                Concretely (verified via
                                                `mcp__workspace__search_files`):
                                                module docstring lines
                                                referencing the helpers
                                                (~lines 8–9), the import
                                                block (~lines 42–45),
                                                `_get_cache_file_path`
                                                usages (~lines 707, 709,
                                                714, 721, 742),
                                                `_load_cache_file` usages
                                                (~lines 749, 753, 761,
                                                786, 791, 797),
                                                `_save_cache_file` usages
                                                (~lines 804, 828), and
                                                `_log_stale_cache_entries`
                                                usages (~lines 838, 840,
                                                879, 883, 922). All occur
                                                in this single file —
                                                this is the only caller
                                                in the codebase besides
                                                the new
                                                `services/branch_info.py`.
                                                Listed for visibility;
                                                the rename itself is
                                                performed in the
                                                implementation step.)
```

> **Boy Scout fix**: existing underscore prefix violated the public-API
> convention (callers outside the defining module shouldn't reach for
> `_`-prefixed names). The rename also touches existing call sites in
> `tests/cli/commands/coordinator/test_core.py` — listed above for
> visibility, but the rename itself is performed in the implementation
> step (this plan only documents the scope).

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
def get_pr_for_issue(project_dir: Path, issue_number: int) -> int | None: ...
```

Renamed from `get_pr_for_branch` to `get_pr_for_issue` because the lookup is
keyed by issue number (which has a linked branch + linked PR), not by branch
name directly.

## HOW

- `get_branch_info` calls (via `mcp_coder.mcp_workspace_git`):
  `is_git_repository`, `get_current_branch_name`, `extract_issue_number_from_branch`.
- For dirty check, call `is_working_directory_clean(project_dir)` (re-exported
  from `mcp_coder.mcp_workspace_git`) and negate the result. **Do not** shell
  out via `execute_subprocess("git status --porcelain")` — the shim already
  handles this. If at some point the plan needs the list of changed files,
  use `get_full_status(project_dir)` instead (also re-exported).
- For repo identity, call `get_repository_identifier(project_dir)` (re-exported
  from `mcp_coder.mcp_workspace_git`). It returns `Optional[RepoIdentifier]`
  with attributes `owner`, `repo_name`, `https_url`. **Do not** parse
  `.git/config` manually. If `repo_id is None` (no remote), skip GH lookups
  and return `BranchInfo` with `issue_*` and `cache_last_checked` set to
  `None` (still populate `branch_name` + `is_dirty`).
- For issue lookup, call `get_all_cached_issues(repo_id, issue_manager=...)`
  from `mcp_coder.mcp_workspace_github`. Wrap in try/except — on any error,
  leave `issue_*` fields as `None`. Hard failures must NOT raise from this
  function.
- Cache `last_checked` is read from the cache JSON file. Use the existing
  `get_cache_file_path(repo_id)` helper re-exported from
  `mcp_coder.mcp_workspace_github` (Boy Scout fix: renamed from
  `_get_cache_file_path` — see WHERE block) to obtain the path; do **not**
  hardcode `~/.mcp_coder/coordinator_cache/{owner-repo}.issues.json` in
  the data layer. Read the JSON via `load_cache_file` (also re-exported,
  renamed from `_load_cache_file`) or stdlib
  `json.loads(path.read_text(...))` — pick whichever the helper actually
  exposes.
- `get_pr_for_issue` is a **two-step lookup**:
  1. **Branch lookup**: `IssueBranchManager(project_dir=project_dir,
     repo_url=repo_id.https_url).get_branch_with_pr_fallback(issue_number,
     repo_id.owner, repo_id.repo_name)` — returns `Optional[str]`, the
     **linked branch name** (NOT a PR number).
  2. **PR lookup**: if the branch name is non-None, call
     `PullRequestManager(project_dir).find_pull_request_by_head(branch_name)`
     which returns `list[PullRequestData]`. Read `.number` (or
     `["number"]` depending on TypedDict shape) from the first item; if the
     list is empty, return `None`.
  Both `IssueBranchManager` and `PullRequestManager` are re-exported from
  `src/mcp_coder/mcp_workspace_github.py`. Lets exceptions from either
  step propagate to the caller (the adapter wraps them).
- Tach: add `[[modules]]` entry for `mcp_coder.services` at the application
  layer (alongside `mcp_coder.checks`). Add it to the `depends_on` list of
  `mcp_coder.icoder` and `mcp_coder.cli`. See "Tach + import-linter wiring"
  below for the full deterministic depends_on list.
- import-linter: add `mcp_coder.services` to the `layered_architecture` `layers`
  block at the same line as `mcp_coder.checks` (separated by `|`).

### Tach + import-linter wiring (deterministic)

After applying the helper changes above, the new `mcp_coder.services` module
imports from exactly these internal modules:

- `mcp_coder.mcp_workspace_git` — `is_git_repository`,
  `get_current_branch_name`, `extract_issue_number_from_branch`,
  `is_working_directory_clean`, `get_repository_identifier`,
  `RepoIdentifier`.
- `mcp_coder.mcp_workspace_github` — `get_all_cached_issues`,
  `get_cache_file_path`, `load_cache_file` (both renamed from underscore
  variants per the Boy Scout fix; the same rename is also applied to the
  two companion helpers `save_cache_file` and `log_stale_cache_entries`
  for consistency, though `services/branch_info.py` does not call them),
  `IssueBranchManager`, `PullRequestManager`, `PullRequestData`.
- `mcp_coder.config` — only if needed for label name → color resolution; the
  data layer itself does NOT need it (label colors are resolved in the
  widget). **Likely omit.** Re-verify during implementation.

The data layer does **not** need `mcp_coder.utils` (no direct subprocess
calls — dirty detection goes through the git shim).

Tach `[[modules]]` block to add (place at application layer, after
`mcp_coder.checks`):

```toml
[[modules]]
path = "mcp_coder.services"
layer = "application"
# Application-layer read-only data services for cross-cutting state
# (branch info, etc.). Consumers: icoder (now), vscodeclaude/web (later).
depends_on = [
    { path = "mcp_coder.mcp_workspace_git" },
    { path = "mcp_coder.mcp_workspace_github" },
    { path = "mcp_coder.constants" },     # optional; include only if used
]
```

Then update `mcp_coder.icoder.depends_on` to add `{ path = "mcp_coder.services" }`,
and update `mcp_coder.cli.depends_on` likewise (CLI imports `icoder` and may
later import `services` for a future `/branchinfo` command).

import-linter `layered_architecture` change — keep `mcp_coder.services` at
the same layer as `mcp_coder.checks`:

```ini
layers =
    mcp_coder.cli | mcp_coder.icoder
    mcp_coder.workflows
    mcp_coder.services | mcp_coder.checks
    mcp_coder.workflow_utils
    mcp_coder.llm | mcp_coder.prompt_manager
    mcp_coder.prompts
    mcp_coder.utils
    mcp_coder.mcp_tools_py | mcp_coder.mcp_workspace_git | mcp_coder.mcp_workspace_github
    mcp_coder.config | mcp_coder.constants
```

No "TBD" entries — if a dependency turns out to be unused at implementation
time, drop it from the tach `depends_on` list before commit.

## ALGORITHM

```
get_branch_info(project_dir):
    if not is_git_repository(project_dir):
        return BranchInfo(is_git_repo=False, branch_name=None, ...all None)
    branch = get_current_branch_name(project_dir)
    is_dirty = not is_working_directory_clean(project_dir)
    issue_number = extract_issue_number_from_branch(branch)
    title, label, last_checked = None, None, None
    if issue_number:
        try:
            repo_id = get_repository_identifier(project_dir)
            if repo_id is not None:
                cache_file = get_cache_file_path(repo_id)
                data = load_cache_file(cache_file)
                last_checked = parse_iso(data["last_checked"])
                issue = get_all_cached_issues(repo_id, issue_manager).get(issue_number)
                title = issue["title"]; label = first label starting with "status-"
        except Exception: pass
    return BranchInfo(True, branch, is_dirty, issue_number, title, label, last_checked)


get_pr_for_issue(project_dir, issue_number):
    repo_id = get_repository_identifier(project_dir)
    if repo_id is None: return None
    mgr = IssueBranchManager(project_dir=project_dir, repo_url=repo_id.https_url)
    branch_name = mgr.get_branch_with_pr_fallback(
        issue_number, repo_id.owner, repo_id.repo_name
    )
    if branch_name is None: return None
    prs = PullRequestManager(project_dir).find_pull_request_by_head(branch_name)
    if not prs: return None
    return prs[0].number       # or prs[0]["number"] if PullRequestData is a TypedDict
```

## DATA

- `BranchInfo` (frozen dataclass) — see `WHAT` above.
- `get_pr_for_issue` returns `int | None` — the PR number when a linked PR is
  found, else `None`. Two-step internal lookup (issue→branch→PR); see HOW
  and ALGORITHM above.

## Tests (TDD — write first)

In `tests/services/test_branch_info.py`:

1. `test_no_git_repo_returns_empty_branchinfo` — patch `is_git_repository` to
   return False; assert all fields None except `is_git_repo=False`,
   `is_dirty=False`.
2. `test_branch_without_issue_number` — patch git calls to return branch
   `"main"`; assert `issue_number is None`, no GH calls attempted.
3. `test_branch_with_issue_populates_from_cache` — patch git +
   `get_repository_identifier` (returns a fake `RepoIdentifier`) +
   `get_all_cached_issues` to return a dict with the issue; patch
   `load_cache_file` to return `{"last_checked": "2026-04-30T10:00:00+00:00",
   "issues": {...}}`; assert `issue_title`, `issue_status_label`, and
   `cache_last_checked` populated.
4. `test_gh_failure_keeps_branch_fields_returns_none_for_issue` — patch
   `get_all_cached_issues` to raise; assert branch+dirty still set, issue
   fields all None, no exception raised.
4b. `test_cache_miss_returns_branchinfo_with_none_issue_fields` — patch
    `get_all_cached_issues` to return `{}` (cache file missing or no
    entries) so the issue lookup misses; assert `BranchInfo` is still
    returned with `issue_title=None`, `issue_status_label=None`, and
    `cache_last_checked=None`, no exception raised. Branch+dirty still
    populated.
5. `test_dirty_detection_uses_shim` — patch `is_working_directory_clean` to
   return `False`; assert `BranchInfo.is_dirty is True`. Also assert with
   `True` → `is_dirty is False`. The data layer must NOT call
   `execute_subprocess` directly — verify by patching it with a sentinel
   raise on any call (the test should pass without ever invoking the
   sentinel).
6. `test_no_repo_remote_skips_gh_lookups` — patch
   `get_repository_identifier` to return `None`; assert `issue_title`,
   `issue_status_label`, `cache_last_checked` all `None` and no
   `get_all_cached_issues` call attempted (use a `Mock(side_effect=AssertionError)`
   sentinel).
7. **Parameterized** `test_status_label_picks_first_status_prefix` — issue
   carries multiple labels including more than one `status-*`-prefixed
   label. Document the assumption: per `labels.json` only one workflow
   status label should be present at a time, so the data layer picks the
   **first** label whose name starts with `status-`. Cases:
   - `["status-04:plan-review"]` → `"status-04:plan-review"`
   - `["bug", "status-04:plan-review"]` → `"status-04:plan-review"`
   - `["status-04:plan-review", "status-05:approved"]` →
     `"status-04:plan-review"` (first wins; document workflow constraint)
   - `[]` → `None`
   - `["bug"]` → `None`
8. `test_get_pr_for_issue_two_step_lookup` — patch
   `get_repository_identifier` to return a fake `RepoIdentifier(owner="o",
   repo_name="r", https_url="https://github.com/o/r.git")`; patch
   `IssueBranchManager.get_branch_with_pr_fallback` to return
   `"123-feature"`; patch
   `PullRequestManager.find_pull_request_by_head` to return
   `[PullRequestData(number=42, ...)]`; assert `42`.
9. `test_get_pr_for_issue_returns_none_when_no_branch_link` — patch
   `get_branch_with_pr_fallback` to return `None`; assert `None` and
   `find_pull_request_by_head` NOT called.
10. `test_get_pr_for_issue_returns_none_when_no_open_pr` — patch
    `get_branch_with_pr_fallback` to return `"branch"`; patch
    `find_pull_request_by_head` to return `[]`; assert `None`.
11. `test_get_pr_for_issue_no_repo_remote` — patch
    `get_repository_identifier` to return `None`; assert `None` and no
    manager constructed.

Run: `mcp__tools-py__run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration and not llm_integration and not textual_integration"])`.
Then pylint + mypy. Single commit when all green.
