# Step 1 — Shim: use `get_issue_cache_last_checked`, drop underscore cache aliases

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`).
> Implement only Step 1. Write/adjust the tests first, then the code.
> Run pylint, pytest (fast unit marker set from CLAUDE.md, `-n auto`) and mypy;
> all must pass. Produce exactly one commit.

## WHERE
- `src/mcp_coder/mcp_workspace_github.py`
- `src/mcp_coder/services/branch_info.py`
- `tests/services/test_branch_info.py`
- `tests/test_mcp_workspace_github_cache.py` (delete)
- `tests/test_mcp_workspace_github_exports.py` (new)

## WHAT
- Shim: add `get_issue_cache_last_checked` to the `issues` import and `__all__`.
  Remove the four underscore aliases (`get_cache_file_path`, `load_cache_file`,
  `save_cache_file`, `log_stale_cache_entries`) and their `__all__` entries.
- `branch_info.get_branch_info`: replace
  ```python
  cache_path = get_cache_file_path(repo_id)
  cache_data = load_cache_file(cache_path)
  last_checked = _parse_iso(cache_data.get("last_checked"))
  ```
  with `last_checked = get_issue_cache_last_checked(repo_id)`.
  Delete `_parse_iso` if it has no other user.

## HOW
- Signature (library): `get_issue_cache_last_checked(repo_identifier: RepoIdentifier) -> datetime | None`.
- Tests in `tests/services/test_branch_info.py`: replace the two patches
  (`get_cache_file_path`, `load_cache_file`) with one patch of
  `f"{BRANCH_INFO_MODULE}.get_issue_cache_last_checked"` returning a datetime
  (or raising the sentinel where the test expects a failure).
- New `tests/test_mcp_workspace_github_exports.py`:
  - `get_issue_cache_last_checked` is importable from `mcp_coder.mcp_workspace_github`;
  - none of the four alias names is an attribute of the shim.
- Delete `tests/test_mcp_workspace_github_cache.py` (no replacement).

## DATA
`BranchInfo.cache_last_checked` keeps type `datetime | None`.
