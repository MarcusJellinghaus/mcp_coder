# Step 1 — Data-layer `get_branch_only`

## LLM Prompt

> Read `pr_info/steps/summary.md` and then implement `pr_info/steps/step_1.md`.
> This step is a pure addition to the data layer: a cheap branch-only
> snapshot function with full test coverage. Do not modify any other files
> or call sites yet — Steps 2 and 3 wire it up.
>
> After the change, run all three quality checks (pylint, pytest, mypy)
> and confirm they pass before producing the single commit for this step.

## WHERE

| Path | Action |
|------|--------|
| `src/mcp_coder/services/branch_info.py` | Add new top-level function `get_branch_only` |
| `tests/services/test_branch_info.py` | Add unit tests for `get_branch_only` |

## WHAT

```python
def get_branch_only(project_dir: Path) -> BranchInfo:
    """Return a cheap branch-only ``BranchInfo`` snapshot.

    Populates only the fields obtainable without GitHub or cache I/O:
    ``is_git_repo``, ``branch_name``, ``is_dirty``, and ``issue_number``
    (parsed from the branch name). The remaining three fields
    (``issue_title``, ``issue_status_label``, ``cache_last_checked``)
    are always ``None``.
    """
```

## HOW

- Reuse the four imports already in `branch_info.py`:
  `is_git_repository`, `get_current_branch_name`, `is_working_directory_clean`,
  `extract_issue_number_from_branch`. **No new imports.**
- Outside a git repo, return the existing module-level `_EMPTY` constant.
- Do **not** touch `get_repository_identifier`, `get_cache_file_path`,
  `load_cache_file`, `IssueManager`, or `get_all_cached_issues` — those are
  the expensive paths and must not be reachable from `get_branch_only`.

## ALGORITHM

```
if not is_git_repository(project_dir):
    return _EMPTY
branch     = get_current_branch_name(project_dir)
is_dirty   = not is_working_directory_clean(project_dir)
issue_num  = extract_issue_number_from_branch(branch) if branch else None
return BranchInfo(is_git_repo=True, branch_name=branch, is_dirty=is_dirty,
                  issue_number=issue_num, issue_title=None,
                  issue_status_label=None, cache_last_checked=None)
```

## DATA

Returns `BranchInfo` (the existing frozen dataclass). For `_EMPTY`, returns
the existing module sentinel unchanged. Three fields are guaranteed `None`
on every successful return.

## Tests

In `tests/services/test_branch_info.py`, mirror the patching style used by
the existing `get_branch_info` tests. Patch all four imported helpers under
`mcp_coder.services.branch_info.<name>`.

1. `test_get_branch_only_no_git_repo_returns_empty` —
   `is_git_repository` patched to `False`, asserts `info == _EMPTY` shape
   (or an equivalent `BranchInfo(is_git_repo=False, ...)`).
2. `test_get_branch_only_branch_with_issue_number` —
   branch `"42-feature"`, dirty=False, regex returns 42; assert
   `branch_name == "42-feature"`, `is_dirty is False`, `issue_number == 42`,
   and the three None fields are `None`.
3. `test_get_branch_only_branch_without_issue_number` —
   branch `"main"`, regex returns None; assert `issue_number is None`.
4. `test_get_branch_only_skips_github_and_cache_io` —
   patch `get_repository_identifier`, `get_cache_file_path`,
   `load_cache_file`, `IssueManager`, `get_all_cached_issues` with a
   sentinel `Mock(side_effect=AssertionError("must not be called"))` and
   assert the function still returns a populated `BranchInfo`.
5. `test_get_branch_only_dirty_flag` —
   parametrised `(is_working_directory_clean returns True/False) →
   info.is_dirty is False/True`.

## Acceptance

- `mcp__tools-py__run_pylint_check` clean.
- `mcp__tools-py__run_pytest_check` (with the standard `-n auto` + the
  CLAUDE.md exclusion markers) green; the new tests run.
- `mcp__tools-py__run_mypy_check` clean.
- A single commit named e.g. `feat(branch-info): add cheap get_branch_only`.
