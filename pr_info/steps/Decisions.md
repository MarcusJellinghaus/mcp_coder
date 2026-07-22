# Plan Update Decisions

Decisions applied to the plan following the plan-review round (2026-07-22). All five
findings were triaged and accepted as aligning with the issue's explicit decisions
(no scope/architecture change).

## 1. (B1) CLI production consumer of `check_and_fix_ci` — Step 4

`src/mcp_coder/cli/commands/check_branch_status.py:32` imports `check_and_fix_ci` from
`implement.ci_operations`. This is the only cross-package production consumer and was
missing from the plan. Decision: repoint it to `mcp_coder.workflow_steps.ci` alongside
`implement/core.py`. Because both production consumers are then repointed,
`implement/ci_operations.py` needs no permanent production shim — it stays only as a
**reactive** re-export shim if a red test reveals a broken patch target (consistent with
the issue's reactive-shim decision).

## 2. (B2) `test_rebase.py` split — Step 3

Do not move `test_rebase.py` wholesale, but move **all of its test classes** to
`tests/workflow_steps/test_rebase.py`. It has two kinds of test, and both exercise the
moved step:

- `TestGetRebaseTargetBranch` — the `_get_rebase_target_branch` unit tests.
- `TestRebaseIntegration` — **five** methods
  (`test_rebase_and_push_called_after_prerequisites`,
  `test_push_with_force_with_lease_after_successful_rebase`,
  `test_workflow_continues_when_rebase_fails`,
  `test_rebase_skipped_when_no_target_branch`,
  `test_workflow_continues_when_push_after_rebase_fails`). Despite the "integration"
  name, these drive `run_implement_workflow` only to reach the rebase step, then assert
  on the **internals** of the real `_attempt_rebase_and_push` (e.g. push called with
  `force_with_lease=True`; workflow never blocked when rebase or push fails). They patch
  the step's callees at `mcp_coder.workflows.implement.rebase.*`
  (`.push_changes`, `.rebase_onto_branch`, `._get_rebase_target_branch`), **not**
  `_attempt_rebase_and_push` itself.

Because they exercise the moved step's real body, all five move to
`tests/workflow_steps/test_rebase.py` alongside the unit tests, with their patch targets
repointed from `mcp_coder.workflows.implement.rebase.*` to
`mcp_coder.workflow_steps.rebase.*`. **Do NOT** repoint them to
`core._attempt_rebase_and_push` — patching the function wholesale would delete the very
internal assertions they exist for. (The `core.*` prerequisite patches they also set
keep working unchanged, since those symbols stay bound on `implement.core`.)

Core-level orchestration coverage that patches `_attempt_rebase_and_push` **wholesale**
already exists **separately** in `tests/workflows/implement/test_core_workflow.py` (and
`test_failure_reporting.py`); it patches `mcp_coder.workflows.implement.core._attempt_rebase_and_push`
and needs **no change**. So nothing rebase-related stays behind under
`tests/workflows/implement/`.

After moving all five, no test references `mcp_coder.workflows.implement.rebase.*`, so
`implement/rebase.py` has no remaining patch target and is removed — the removal holds
precisely *because* these five tests move to `workflow_steps`.

## 3. (I1) Mandatory `task_processing.py` self-import — Step 2

`process_single_task` (staying in `implement`) calls the three moved functions, so
`task_processing.py` must add `from mcp_coder.workflow_steps.commit import commit_changes,
push_changes, run_formatters` for its own production body. This is a required edit, not a
reactive test-patch shim.

## 4. (I2) `PR_INFO_DIR` clarity note — Step 4

`PR_INFO_DIR` (used at `ci_operations.py:157`) is intentionally absent from Step 4's
constant list because Step 2 already relocated it to `workflow_steps/constants.py`; `ci.py`
imports it from `.constants`. Not missing.

## 5. (I3) Exception-scope delta in `check_git_clean` — Step 5

The shared `check_git_clean` narrows create_pr's current catch (all exceptions → False) to
`ValueError` → False. Since `is_working_directory_clean` is documented to raise
`ValueError`, this is practically equivalent — accepted as a conscious choice rather than
widening the shared step's catch.
