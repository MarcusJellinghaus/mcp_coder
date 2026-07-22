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

Do not move `test_rebase.py` wholesale. The `_get_rebase_target_branch` /
`_attempt_rebase_and_push` unit tests move to `tests/workflow_steps/test_rebase.py`; the
`TestRebaseIntegration::test_rebase_and_push_called_after_prerequisites` test is an
`implement/core` orchestration test and stays under `tests/workflows/implement/` (e.g.
`test_core.py`), with its rebase-call patch repointed to
`mcp_coder.workflows.implement.core._attempt_rebase_and_push`. After the split,
`implement/rebase.py` likely has no remaining patch target and is removed.

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
