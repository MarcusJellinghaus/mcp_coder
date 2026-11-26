# Step 1 — Clean-tree check in `commit_changes`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Write the tests first (TDD), then the implementation. Run pylint, mypy and the fast
> pytest suite, all with `-n auto` and the non-integration markers from CLAUDE.md, then
> run the formatter. Make exactly one commit for this step. Do not edit
> `pr_info/TASK_TRACKER.md`.

## Precondition

`get_working_tree_status` must be in `__all__` of `src/mcp_coder/mcp_workspace_git.py`.
If it is not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/workflow_steps/commit.py` (modify)
- `tests/workflow_steps/test_commit.py` (modify)
- `tests/workflow_steps/test_commit_clean_tree.py` (**new**)

## WHAT

```python
def _tree_is_clean(project_dir: Path) -> bool:
    """Return True only if git status succeeded and the tree is clean. Never raises."""
```

`commit_changes(...)` keeps its signature. Only its body and the `Returns:` section of
its docstring change.

## HOW

- Change the import to
  `from mcp_coder.mcp_workspace_git import commit_all_changes, get_working_tree_status, git_push`.
- Place `_tree_is_clean` directly above `commit_changes`.
- In `commit_changes`, insert the check inside the existing `try`:
  - **after** the prepared message file has been read and unlinked;
  - **before** `if not commit_message:`.

  The helper never raises, so the broad `except` cannot turn a failed check into a
  `False` return.

## ALGORITHM

```
_tree_is_clean:
    try: status = get_working_tree_status(project_dir)
         if status["success"]: return status["clean"]
         detail = status["error"]
    except Exception as e: detail = str(e)        # broad-exception-caught, pylint-disabled
    logger.warning(f"Could not read working tree status ({detail}); committing as usual")
    return False

commit_changes (inserted after the message-file block):
    if _tree_is_clean(project_dir):
        logger.info("No changes to commit - skipping commit"); return True
```

## DATA

`get_working_tree_status` returns a `StatusResult` dict with these keys:

- `success`, `error`, `returncode`, `stderr`
- `clean`
- `staged`, `modified`, `untracked`

`_tree_is_clean` returns a `bool`. `commit_changes` still returns `True` on a clean tree.

Update the `Returns:` docstring of `commit_changes` to say:

- A clean tree skips message generation and the commit, and returns `True`.
- A failed status read counts as dirty.

## Tests

### `tests/workflow_steps/test_commit.py`

1. **Patch the status to dirty for every `TestCommitChanges` test.**
   - Add an autouse fixture inside `TestCommitChanges`.
   - It patches `mcp_coder.workflow_steps.commit.get_working_tree_status` to return a
     successful dirty status: `success=True`, `clean=False`, `modified=["a.py"]`.
   - Without it, these tests (`/test/project`, or a `tmp_path` that is not a git repo)
     would take the failure path by accident.
2. **Move the old clean-tree test out.** Delete
   `test_commit_changes_clean_tree_flows_through_fallback` from this file; it moves to
   the new file, below.

### `tests/workflow_steps/test_commit_clean_tree.py` (new)

Setup:

- Add one helper `_status(success: bool = True, clean: bool = False) -> dict[str, object]`
  that builds a `StatusResult`-shaped dict. On failure: `error="git status failed (exit 128)"`
  and empty lists.
- Patch these three, all at `mcp_coder.workflow_steps.commit.*`:
  `get_working_tree_status`, `generate_commit_message_with_llm`, `commit_all_changes`.
- Use `caplog.set_level(logging.INFO)`.

Tests:

1. `test_clean_tree_skips_commit`
   - Status: clean.
   - Expect: `commit_changes(tmp_path)` is `True`; generation and `commit_all_changes`
     are not called; no caplog record with `levelno >= logging.WARNING`; the text
     `No changes to commit - skipping commit` is in caplog.
2. `test_clean_tree_with_prepared_message_deletes_file`
   - Setup: write `pr_info/.commit_message.txt` with `feat: x`. Status: clean.
   - Expect: `True`; the file no longer exists; `commit_all_changes` is not called.
3. `test_status_read_failure_proceeds_as_dirty`
   - Parametrize over two cases: `return_value=_status(success=False)` and
     `side_effect=RuntimeError("boom")`.
   - Generation returns `(True, "feat: m", None)`. The commit returns
     `{"success": True, "commit_hash": "abc123", "error": None}`.
   - Expect: `True`; generation called once; `commit_all_changes` called once; exactly
     one caplog record at `WARNING` and none at `ERROR`.
4. `test_dirty_status_nothing_staged_flows_through_fallback`
   - This is the renamed former `test_commit_changes_clean_tree_flows_through_fallback`,
     the stat-only line-ending dirt edge case.
   - Status: dirty. Generation returns `(False, "", "No changes to commit")`. The commit
     returns `commit_hash=None` with success.
   - Expect: `True`; `commit_all_changes` called once with
     `(FALLBACK_COMMIT_MESSAGE, tmp_path)`.

Docstrings say what the behaviour is and why, not what changed.

## Commit message

`fix(commit): skip commit_changes on a clean working tree`
