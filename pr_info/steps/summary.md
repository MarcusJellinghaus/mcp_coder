# Summary — Split `tests/workflow_utils/test_task_tracker.py` (#1326)

Part of #353. Process: `docs/processes-prompts/refactoring-guide.md`.

## Goal

`tests/workflow_utils/test_task_tracker.py` (1729 lines, allowlisted) is split into the base file plus four
prefixed siblings, one per function family of `src/mcp_coder/workflow_utils/task_tracker.py`. Every file
ends up under 600 lines and the file comes off `.large-files-allowlist`.

**Pure refactoring, so no code changes.** Classes move verbatim with `mcp__mcp-tools-py__move_symbol`. The only
allowed hand edits: import lines, deleting the one section banner left empty by the move, and the
`.large-files-allowlist` entry. The full rules are in issue #1326's rules box.

## Architectural / design changes

- **Source: none.** `src/mcp_coder/workflow_utils/task_tracker.py` (537 lines) is cohesive and under the
  limit, so this is a test-only split.
- **Test layout:** the module is a single file, so its tests become a namespace of prefixed sibling files
  (`test_task_tracker_<concern>.py`) in the same directory. The `conftest.py` chain is unchanged (only
  `tests/conftest.py`).
- **Shared helper:** `create_test_tracker_content` and `MULTI_PHASE_CONTENT` never move. `_parsing` and
  `_status` import the helper from `tests.workflow_utils.test_task_tracker`. Siblings never import a
  `Test*` class (pytest would collect it twice).
- No change to `.importlinter`, `tach.toml`, `vulture_whitelist.py`, docs or any other test file.

## Target layout

| File | Classes | Tests | ~lines |
|---|---|---:|---:|
| `test_task_tracker.py` (keep) | `MULTI_PHASE_CONTENT`, `create_test_tracker_content`, `TestTaskInfo`, `TestExceptions`, `TestReadTaskTracker`, `TestCreateTestTrackerContent`, `TestMultiPhaseTaskTracker` | 13 | ~285 |
| `test_task_tracker_parsing.py` (new) | `TestFindImplementationSection`, `TestParseTaskLines`, `TestNormalizeTaskName` | 24 | ~475 |
| `test_task_tracker_incomplete_tasks.py` (new) | `TestGetIncompleteTasksInternal`, `TestGetIncompleteTasks`, `TestHasIncompleteWork`, `TestGetIncompleteTasksEdgeCases` | 18 | ~410 |
| `test_task_tracker_status.py` (new) | `TestGetStepProgress`, `TestIsTaskDone`, `TestGetTaskCounts` | 19 | ~435 |
| `test_task_tracker_validation.py` (new) | `TestValidateTaskTracker`, `TestTaskTrackerTemplate` | 9 | ~180 |

Total: 83 tests, the same as today.

## Files created / modified

| Path | Change | Step |
|---|---|---|
| `tests/workflow_utils/test_task_tracker.py` | modified (classes moved out, imports shrink, banner deleted) | 1–4 |
| `tests/workflow_utils/test_task_tracker_parsing.py` | created | 1 |
| `tests/workflow_utils/test_task_tracker_incomplete_tasks.py` | created | 2 |
| `tests/workflow_utils/test_task_tracker_status.py` | created | 3 |
| `tests/workflow_utils/test_task_tracker_validation.py` | created | 4 |
| `.large-files-allowlist` | modified (remove `tests/workflow_utils/test_task_tracker.py`) | 4 |

No new folders, no `__init__.py` or `conftest.py` changes (`tests/workflow_utils/__init__.py` exists).

## Baseline (measured 2026-10-26 on this branch)

- `tests/workflow_utils/test_task_tracker.py`: 83 collected, 83 passed with the fast-unit exclusion
- `tests/workflow_utils/`: 232 collected (the issue says 225, but the suite has grown since it was written)
- whole suite: 6587 collected (the issue says 6463)

Counts outside the task-tracker files may change if the branch is rebased. So each step compares
counts **before vs after its own move** instead of against fixed totals. The only fixed totals are the
per-file test counts in the table above.

## Shared conventions for every step

**Fast-unit exclusion** (`<FAST>` below):
`not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration`

**Move procedure** (each `move_symbol` call):
1. `move_symbol(source_file="tests/workflow_utils/test_task_tracker.py", symbol_names=[...], dest_file=<dest>, dry_run=true)`.
   It must list only `tests/workflow_utils/test_task_tracker.py` and `<dest>`.
2. Run the same call with `dry_run=false`.
3. Read `<dest>` and the base file:
   - test bodies are unchanged
   - each method-local `import os` is still inside its method
   - `create_test_tracker_content` and `MULTI_PHASE_CONTENT` are still in the base file

**Imports:** `move_symbol` adds the imports each destination needs and removes the ones the source
no longer uses. Edit imports by hand only if the result differs from the expected end state in the
step. Leftover unused imports → `run_ruff_fix(select=["F401"])`. Import order is the formatter's job.

**Per-step checks (all MCP):** `run_format_code`, `run_ruff_check`, `run_pylint_check`, `run_mypy_check`,
fast unit tests (`run_pytest_check(extra_args=["-n", "auto", "-m", "<FAST>"])`), `check_file_size`.

**Count invariant:** before the first move of the step, record `--collect-only -q` counts for
`tests/workflow_utils/` and for the whole suite. After the step, both must be identical.

**Failure rule:** if any precondition or check in a step fails in a way the step doesn't allow for,
write one line to `pr_info/.blocked.txt` and stop. Never hand-edit code to recover. Specific cases:
- a dry run or real call touches another file
- a call times out
- `Token <…> cannot be matched`
- a test body changes
- an `import os` is hoisted
- the helper, the constant or the banner moves
- `NameError` / `ImportError` at collection
- a count mismatch
- a failing test

**Commit:** one commit per step, after `run_format_code`. The message is given in each step.
