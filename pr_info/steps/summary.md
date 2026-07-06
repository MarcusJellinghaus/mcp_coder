# Summary — Split `implement/core.py` + `test_core.py` (Issue #1025)

## Goal

Both files exceed the enforced **750-line** limit and are grandfathered in
`.large-files-allowlist`:

- `src/mcp_coder/workflows/implement/core.py` — 949 lines
- `tests/workflows/implement/test_core.py` — 2804 lines

"Done" = **both files under 750 lines AND removed from the allowlist**
(CI runs `check file-size --max-lines 750 --allowlist-file .large-files-allowlist`).

## Architectural / design changes

**None in behaviour — this is a pure-move refactor ("Move, Don't Change").**
Whole functions and classes are relocated verbatim. The *only* permitted edits are:

1. **Import statements** — in moved files, consumers, and `__init__.py`.
2. **`unittest.mock.patch()` target strings** — when a function moves from
   `core.py` to a new sibling module, the name is now looked up in the new
   module, so `patch("...implement.core.X")` becomes
   `patch("...implement.<new_module>.X")`. This is an import-path adjustment,
   not a logic change.
3. **A tiny test helper `_make_llm_response`** (8-line dict factory) is
   **duplicated** into each new test file that needs it. We deliberately avoid a
   shared `conftest` fixture: that would rewrite ~20 call sites and drift from
   the pure-move property. Duplicating keeps each moved test class byte-identical
   and keeps the compact-diff clean.

`run_implement_workflow` is **NOT** decomposed — extracting inline stages would
be a logic change and belongs in a separate PR.

### Why the source splits into 4 sibling modules

The binding constraint is the **test file**. Even after moving every
non-orchestrator test class out, the orchestrator's own tests total ~1370 lines
— over 750 — so they must span **two** test files. Each non-orchestrator test
group needs a clean parallel-named source module to mirror. Consolidating the
source would not reduce the (mandatory) test-file count; it would only muddy the
naming. So the 4-module source split is load-bearing, not gold-plating.

### Layering / import contracts

New modules are same-layer siblings inside `mcp_coder.workflows.implement`. There
is **no `implement` sub-layer** in `.importlinter`, so **no contract change is
needed**. `core.py` importing its new siblings is allowed. `prepare_task_tracker`
stays in-package (it imports from `.constants`/`.prerequisites`; moving it to
`workflow_utils` would violate the layered architecture).

### Module naming (collision avoidance)

- `failure_reporting.py` — NOT `failures.py` (`llm_failures.py` already exists).
- `task_tracker_prep.py` — NOT `task_tracker.py` (`workflow_utils/task_tracker.py`
  already exists).

### Package API stability

`implement/__init__.py` keeps `__all__` unchanged. `move_symbol` repoints the
`log_progress_summary` / `prepare_task_tracker` re-exports to `task_tracker_prep`
automatically and updates the only external consumer
(`cli/commands/implement.py` imports `run_implement_workflow`, which stays put).

### Correctness cleanup (bundled)

`TestResolveProjectDir` currently lives in `test_core.py` but tests
`resolve_project_dir` from `mcp_coder.workflows.utils`. It is misplaced; it moves
to a new mirror `tests/workflows/test_utils.py`. This is a free correctness fix
that also trims the orchestrator test mass.

## Target layout

### Source (`src/mcp_coder/workflows/implement/`)

| File | Holds | ~lines |
|------|-------|--------|
| `core.py` (keep) | `run_implement_workflow` | ~500 |
| `failure_reporting.py` (new) | `_format_failure_comment`, `_handle_workflow_failure` | ~90 |
| `rebase.py` (new) | `_get_rebase_target_branch`, `_attempt_rebase_and_push` | ~60 |
| `task_tracker_prep.py` (new) | `prepare_task_tracker`, `log_progress_summary` | ~225 |
| `finalisation.py` (new) | `run_finalisation` | ~155 |

