# Step 1: guard in `_attempt_rebase_and_push`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`. Write the tests first and confirm that the new "must stop" tests fail. Then implement, run the checks listed in the summary, and produce exactly one commit. Implement only this step.

## WHERE

| File | Change |
|---|---|
| `tests/conftest.py` | New `bare_remote` fixture |
| `tests/workflow_steps/test_rebase_branch_moved.py` | New test file |
| `tests/workflow_steps/test_rebase.py` | Autouse mocks, reason list |
| `tests/workflows/implement/test_core_failure_routing.py` | One new test |
| `src/mcp_coder/mcp_workspace_git.py` | Export `git_merge_base` |
| `src/mcp_coder/workflow_steps/rebase.py` | Reason, constants, helper, guard |

## WHAT

### `mcp_workspace_git.py`

```python
from mcp_workspace.git_operations.read_operations import git_diff, git_merge_base
```

Add `"git_merge_base"` to `__all__`.

### `workflow_steps/rebase.py`

- Import `get_current_branch_name`, `get_latest_commit_sha` and `git_merge_base`.
- Add `"branch_moved"` to `RebaseReason`.
- Add next to `RebaseReason`:

```python
BranchCheck = Literal["passed", "moved", "skipped", "error"]

BRANCH_MOVED_REASON = "`origin/<branch>` has commits this checkout does not have"
BRANCH_MOVED_NEXT_STEP = (
    "Check `origin/<branch>` for new commits, update or discard the local "
    "checkout, then re-run"
)

def _check_branch_not_moved(project_dir: Path, pre_sha: str) -> BranchCheck: ...
```

## HOW

- `get_remote_branch_commit_sha` is already imported. Keep comparing by its SHA, never by the name `origin/<branch>`.
- Step 2 imports the helper from this module, so it must not depend on `_attempt_rebase_and_push`.
- `_reset_hard` is defined later in the module; a call at runtime is fine.
- Reword the log line "manual push with --force-with-lease may be required", for example: "Rebase succeeded but push failed - check origin/<branch> before re-running; do not fetch and push with --force-with-lease".
- Update docstrings:
  - `_attempt_rebase_and_push`: add `"branch_moved"`, and say `push_failed` also covers a check that could not run.
  - `_reset_hard`: also undoes a rebase stopped by the branch check.
  - The module docstring needs no change.

## ALGORITHM

Helper:

```text
try:
    branch = get_current_branch_name; if None: warn "Could not verify"; return "error"
    remote_sha = get_remote_branch_commit_sha(branch); if None: debug log; return "skipped"
    result = git_merge_base(project_dir, ["--is-ancestor", remote_sha, pre_sha])
except Exception: warn "Could not verify", exc_info=True; return "error"
"true" -> "passed"; "false" -> warn BRANCH_MOVED_REASON + NEXT_STEP; return "moved"
anything else -> warn "Could not verify"; return "error"
```

The "Could not verify" line reads: "Could not verify `origin/<branch>`; not pushing".

In `_attempt_rebase_and_push`, after the `base_missing` return:

```text
pre_sha = get_latest_commit_sha; if None: warn; return RebaseOutcome("rebase_failed", target, _base_sha(target))
rebase as today; if not rebased: classify and return as today
status = _check_branch_not_moved(project_dir, pre_sha)
if status in ("moved", "error"):
    _reset_hard(project_dir, pre_sha)   # logs its own failure, never raises
    return RebaseOutcome("branch_moved" if status == "moved" else "push_failed", target, sha)
push as today
```

## DATA

- `_check_branch_not_moved` returns `BranchCheck`.
- `RebaseOutcome("branch_moved", target, sha)`: `.ok` is `False`, `files` is empty.
- A failed reset returns the same reason and still pushes nothing.

## Tests

### Fixture: `bare_remote` in `tests/conftest.py`

Function-scoped, using GitPython only and `setup_git_config`. It yields an object with methods, so that test packages do not import from each other. Close all repos at teardown.

Setup, which a probe confirmed working:

```python
git.Repo.init(tmp_path / "remote.git", bare=True, initial_branch="main")
seed = git.Repo.clone_from(bare, tmp_path / "seed")
# seed: checkout -b main, commit base, push -u origin main
# seed: checkout -b feature, commit feat1, push -u origin feature
local = git.Repo.clone_from(bare, tmp_path / "local", branch="feature")
foreign = git.Repo.clone_from(bare, tmp_path / "foreign", branch="feature")
```

