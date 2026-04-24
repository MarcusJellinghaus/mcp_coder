# Summary: Add `--push` flag to commit auto and commit clipboard

**Issue:** #907

## Goal

Add a `--push` flag to `mcp-coder commit auto` and `mcp-coder commit clipboard` that pushes the current branch to origin after a successful commit.

## Architecture / Design Changes

- **No new files or modules** — all changes are within existing files.
- **One new private helper** `_push_after_commit(project_dir: Path) -> int` added to `commit.py`. Uses the existing module-level `logger`. Encapsulates all push logic (branch detection, safety guard, push with/without upstream) so both execute functions call a single function.
- **New imports** in `commit.py` from the existing `mcp_workspace_git` shim: `get_current_branch_name`, `get_default_branch_name`, `has_remote_tracking_branch`, `git_push`, `push_branch`.
- **Parser additions** — `--push` flag (store_true) added to both `auto_parser` and `clipboard_parser` in `parsers.py`.
- **No changes to exit code semantics** — push failure reuses exit code `2` (same as commit failure).

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/parsers.py` | Add `--push` argument to `auto_parser` and `clipboard_parser` |
| `src/mcp_coder/cli/commands/commit.py` | Add imports, `_push_after_commit()` helper, call it from both execute functions |
| `tests/cli/test_parsers.py` | Add parser acceptance tests for `--push` |
| `tests/cli/commands/test_commit.py` | Add tests for `_push_after_commit` and integration with execute functions |

## Behavior Summary

1. After successful commit, if `--push` is set, call `_push_after_commit(project_dir)`
2. Get current branch; refuse to push if it matches the default branch (or `main`/`master` as fallback)
3. If no remote tracking branch: `push_branch(branch, project_dir, set_upstream=True)` → returns `bool`
4. If has tracking branch: `git_push(project_dir)` → returns `dict` with `"success"` key
5. Log result; return 0 on success, 2 on failure

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Parser: add `--push` flag + parser tests | `feat(cli): add --push flag to commit auto and clipboard parsers` |
| 2 | `_push_after_commit` helper + unit tests | `feat(cli): add _push_after_commit helper with safety guards` |
| 3 | Wire `--push` into both execute functions + integration tests | `feat(cli): integrate --push into commit auto and clipboard` |