### Tests (`tests/workflows/`)

| File | Holds | ~lines |
|------|-------|--------|
| `implement/test_failure_reporting.py` (new) | `TestFormatFailureComment`, `TestHandleWorkflowFailure`, `TestFormatFailureCommentElapsedAndBuildUrl`, `TestExistingFailuresIncludeNewFields` | ~370 |
| `implement/test_rebase.py` (new) | `TestGetRebaseTargetBranch`, `TestRebaseIntegration` | ~192 |
| `implement/test_task_tracker_prep.py` (new) | `TestPrepareTaskTracker`, `TestPrepareTaskTrackerExecutionDir`, `TestLogProgressSummary` | ~483 |
| `implement/test_finalisation.py` (new) | `TestRunFinalisation` | ~350 |
| `implement/test_core.py` (keep) | `TestRunImplementWorkflow` | ~700 |
| `implement/test_core_workflow.py` (new) | `TestRunImplementWorkflowLabelTransitions`, `TestNoPostErrorProgressDisplay`, `TestWorkflowSafetyNet`, `TestSigtermHandler`, `TestIntegration` | ~717 |
| `test_utils.py` (new) | `TestResolveProjectDir` | ~70 |

## Files created / modified / removed

**Created (source):**
- `src/mcp_coder/workflows/implement/failure_reporting.py`
- `src/mcp_coder/workflows/implement/rebase.py`
- `src/mcp_coder/workflows/implement/task_tracker_prep.py`
- `src/mcp_coder/workflows/implement/finalisation.py`

**Created (tests):**
- `tests/workflows/implement/test_failure_reporting.py`
- `tests/workflows/implement/test_rebase.py`
- `tests/workflows/implement/test_task_tracker_prep.py`
- `tests/workflows/implement/test_finalisation.py`
- `tests/workflows/implement/test_core_workflow.py`
- `tests/workflows/test_utils.py`

**Modified:**
- `src/mcp_coder/workflows/implement/core.py` (functions removed; unused imports cleaned)
- `src/mcp_coder/workflows/implement/__init__.py` (re-exports repointed; `__all__` unchanged)
- `tests/workflows/implement/test_core.py` (classes removed; unused imports cleaned)
- `.large-files-allowlist` (remove the two entries)

**No new folders.** No `__init__.py` additions (all target test dirs already exist).

## `_make_llm_response` helper — which files get a copy

Used by orchestrator, task-tracker, finalisation, and integration tests. Duplicate
the 8-line helper into: `test_task_tracker_prep.py`, `test_finalisation.py`,
`test_core.py` (keep existing), `test_core_workflow.py`. NOT needed in
`test_failure_reporting.py`, `test_rebase.py`, `test_utils.py`.

## Commit / step plan (one PR, 6 commits — one commit per step)

1. Move `failure_reporting` group (src + tests).
2. Move `rebase` group (src + tests).
3. Move `task_tracker_prep` group (src + tests) — auto-repoints `__init__.py`.
4. Move `finalisation` group (src + tests) — after this `core.py` < 750.
5. Redistribute orchestrator tests into `test_core_workflow.py`; move
   `TestResolveProjectDir` to `tests/workflows/test_utils.py` — after this
   `test_core.py` < 750.
6. Verify `__init__.py`/`__all__` stable; remove both `.large-files-allowlist`
   entries; final full verification (compact-diff purity + file-size).

## Per-step definition of done

Every step is exactly one commit with all checks green:

- `run_format_code` (isort + black)
- `run_ruff_fix` then `run_ruff_check` (removes now-unused imports — allowed)
- `run_lint_imports_check`
- `run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])`
- `run_pylint_check`
- `run_mypy_check`
- `check_file_size` (max 750) where relevant

Purity gate (whole PR): `mcp-coder git-tool compact-diff` shows **only** import
changes, `patch()` target-path changes, the duplicated helper, and new/deleted
file headers — no logic changes.
