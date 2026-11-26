# Summary — #1486: `commit_changes` skips on a clean tree

## Problem

When a review round changes no files, `commit_changes`
(`src/mcp_coder/workflow_steps/commit.py`) still calls
`generate_commit_message_with_llm`. That call finds an empty diff, and the run logs:

- a WARNING from `commit_operations`
- an ERROR and a second WARNING from `commit_changes`, which then falls back to the static message
- the success line `Changes committed successfully: None - ...`

Jenkins' Text Finder marks a build UNSTABLE on any ` - WARNING - ` line, so a clean
round reads like a failure.

## Design change

All changes are local to `commit_changes`, plus one new private helper next to it.

1. **Clean-tree check inside `commit_changes`.** It runs after the prepared message
   file (`pr_info/.commit_message.txt`) has been read and deleted, and before the
   `if not commit_message:` block. If the tree is clean, it logs INFO
   `No changes to commit - skipping commit` and returns `True`. Message generation
   and `commit_all_changes` are not called.
   - It runs after the file is deleted, because the untracked message file would
     otherwise make the tree read dirty.
   - It stays inside `commit_changes`, after the callers' formatters, so a change
     made only by a formatter is still committed.
2. **New helper `_tree_is_clean(project_dir) -> bool` that never raises.**
   - It calls `get_working_tree_status`, imported through the
     `mcp_coder.mcp_workspace_git` shim.
   - It checks `success` before `clean`.
   - A raise or `success=False` gives one WARNING and returns `False` (dirty), so
     today's path continues.
   - It never returns a failure to the caller and never skips a real commit.
   - It does not use `is_working_directory_clean`, which reads a git error as clean.
   - It has no ignore list for build artifacts.
3. **Safety net after the commit.** When `commit_all_changes` succeeds with
   `commit_hash is None`, it logs INFO `No changes to commit` instead of the success
   line. The return value stays `True`.

### Contract

`commit_changes` still returns `True` on a clean tree (#1090), so review still pushes
and still carries the flushed round log. It returns `False` only on a git-level
commit failure, as today.

### Unchanged

- `generate_commit_message_with_llm`: the interactive CLI keeps failing loudly.
- `review/core.py`
- The CLI `mcp-coder commit`
- The other commit paths

### Known edge case

Stat-only line-ending dirt can make the tree read dirty while nothing is staged.
That case keeps today's fallback path.

## Files

| Path | Change |
|---|---|
| `src/mcp_coder/workflow_steps/commit.py` | modified: import, `_tree_is_clean`, early return, `None`-hash guard, docstring |
| `tests/workflow_steps/test_commit.py` | modified: autouse fixture in `TestCommitChanges` that patches the status to dirty; edge-case test moved out |
| `tests/workflow_steps/test_commit_clean_tree.py` | **new**: clean-tree, status-failure, edge-case and safety-net tests |
| `tests/workflows/review/test_core.py` | modified: `test_clean_tree_round_proceeds_normally` also asserts `push_changes` is called |

No new packages, modules or dependencies.

## Steps

1. Clean-tree check in `commit_changes`: `_tree_is_clean` plus the early return, and its tests.
2. Safety net: an INFO `No changes to commit` line when `commit_hash is None`.
3. Review regression guard: assert the push still happens on a clean round.