| Member | Meaning |
|---|---|
| `local`, `local_dir`, `foreign` | The clones and the checkout path |
| `commit_local(name) -> str` | Commit a new file in `local`, not pushed |
| `push_foreign(name) -> str` | Commit and push from `foreign` to `feature` |
| `rewrite_remote() -> str` | `commit --amend` in `foreign` with a changed message or changed content, so the commit always gets a new SHA (not `--no-edit` alone: within the same second it can reproduce the same SHA), then `push --force` |
| `move_base(name) -> str` | Commit and push to `main` from `foreign`, then return to `feature` |
| `remote_sha(branch="feature") -> str` | The branch's SHA in the bare repo |
| `remote_log(branch="feature") -> list[str]` | The branch's SHAs in the bare repo |

### `tests/workflow_steps/test_rebase_branch_moved.py`

Patch only `mcp_coder.workflow_steps.rebase.detect_base_branch` to return `"main"` in the real-git tests. Mark them `@pytest.mark.git_integration`.

The real-git tests must run before the implementation, so this file must collect without the new names. At module level, import only what exists today. The unit tests get `BRANCH_MOVED_REASON` and `BRANCH_MOVED_NEXT_STEP` with a local import inside the test, or read them through the module at test time. The real-git tests compare against the literal `"branch_moved"`.

Must stop. Each asserts outcome `branch_moved`, an unchanged `remote_sha`, and local HEAD back at the captured SHA:

- foreign commit with an unpushed local commit
- foreign commit with an unpushed local commit and `move_base`, so the rebase really moves HEAD. This is the only real-git case where the HEAD assertion proves the reset; in the others the rebase leaves HEAD where it was
- stale checkout with no local commits
- remote rewritten by someone else's rebase
- a tag `origin/feature` at the local HEAD alongside a foreign commit

Must push, with outcome `ok` and the remote at local HEAD:

- normal rebase after `move_base`, with an unpushed local commit
- local commit ahead with nothing to rebase (review's round-log case)
- never-pushed branch: `local.git.checkout("-b", "fresh")` plus a commit; the check is skipped and the branch is created

Unit tests, mocking the collaborators with `tmp_path`:

| Case | Expected |
|---|---|
| `git_merge_base` raises | `push_failed`; `push_changes` not called; `reset_hard` called with the captured SHA |
| `get_current_branch_name` returns `None` | Same |
| `git_merge_base` returns unexpected text | Same |
| `git_merge_base` returns `"false"` | `branch_moved`; `push_changes` not called; `reset_hard` called with the captured SHA |
| `reset_hard` fails, on `moved` | `branch_moved`; no push; `reset_hard` called with the captured SHA |
| `reset_hard` fails, on `error` | `push_failed`; no push |
| `get_latest_commit_sha` returns `None` | `rebase_failed`; `rebase_onto_branch` and `push_changes` not called |
| `moved` | Warning contains `BRANCH_MOVED_REASON` and `BRANCH_MOVED_NEXT_STEP`; `reset_hard` called with the captured SHA |
| `git_merge_base` call | Arguments are the remote SHA and pre-rebase SHA, never a name |

This file needs `get_remote_branch_commit_sha` to branch on its argument, because `_base_sha` uses the same function.

### `tests/workflow_steps/test_rebase.py`

- Add autouse mocks on `mcp_coder.workflow_steps.rebase`:
  - `get_latest_commit_sha`: a fixed SHA
  - `get_current_branch_name`: `"feature"`
  - `git_merge_base`: `"true"`
- Add `"branch_moved"` to the list in `TestRebaseOutcome`.

### `tests/workflows/implement/test_core_failure_routing.py`

Copy the mock stack of `test_timeout_calls_handle_failure_with_llm_timeout`. With `mock_rebase.return_value = RebaseOutcome("branch_moved", "main", "abc1234")`, assert that `mock_process` was called, showing the workflow continues.

## Precondition

Run the "must stop" tests before the implementation. Each must fail on its own assertions, with outcome `ok` and the foreign commit gone from the remote. A collection `ImportError` does not count: fix the test file's imports and run them again.

If any "must stop" test passes before the implementation, write one line to `pr_info/.blocked.txt` and stop.
