# Step 1: `PushRejectedError` and opt-in detection in `push_changes`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`. Write the tests first, then the code. Run the checks listed in the summary, plus the `git_integration` tests in the new test file. Make exactly one commit's worth of change. Nothing calls the new keyword yet.

## WHERE

- `src/mcp_coder/workflow_steps/commit.py`
- `tests/workflow_steps/test_commit_push_rejected.py` (new)

## WHAT

```python
PUSH_REJECTED_ERROR = "Push rejected because the branch moved on the remote"

# Keep in step with #1382: re-running from a local checkout can reach the
# rebase-then-lease overwrite. Do not cite the issue number in the text itself,
# because these comments also post to other repositories.
BRANCH_MOVED_NEXT_STEP = (
    "The CI fix commit was not pushed. A Jenkins run's checkout is discarded, "
    "so the fix is lost and a re-run starts from the new branch tip. If this run "
    "came from a local checkout, discard that commit before re-running, because "
    "re-running from that checkout can overwrite the new commit. "
    "Check the new commit on the branch."
)

class PushRejectedError(Exception):
    """The remote rejected a push because the branch has moved."""

def _rejected_status_line(error: str) -> str | None: ...

def push_changes(
    project_dir: Path,
    force_with_lease: bool = False,
    *,
    raise_on_rejected: bool = False,
) -> bool: ...
```

## HOW

- Compile the regex at module level with `re.MULTILINE`:
  `^[ \t]*! \[rejected\] .*\((?:fetch first|non-fast-forward)\)`
- Raise outside the existing `try`, so its `except Exception` cannot swallow the error.
- Add a `Raises:` section to the `push_changes` docstring.

## ALGORITHM

```
rejected_line = None
try:
    result = git_push(...)
    if not result["success"]:
        log the error as today
        if raise_on_rejected: rejected_line = _rejected_status_line(result["error"] or "")
        if rejected_line is None: return False
    else: log success as today; return True
except Exception: log as today; return False
raise PushRejectedError(f"{PUSH_REJECTED_ERROR}: {rejected_line}")
```

## DATA

- `_rejected_status_line` returns the stripped status line, or `None`.
- `str(PushRejectedError)` is `"<PUSH_REJECTED_ERROR>: ! [rejected] <refs> (fetch first)"`.
- `push_changes` returns `bool` as today, and raises only when `raise_on_rejected=True` and the line matches.

## TESTS (`test_commit_push_rejected.py`)

**Unit tests, patching `commit.git_push`:**

- Both `fetch first` and `non-fast-forward` raise, in a `GitCommandError`-shaped multi-line string (`cmdline:` line, `stderr: 'To ...`, an indented status line, `hint:` lines).
- These cases return `False` and do not raise, even with `raise_on_rejected=True`:
  - `! [remote rejected] x -> x (pre-receive hook declined)`
  - `remote:  ! [rejected] x -> x (fetch first)`
  - A network failure whose `cmdline:` has a branch containing `rejected`
  - A network failure whose `cmdline:` has a branch containing `non-fast-forward`
  - An authentication failure
- A rejected push without the keyword returns `False`.
- An exception from `git_push` returns `False`.

**`@pytest.mark.git_integration`, real git through GitPython (the `subprocess_isolation` contract forbids subprocess in tests):**

- Create a bare repo with `git.Repo.init(bare=True)` and two clones, configured with `setup_git_config` as `tests/conftest.py` does. Keep the fixture local to this file.
- Clone B pushes a commit, then clone A commits. `push_changes(A, raise_on_rejected=True)` raises, and the message contains `(fetch first)`.
- Clone A then fetches. The same call raises, and the message contains `(non-fast-forward)`.
- The remote tip is still clone B's commit afterwards.

## Precondition

If real git's error text does not put the status line at the start of its own line, so the regex cannot match it, write one line to `pr_info/.blocked.txt` and stop.
