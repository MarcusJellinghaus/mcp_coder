# Step 1 — Shim: re-export `create_empty_issue_data`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Write the test change first, then the implementation. Run the checks listed in the
> summary; all must pass. Produce one commit.

## Precondition

`create_empty_issue_data` must be importable from `mcp_workspace.github_operations.issues`
(check with `mcp__mcp-tools-py__get_library_source`). If it is not, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE
- `tests/test_mcp_workspace_github_smoke.py`
- `src/mcp_coder/mcp_workspace_github.py`

## WHAT

Test (first):
- `test_all_exports_defined`: `assert len(__all__) == 32`.
- New `test_create_empty_issue_data_importable() -> None`, modelled on
  `test_get_github_token_importable`: import `__all__, create_empty_issue_data` from the
  shim; assert `create_empty_issue_data()["number"] == 0` and
  `"create_empty_issue_data" in __all__`.

Implementation:
- Add `create_empty_issue_data` to the existing import block
  `from mcp_workspace.github_operations.issues import (CacheData, ..., IssueData, ...)`
  (alphabetical position).
- Add `"create_empty_issue_data"` to `__all__` in the `# Issues` group, after `"EventData"`.

## HOW
Plain re-export; no wrapper function.

## DATA
`create_empty_issue_data() -> IssueData` with `number=0`, empty strings, `None`, empty lists,
`locked=False`, `author_association=None`.
