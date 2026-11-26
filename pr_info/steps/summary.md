# Summary: pass the pushed SHA to `check_and_fix_ci` in implement (#1484)

## Problem

Implement's step 5.6 calls `check_and_fix_ci` without `expected_sha`, which causes three problems:

- When the branch has no CI run, the poll runs the full `CI_MAX_POLL_ATTEMPTS` (about 12.5 min) before it gives up.
- An older commit's run (for example, the last task's push) can be taken as the result for the commit just pushed.
- In a repo whose CI cancels older runs, a cancelled run of the previous commit can be read as the result.

Review already passes `expected_sha` (`workflows/review/steps.py`). Implement should do the same.

## Design change

- **One call site changes:** `run_implement_workflow`, step 5.6, in `src/mcp_coder/workflows/implement/core.py`.
  It reads local HEAD with `get_latest_commit_sha(project_dir)` and passes it as
  `expected_sha` to `check_and_fix_ci`. The read is inline in the call, so it
  happens inside the existing `if current_branch:` block, right before the CI
  check. Like review's call, it is unguarded.
- **`None` keeps today's behaviour:** if HEAD can't be read, `expected_sha=None`
  is passed, which is what happens today.
- **The poll logic is unchanged.** `_poll_for_ci_completion` already handles
  `expected_sha`: a separate budget of about 105 s for "no run yet" or "another
  commit's run", and a run for another commit is never taken as the result.
- **Unchanged on purpose:** `workflow_steps/ci.py`, `fix_ci`, `check_branch_status`,
  create-pr, auto-merge, and the fix loop's own polls after its pushes. Neither
  `fix_ci` nor `check_branch_status` pushes before its call, so both keep `None`.
- **Test isolation:** many implement tests reach step 5.6 without patching
  `get_latest_commit_sha`. An autouse stub in `tests/workflows/implement/conftest.py`
  returns `None`, so those tests run against no real git and keep today's call
  shape. A test's own patch overrides it.

## Files modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/implement/core.py` | Import `get_latest_commit_sha` and pass `expected_sha=get_latest_commit_sha(project_dir)` at step 5.6 |
| `tests/workflows/implement/conftest.py` | Autouse fixture that stubs `core.get_latest_commit_sha` to return `None` |
| `tests/workflows/implement/test_core.py` | A test parametrized over `"PUSHEDSHA"` and `None` that asserts the `expected_sha` kwarg |

No files are created and no files are deleted.

## Steps

1. [step_1.md](./step_1.md): stub, test and implementation in one commit. The
   stub needs the import in `core.py`, so they can't be split.
