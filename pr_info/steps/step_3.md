# Step 3 — Move `_poll_mergeable_state` to `workflow_steps/rebase.py`

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` exactly.
> Use `mcp__mcp-tools-py__move_symbol` for the move. Move/adapt the tests first, then the code.
> Run pylint, pytest (fast unit set, `-n auto`), mypy and lint-imports; all must pass.
> Format the code and make exactly one commit for this step.

## WHERE
- From `src/mcp_coder/workflows/fix_conflict/core.py`: `_poll_mergeable_state`, `_POLL_ATTEMPTS`, `_POLL_INTERVAL_SECONDS`
- To `src/mcp_coder/workflow_steps/rebase.py`
- `tests/workflow_steps/test_rebase.py`, `tests/workflows/fix_conflict/test_core.py`

## WHAT
```python
# workflow_steps/rebase.py
_POLL_ATTEMPTS = 6
_POLL_INTERVAL_SECONDS = 5

def _poll_mergeable_state(project_dir: Path, branch_name: str) -> str | None: ...  # body unchanged
```
Name, behaviour and docstring unchanged (it stays "private" like `_attempt_rebase_and_push`, which is already imported across modules).

## HOW
- `rebase.py` adds `import time` and `from mcp_coder.mcp_workspace_github import PullRequestManager`.
- `fix_conflict/core.py` imports `_poll_mergeable_state` from `mcp_coder.workflow_steps.rebase`
  and drops its own `time` / `PullRequestManager` imports if unused (`IssueManager` stays).
- Update the `fix_conflict/core.py` module docstring only if it now misdescribes where polling lives.

## Tests
- `tests/workflows/fix_conflict/test_core.py` `_patch_all`: patch `PullRequestManager` and `time.sleep` in
  `mcp_coder.workflow_steps.rebase` instead of the fix_conflict module. All existing parametrised cases
  (including `expected_sleeps`) must still pass.
- Add direct tests to `tests/workflow_steps/test_rebase.py`:
  - settled state on first poll → returned, no sleep;
  - `unknown` ×6 → `"unknown"`, 5 sleeps;
  - no PR (`[]`) ×6 → `None`, 5 sleeps;
  - `unknown` then `clean` → `"clean"`.

## DATA
`str | None` — last observed `mergeable_state`.
