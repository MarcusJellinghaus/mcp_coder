# Step 2: `mcp-coder rebase` workflow

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`. Step 1 is already committed. Write the tests first and confirm that the new "must stop" tests fail. Then implement, run the checks listed in the summary, and produce exactly one commit. Implement only this step.

## WHERE

| File | Change |
|---|---|
| `tests/workflows/rebase/test_workflow_branch_moved.py` | New test file |
| `tests/workflows/rebase/conftest.py` | `patched` fixture |
| `src/mcp_coder/workflows/rebase.py` | Two checks, docstring |
| `src/mcp_coder/cli/commands/rebase.py` | Exit contract |

## WHAT

No new functions. `workflows/rebase.py` imports the helper:

```python
from mcp_coder.workflow_steps.rebase import _check_branch_not_moved, _reset_hard
```

`_check_branch_not_moved(project_dir: Path, pre_sha: str) -> BranchCheck` never raises and does its own logging (Step 1).

## HOW

### First check

Place it right after the `pre_sha is None` return and before "Running baseline checks". `needs_rebase` has already fetched, so the tracking ref is current. Nothing has changed yet, so there is no restore.

### Second check

Place it right after the `_rebase_success_shape` block and before "Force-pushing (with lease)...". It sits inside the `try`, which is safe because the helper never raises.

### Docs

- `run_rebase_workflow` docstring: add both checks to the composed sequence, and name a moved branch in the exit-2 description.
- `cli/commands/rebase.py` exit contract: `2 = error / push rejected / branch moved`.

## ALGORITHM

```text
# first check
if _check_branch_not_moved(project_dir, pre_sha) in ("moved", "error"):
    return 2

# second check
if _check_branch_not_moved(project_dir, pre_sha) in ("moved", "error"):
    note = _restore_note(project_dir, pre_sha)
    logger.log(OUTPUT, "Aborted: not pushing%s", note)
    return 2
```

## DATA

Exit codes: `2` at both stops. All others are unchanged. A moved or error status never reaches `git_push`.

## Tests

### `tests/workflows/rebase/conftest.py`, `patched` fixture

Patch the helper's collaborators on `rebase_step_module`, as `reset_hard` already is, not on `rebase_module`. Default to a passing check:

```python
branch_name = MagicMock(return_value="feature")
remote_sha = MagicMock(return_value="remotesha")
merge_base = MagicMock(return_value="true")
monkeypatch.setattr(rebase_step_module, "get_current_branch_name", branch_name)
monkeypatch.setattr(rebase_step_module, "get_remote_branch_commit_sha", remote_sha)
monkeypatch.setattr(rebase_step_module, "git_merge_base", merge_base)
```

Add `merge_base` to the returned namespace. The fixture also serves `test_workflow.py`, `test_workflow_regression.py` and `test_workflow_safety_net.py`, which must keep passing unchanged.

### `tests/workflows/rebase/test_workflow_branch_moved.py`

Unit tests with `patched`:

| Case | Setup | Expected |
|---|---|---|
| First check moved | `merge_base.return_value = "false"` | Exit 2; `all_checks`, `reset` and `push` not called |
| First check error | `merge_base.side_effect = RuntimeError` | Same |
| Second check moved | `merge_base.side_effect = ["true", "false"]` | Exit 2; `reset` called with `"presha"`; `push` not called |
| Second check error | `merge_base.side_effect = ["true", RuntimeError("boom")]` | Same |
| Both pass | Default | Exit 0; `push` called |

Real-git tests with `bare_remote`, marked `@pytest.mark.git_integration`. On `mcp_coder.workflows.rebase`, stub only:

- `_preflight` returning `None`
- `_resolve_base_branch` returning `("main", None)`
- `prepare_llm_environment` returning `{}`
- `_run_all_checks`

Every case calls `bare_remote.move_base(...)` first. Without a moved base, `needs_rebase` exits 0 before any check, and the test would pass without the fix.

| Case | Setup | Expected |
|---|---|---|
| Foreign commit before the run | `push_foreign` before the call | Exit 2; `_run_all_checks` not called; remote unchanged |
| Foreign commit fetched just before the push | `_run_all_checks` side effect: on its second call, `push_foreign` then `local.git.fetch("origin")`; returns `set()` | Exit 2; remote unchanged; local HEAD back at the pre-rebase SHA |
| Normal rebase | `commit_local`, no foreign commit | Exit 0; remote at local HEAD |

## Precondition

If either foreign-commit real-git test passes before the implementation, write one line to `pr_info/.blocked.txt` and stop.
