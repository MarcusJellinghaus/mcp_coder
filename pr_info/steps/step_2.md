# Step 2 — A rebase that left HEAD equal to `origin/<branch>` does not push

Read `pr_info/steps/summary.md` first.

## WHERE

- `src/mcp_coder/workflow_steps/rebase.py`: new `_up_to_date_branch`, a change
  in `_attempt_rebase_and_push`, and docstrings
- `src/mcp_coder/workflows/review/steps.py`: comment and docstring text only
- `tests/workflow_steps/test_rebase.py`: two existing tests, edited in place
  (the file is at 708 of 750 lines)
- `tests/workflow_steps/test_rebase_branch_moved.py`: new class `TestUpToDate`

## WHAT

```python
def _up_to_date_branch(project_dir: Path) -> str | None:
    """Return the branch when HEAD equals ``origin/<branch>``; None otherwise. Never raises."""
```

## HOW

Place `_up_to_date_branch` directly after `_check_branch_not_moved`. In
`_attempt_rebase_and_push`, after the `if status in ("moved", "error"):` block
and before `push_changes(...)`:

```python
branch = _up_to_date_branch(project_dir)
if branch:
    logger.info("Already up to date with origin/%s; nothing to push", branch)
    return RebaseOutcome("ok", target, sha)
```

It uses only functions the module already imports: `get_current_branch_name`,
`get_latest_commit_sha` and `get_remote_branch_commit_sha`. No new imports.

## ALGORITHM

```
try:
    branch = get_current_branch_name(project_dir)
    head = get_latest_commit_sha(project_dir)          # call order matters for the "raises" test
    remote = get_remote_branch_commit_sha(project_dir, branch) if branch else None
except Exception:                                      # broad, with pylint disable comment
    logger.debug("Could not compare HEAD with origin/<branch>; pushing", exc_info=True)
    return None
return branch if head and head == remote else None
```

Never use `logger.warning` here.

## DATA

- `_up_to_date_branch` returns `str | None`.
- `_attempt_rebase_and_push` returns `RebaseOutcome("ok", target, sha)` on the
  new path. That is the same shape as a successful push.

## Docstrings and comments to update

- `RebaseOutcome.ok`: "Return True only when the rebase succeeded and
  ``origin/<branch>`` holds HEAD (pushed here or already there)."
- Returns section of `_attempt_rebase_and_push`: `"ok"` when the rebase
  succeeded and the push succeeded or was not needed, because HEAD already
  equals `origin/<branch>`.
- `review/steps.py`:
  - In the comment before `pushed_sha = get_latest_commit_sha(project_dir)`:
    "The rebase step just pushed local HEAD" becomes "After the rebase step,
    origin/<branch> holds local HEAD (pushed by it, or already there)". Keep the
    rest of the comment.
  - In the `_after_steps` docstring: "the SHA the rebase step just pushed"
    becomes "local HEAD, which the rebase step left on origin".

## Tests (write first)

### `tests/workflow_steps/test_rebase.py` (edit in place, no net growth beyond a few lines)

In `TestAttemptRebaseOutcomes.test_ok` and `test_push_failed`, the autouse
mocks return `_FULL_SHA` for both HEAD and the remote. The push would then be
skipped and `test_push_failed` would fail. Replace
`mock_remote_sha.return_value = _FULL_SHA` with:

```python
mock_remote_sha.side_effect = lambda _d, b: _FULL_SHA if b == "main" else None
```

`origin/feature` is then absent, the branch check is skipped, and the push runs.
In `test_ok`, add `mock_push.assert_called_once_with(tmp_path, force_with_lease=True)`.

### `tests/workflow_steps/test_rebase_branch_moved.py`: new `class TestUpToDate`

Reuse the existing `mocks` fixture. By default, HEAD is `_PRE_SHA` and
`origin/feature` is `_REMOTE_SHA`, so they differ.

| Test | Setup | Assert |
|------|-------|--------|
| `test_head_equals_remote_skips_push` | `mocks.latest_sha.return_value = _REMOTE_SHA` | `outcome.reason == "ok"`, `mocks.push.assert_not_called()`, an INFO record containing `Already up to date with origin/feature` |
| `test_head_differs_pushes` (docstring: also covers HEAD unchanged by the rebase while the remote is behind) | Fixture default | `push` called once with `(tmp_path, force_with_lease=True)`, reason `ok` |
| `test_no_upstream_pushes` | Inside the test, `patch(f"{_MODULE}.get_remote_branch_commit_sha", lambda _d, b: _BASE_SHA if b == "main" else None)` | `push` called once, reason `ok` |
| `test_comparison_raises_pushes` | `mocks.latest_sha.side_effect = [_PRE_SHA, RuntimeError("boom")]` | `push` called once, reason `ok`, no WARNING record |

The moved and error paths are covered by the existing `TestGuardUnit`, which
must stay green unchanged. The real-git `TestMustPush.test_never_pushed_branch`
must keep passing (run with marker `git_integration`).

Also run `tests/workflow_steps/test_rebase_line_endings.py`,
`tests/workflows/rebase/` and `tests/workflows/review/`. A test that asserted a
force-push while HEAD already equalled `origin/<branch>` now sees no push. Only
update such a test when its setup really has nothing to push. If a test fails
for any other reason, write one line to `pr_info/.blocked.txt` and stop.

## LLM prompt

> Implement Step 2 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_2.md`.
>
> 1. Write the `TestUpToDate` tests in
>    `tests/workflow_steps/test_rebase_branch_moved.py` and apply the in-place
>    edit to `tests/workflow_steps/test_rebase.py`. See the new skip test fail.
> 2. Add `_up_to_date_branch` to `src/mcp_coder/workflow_steps/rebase.py` and
>    call it in `_attempt_rebase_and_push` after the branch check, before the
>    push.
> 3. Update the `RebaseOutcome.ok` docstring, the Returns section of
>    `_attempt_rebase_and_push`, and the comment and `_after_steps` docstring in
>    `src/mcp_coder/workflows/review/steps.py`.
> 4. Run `run_format_code`, then pylint, mypy and pytest (fast unit set with
>    `-n auto`, plus `markers=["git_integration"]`), and fix any findings.
> 5. Commit as one commit: `fix(rebase): skip the force-push when HEAD already equals origin/<branch>`.
