# Step 9: A no-change CI fix counts as a failed attempt

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_9.md`. First add only the `get_latest_commit_sha` and `get_working_tree_status` imports to `ci_fix_helpers.py`, so the tests' patch targets exist. Then write the tests, and confirm the false-success test fails on its result assertion (`True` vs `False`) before changing any other code. An `AttributeError` does not count as that failure. Run the checks listed in the summary. Make exactly one commit's worth of change.

## WHERE

- `src/mcp_coder/workflow_steps/ci_fix_helpers.py`
- `src/mcp_coder/workflow_steps/ci.py`
- `tests/workflow_steps/test_ci_fix_helpers.py` (new)
- `tests/workflow_steps/test_ci_fix_loop.py`

## WHAT

```python
# ci_fix_helpers.py
@dataclass
class CIFixState:
    """Per-run state of the CI fix loop."""
    push_pending: bool = False

def read_head(project_dir: Path) -> str | None:
    """Return HEAD's SHA, or None on any failure. Never raises."""

def discard_if_no_change(project_dir: Path, head_before: str | None) -> bool:
    """Return True if the attempt changed nothing, and delete the unused message file.

    A failed read of HEAD or of the tree counts as "has changes". Never raises.
    """

# ci.py: keyword-only, optional, on both helpers; _run_ci_fix still returns bool
def _run_ci_fix(config, problem_description, fix_attempt, branch_name=None,
                *, state: CIFixState | None = None) -> bool: ...
def _run_ci_analysis_and_fix(config, ci_status, ci_manager, fix_attempt,
                             *, state: CIFixState | None = None) -> tuple[bool, bool | None]: ...
```

## HOW

- `ci_fix_helpers.py` imports `get_latest_commit_sha` and `get_working_tree_status` from `mcp_coder.mcp_workspace_git`, `DEFAULT_IGNORED_BUILD_ARTIFACTS` from `mcp_coder.constants`, and `COMMIT_MESSAGE_FILE` from `.constants`.
- Do not use `is_working_directory_clean`, which returns `True` on a status error and raises on a non-repo.
- Compare paths exactly: `get_working_tree_status` runs with `-uall` and returns repo-relative, forward-slash paths.
- `_run_ci_fix` calls `read_head` just before the fix `prompt_llm` call, so the baseline is per attempt. A baseline per run would read an earlier attempt's commit as a change.
- `check_and_fix_ci` creates one `CIFixState()` before its `for` loop and passes it down. `tests/ci_fix_drive.py` patches `ci.get_latest_commit_sha`, which does not affect the helpers, so its non-repo `tmp_path` still reads as "has changes".
- Keep `ci.get_latest_commit_sha` in place for its existing debug log.

## ALGORITHM

```python
# discard_if_no_change
try:
    if head_before is None or read_head(project_dir) != head_before: return False
    status = get_working_tree_status(project_dir)
    ignored = {COMMIT_MESSAGE_FILE, *DEFAULT_IGNORED_BUILD_ARTIFACTS}
    if not status["success"] or set(status["staged"] + status["modified"] + status["untracked"]) - ignored:
        return False
    (project_dir / COMMIT_MESSAGE_FILE).unlink(missing_ok=True)
    return True
except Exception: log a warning; return False  # An OSError from unlink also lands here
```

```python
# _run_ci_fix, after run_formatters
if discard_if_no_change(config.project_dir, head_before):
    if not (state and state.push_pending):
        logger.warning("CI fix produced no changes")
        return False
    logger.info("CI fix produced no changes; retrying the earlier failed push")
elif not commit_changes(...):
    logger.warning("Failed to commit CI fix changes")
    return False

if not push_changes(config.project_dir, raise_on_rejected=True):
    if state:
        state.push_pending = True
    logger.error("Git push failed during CI fix")
    return False
if state:
    state.push_pending = False
return True
```

If `unlink` fails after the tree read as clean, the helper returns `False`, so `commit_changes` runs as it does today. That failure is harmless.

## DATA

- `CIFixState.push_pending` is `True` after a non-rejected push failure, and `False` after any successful push.
- `discard_if_no_change` returns `bool`.

## TESTS

**`test_ci_fix_helpers.py`**, patching the helpers' git reads, except where noted:

- `read_head` returns the SHA, and returns `None` when the read raises.
- `discard_if_no_change` returns `True` for:
  - Same HEAD and a clean tree.
  - Only `pr_info/.commit_message.txt`, with the file removed (use a real file under `tmp_path`).
  - Only `uv.lock`.
- It returns `False` for:
  - A changed HEAD.
  - `head_before=None`, including when the current read is also `None`.
  - `success=False` from the status read.
  - The status read raising.
  - `read_head` returning `None`.
  - A real change alongside the message file, with the message file kept.
  - Each of a staged, modified or untracked real file.

**`test_ci_fix_loop.py`**, using `patch_ci_fix_externals` with `ci.run_formatters` patched, and patching `ci_fix_helpers.get_working_tree_status` and `ci_fix_helpers.get_latest_commit_sha` to control the result:

- **False success, written first:** clean tree and unchanged HEAD on every attempt, CI still failing. Assert the result first, so the red run shows `True` where `False` is expected. Result is `False`, `prompt_llm` is called `2 * CI_MAX_FIX_ATTEMPTS` times, and `commit_changes` and `push_changes` are not called.
- **Formatter-only change:** a tree that becomes dirty only through `run_formatters` still commits.
- **Failed push then no change:** attempt 1 is dirty and `push_changes` returns `False`; attempt 2 is clean with HEAD unchanged since that attempt began. `commit_changes` is called once, `push_changes` twice. When the retry succeeds, the loop waits for a new run as usual; give it a new green run and assert `True`.
- **Retry rejected:** the second `push_changes` raises `PushRejectedError`, and it propagates.
- **State cleared:** after a retry succeeds, a later no-change attempt does not push.
- **Real fix:** a prepared message file is left for `commit_changes`, which is called.

## Precondition

If `ci.py` is over 750 lines after this step, also move `_classify_ci_exception` to `ci_fix_helpers.py` the same way as step 8. If it is still over, write one line to `pr_info/.blocked.txt` and stop. Do not add it to `.large-files-allowlist`.
