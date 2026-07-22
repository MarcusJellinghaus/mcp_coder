# Workflow-step library refactor (Issue #1071) — Implementation Summary

## Goal

Create a new **`mcp_coder.workflow_steps`** layer and migrate the reusable steps of
the `implement` workflow onto it, so the automated-review workflows (#1072) have a
single shared foundation. This is **behavior-preserving** for `create-plan`,
`implement`, and `create-pr` — no observable change. Ships independently, ahead of
#1072 / #1073.

## Architectural / design changes

### 1. A new middle tier (`workflow_steps`)

Today the code has two tiers: **workflows** (thin orchestrators that own labels,
config, per-workflow `FailureCategory`, and sequence the work) and **primitives**
(`workflow_utils/` + `checks/`). This refactor inserts the missing middle tier:

```
workflows            thin orchestrators (create_plan, create_pr, implement)
   ↓
workflow_steps  ★NEW  workflow-agnostic composed steps (commit/push, rebase, CI, prereqs)
   ↓
workflow_utils | checks   single-purpose primitives / assessments
```

**Why a new layer and not `workflow_utils`:** the CI step composes
`checks.get_failed_jobs_summary`, and `checks` sits *above* `workflow_utils` in the
import-linter layer contract (`checks/branch_status.py` imports `workflow_utils`).
A CI step placed in `workflow_utils` would be an **upward import → contract
violation**. Any step that consumes a `check` must live at/above `checks`;
`workflow_steps` above both is the only clean single home.

### 2. Dual boundary enforcement (both must stay green at every commit)

- **`.importlinter`** `layered_architecture`: a new layer line
  `mcp_coder.workflow_steps` inserted **between** `mcp_coder.workflows` and
  `mcp_coder.services | mcp_coder.checks`. (This is the real upward-import guard.)
- **`tach.toml`**: a new `[[modules]]` entry (layer `application`) with `depends_on`
  derived from the moved code's **actual** imports, plus `workflow_steps` added to
  `mcp_coder.workflows` and `tests` `depends_on`. (tach's allow-list is the only
  enforcer that catches an under-specified dependency list.)

### 3. Constants relocated **by re-export** (KISS)

The 9 generic CI/commit tuning constants move down into
`workflow_steps/constants.py` (a step importing them from `implement/constants.py`
would be an upward import). To avoid churning production call sites,
`implement/constants.py` simply **re-imports** the ones that staying-in-`implement`
code still uses (`PR_INFO_DIR`, `COMMIT_MESSAGE_FILE`, `LLM_INACTIVITY_TIMEOUT_SECONDS`).
Every `from .constants import …` line in `implement` keeps working unchanged.
`RUN_MYPY_AFTER_EACH_TASK`, `MAX_NO_CHANGE_RETRIES`, `FailureCategory`,
`WorkflowFailure` **stay** in `implement`.

### 4. Loop-ready CI signature via defaulted parameters (KISS)

`check_and_fix_ci` gains three keyword args — `analysis_prompt_header`,
`fix_prompt_header`, `session_dir_name` — **defaulting to `implement`'s current
literals**. `implement`'s call site does not change (byte-identical); #1072
overrides them per review round. Same idea for the session dir
(`.mcp-coder/implement_sessions`).

### 5. Prerequisite extraction (pure kernels)

The duplicated sub-checks are extracted as small, pure helpers:
- `check_git_clean(project_dir)` — the shared cleanliness determination.
- `is_branch_not_base(current_branch, base_branch)` — a **pure comparison**; each
  orchestrator resolves its own base (implement → default branch;
  create_pr → `detect_base_branch`, which can be a custom base) and passes it in.
  This preserves create_pr's custom-base semantics without the step ever resolving.

### 6. Re-export shims (reactive) vs. production import migration

Moved symbols keep a thin re-export in their original module **only where a red test
reveals a broken `patch("…implement.…")` target** — no upfront inventory. **Distinct from
this** are the *production* import migrations, which are mandatory (not reactive): the
`cli/commands/check_branch_status.py` repoint of `check_and_fix_ci` (Step 4), the
`task_processing.py` self-import of commit/push/run_formatters for `process_single_task`
(Step 2), and the constant re-exports in `implement/constants.py`.

## What moves (and what stays)

| Symbol | From | To |
|--------|------|----|
| `run_formatters`, `commit_changes`, `push_changes` | `implement/task_processing.py` | `workflow_steps/commit.py` |
| `_attempt_rebase_and_push`, `_get_rebase_target_branch` | `implement/rebase.py` | `workflow_steps/rebase.py` |
| `check_and_fix_ci` + CI helpers + `CIFixConfig` | `implement/ci_operations.py` | `workflow_steps/ci.py` |
| `check_git_clean` (kernel), `is_branch_not_base` | `implement/prerequisites.py`, `create_pr/core.py` | `workflow_steps/prerequisites.py` |
| 9 tuning constants | `implement/constants.py` | `workflow_steps/constants.py` |

**Stays in `implement`:** `process_single_task`, `process_task_with_retry`,
`check_and_fix_mypy`, `_run_mypy_check`, `get_next_task`, `_cleanup_commit_message_file`,
task-tracker prep, `finalisation`, `core`, `FailureCategory`/`WorkflowFailure`,
`RUN_MYPY_AFTER_EACH_TASK`, `MAX_NO_CHANGE_RETRIES`. **`create_plan`/`create_pr`
orchestrator LLM calls are NOT refactored** in this issue (out of the enumerated Scope;
no #1072 benefit).

## Files / folders created or modified

### Created
- `src/mcp_coder/workflow_steps/__init__.py`
- `src/mcp_coder/workflow_steps/py.typed`
- `src/mcp_coder/workflow_steps/constants.py`
- `src/mcp_coder/workflow_steps/commit.py`
- `src/mcp_coder/workflow_steps/rebase.py`
- `src/mcp_coder/workflow_steps/ci.py`
- `src/mcp_coder/workflow_steps/prerequisites.py`
- `tests/workflow_steps/__init__.py`
- `tests/workflow_steps/test_scaffold.py`
- `tests/workflow_steps/test_commit.py`
- `tests/workflow_steps/test_rebase.py`
- `tests/workflow_steps/test_ci.py`
- `tests/workflow_steps/test_prerequisites.py`

### Modified
- `.importlinter` — add `workflow_steps` layer + `tests.workflow_steps` to independence contract
- `tach.toml` — add `[[modules]]` for `workflow_steps`; add it to `workflows` and `tests` `depends_on`
- `src/mcp_coder/workflows/implement/constants.py` — remove relocated constants, re-export shared ones
- `src/mcp_coder/workflows/implement/task_processing.py` — remove 3 moved funcs; add mandatory `from workflow_steps.commit import …` for its own `process_single_task` body
- `src/mcp_coder/workflows/implement/__init__.py` — repoint the `commit_changes`/`push_changes`/`run_formatters` package re-export to import them **directly** from `workflow_steps.commit` (explicit, not via the self-import re-binding); `__all__` unchanged
- `src/mcp_coder/workflows/implement/ci_operations.py` — reactive re-export shim only (both production consumers repointed in Step 4); removed if no red test needs it
- `src/mcp_coder/workflows/implement/rebase.py` — removed once no patch target references it after the Step 3 test split (reactive shim only otherwise)
- `src/mcp_coder/workflows/implement/finalisation.py` — import `push_changes` from `workflow_steps`
- `src/mcp_coder/workflows/implement/core.py` — import moved steps from `workflow_steps`
- `src/mcp_coder/workflows/implement/prerequisites.py` — use shared `check_git_clean` / `is_branch_not_base`
- `src/mcp_coder/workflows/create_pr/core.py` — use shared `check_git_clean` / `is_branch_not_base`
- `src/mcp_coder/cli/commands/check_branch_status.py` — repoint `check_and_fix_ci` import to `workflow_steps.ci` (only cross-package production consumer; Step 4)

### Moved (tests relocated to mirror the source move)
- CI / commit-push tests → `tests/workflow_steps/` (patch targets updated to `mcp_coder.workflow_steps.*`)
- rebase tests → **all** move to `tests/workflow_steps/test_rebase.py` (Step 3): `TestGetRebaseTargetBranch` **and** all **five** `TestRebaseIntegration` methods. The integration methods assert on the internals of the real `_attempt_rebase_and_push` (e.g. `force_with_lease=True`), so their callee patches are repointed from `implement.rebase.*` to `workflow_steps.rebase.*` — **not** repointed to `core._attempt_rebase_and_push` (patching it wholesale would delete their assertions). Nothing rebase-related stays under `tests/workflows/implement/`; core-level wholesale coverage already lives in `test_core_workflow.py` / `test_failure_reporting.py` (unchanged). `implement/rebase.py` is removed once no `implement.rebase.*` patch target remains.

## Step sequence (one commit each; order is dependency-constrained)

1. **Scaffold the `workflow_steps` layer** — package + `py.typed` + both enforcers + empty test package.
2. **Move commit / push / run_formatters** (+ `PR_INFO_DIR`, `COMMIT_MESSAGE_FILE`).
3. **Move rebase** — depends on `push_changes` already living in `workflow_steps`.
4. **Move CI check/fix** (+ CI constants, `LLM_INACTIVITY_TIMEOUT_SECONDS`) with defaulted header/session-dir params.
5. **Extract shared `check_git_clean` prerequisite step.**
6. **Extract shared `is_branch_not_base` prerequisite step.**

Steps 2 → 3 → 4 are strictly ordered (rebase imports `push_changes`; CI imports
`commit_changes`/`push_changes`). Steps 5 and 6 are independent of each other.

## Definition of done (every step)

`run_lint_imports_check`, `run_tach_check`, and the pylint / pytest / mypy trio all
green before the commit. Existing behavior unchanged (return values, control flow,
commit-message-file read/unlink lifecycle, the two CI prompt headers, and the
`implement_sessions` dir preserved). The `finalisation.py:73` doubled-path quirk is
left as-is by design.
