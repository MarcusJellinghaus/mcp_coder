# Summary: Remove dead local `TaskTrackerStatus` enum (#1104)

## Goal

Delete the unused `TaskTrackerStatus` enum from
`mcp_coder.workflow_utils.task_tracker`. It has **zero production consumers** —
its only references are its own definition, its `__init__` re-export, and its own
pinning test. The only code that needs a task-tracker status
(`BranchStatusReport.tasks_status`) is typed against **upstream's**
`mcp_workspace.workflows.task_tracker.TaskTrackerStatus`, which the relevant test
files already import directly.

This is a **pure deletion with zero behavioural effect**.

## Architectural / design changes

- **Removes a duplicated-but-divergent type.** The local enum and upstream's are
  both `(str, Enum)` and share a name, but their `N_A` members differ
  (`local "N/A"` vs `upstream "N_A"`). Because both subclass `str`, a
  cross-comparison of `N_A` silently evaluates `False` instead of raising — a
  latent trap sitting under a shared-looking name. Deleting the local copy
  removes the trap.
- **Enforces the "one door" principle for this type.** If a consumer ever needs a
  task-tracker status enum, it should come from upstream via a shim, matching the
  `checks/branch_status.py` pattern established in #1068 (`bce0f22`, PR #1105).
  This change removes the second door.
- **Small public-surface API removal.** `mcp_coder.workflow_utils.__all__` is a
  public surface, so dropping `TaskTrackerStatus` from it is technically a minor
  API removal. It must be called out explicitly in the commit message, not landed
  as a silent tidy-up.

## Explicit non-goals / constraints (do not do these)

- **Do NOT shim the whole `task_tracker` module onto upstream.** The "one door"
  principle applies to the *enum only*. The local `task_tracker` module is a
  genuine fork with real behavioural divergence and ~8 live production importers
  (`workflows/implement/*`, `workflows/create_pr/core.py`,
  `workflows/create_plan/prerequisites.py`). It differs from upstream in:
  checkbox regex (accepts `[ ]` without leading dash vs requires `- [ ]`),
  section anchor (`Implementation` vs `## Tasks`), and `TASK_TRACKER_TEMPLATE`.
  Collapsing it onto upstream would change parsing behaviour.
- **Do NOT touch the five `test_check_branch_status*.py` files.** They import the
  enum from **upstream** (`mcp_workspace.workflows.task_tracker`), which is correct
  because the field they populate (`BranchStatusReport.tasks_status`) is
  upstream-typed.
- **The `N_A` display flip (`N/A` -> `N_A`) is already accepted.** It happened when
  #1068 made `tasks_status` upstream-typed; this deletion only removes the last
  trace of the old spelling from the repo. No upstream follow-up is planned.

## Folders / modules / files modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflow_utils/task_tracker.py` | Delete `TaskTrackerStatus` class; delete now-unused `from enum import Enum` |
| `src/mcp_coder/workflow_utils/__init__.py` | Remove `TaskTrackerStatus` from the `.task_tracker` import block and from `__all__` |
| `tests/workflow_utils/test_task_tracker.py` | Remove `TaskTrackerStatus` from the import block; delete the `TestTaskTrackerStatusEnum` class |

- **Files created:** none (besides these planning docs).
- **Files deleted:** none.
- **Files left intentionally untouched:** the five
  `tests/cli/commands/test_check_branch_status*.py` files (correct upstream import).

## Verification

- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_pytest_check` (fast unit subset via `-n auto` + the
  `not ...integration` marker exclusions)
- `mcp__tools-py__run_mypy_check`
- Post-change search for `TaskTrackerStatus` should show **only** the five
  upstream-importing test files remaining.

## Step index

- `step_1.md` — the complete deletion (single atomic commit).
