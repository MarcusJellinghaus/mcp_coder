# Step 2 — Move incomplete-task tests to `test_task_tracker_incomplete_tasks.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly. This is a pure
> move-only refactoring: use `mcp__mcp-tools-py__move_symbol`, never move code by hand, and edit only
> import lines. Follow the summary's move procedure, checks and failure rule. Produce exactly one commit.

## WHERE

- Source: `tests/workflow_utils/test_task_tracker.py`
- Destination (new): `tests/workflow_utils/test_task_tracker_incomplete_tasks.py`

## WHAT

Move these top-level test classes verbatim. No new functions or signatures.

| Call | `symbol_names` (source order) | Tests |
|---|---|---:|
| 2a | `["TestGetIncompleteTasksInternal", "TestGetIncompleteTasks", "TestHasIncompleteWork"]` | 6 + 8 + 3 |
| 2b | `["TestGetIncompleteTasksEdgeCases"]` | 1 |

## HOW

- `TestGetIncompleteTasks.test_get_incomplete_tasks_default_folder` has a method-local `import os`. It must
  stay inside the method, and no module-level `import os` may appear.
- 2b's class may land above the others in the destination. Leave it there; order doesn't matter.
- Expected destination imports: `from pathlib import Path`; `from tempfile import TemporaryDirectory`;
  `import pytest`; `from mcp_coder.workflow_utils.task_tracker import (TaskTrackerFileNotFoundError,
  TaskTrackerSectionNotFoundError, _get_incomplete_tasks, get_incomplete_tasks, has_incomplete_work)`.
  No import from `tests.workflow_utils.test_task_tracker`.
- The base file still needs `has_incomplete_work` (`TestGetStepProgress`) and `_get_incomplete_tasks`
  (`TestMultiPhaseTaskTracker`). ruff F401 is the judge.

## ALGORITHM

```
precondition: step 1 is committed and dest file does not exist, else write one line to pr_info/.blocked.txt and stop
record collect counts: tests/workflow_utils/ and whole suite
for call in [2a, 2b]: dry_run -> verify only 2 files listed -> real run -> inspect (import os stays local)
fix imports only if they differ from the expected end state (run_ruff_fix F401 for leftovers)
run_format_code; run the summary's per-step checks
verify counts (below), then commit
```

## DATA (expected after this step)

- `--collect-only -q tests/workflow_utils/test_task_tracker_incomplete_tasks.py` → **18**
- `--collect-only -q tests/workflow_utils/test_task_tracker.py` → **41**
- `tests/workflow_utils/` and whole-suite counts: identical to the values recorded at the start of the step
- The base file stays on `.large-files-allowlist`.

## Tests

No new tests; this is pure refactoring. The 18 moved tests must pass in their new file:
`run_pytest_check(extra_args=["-q", "-n", "auto", "-m", "<FAST>", "tests/workflow_utils/test_task_tracker.py", "tests/workflow_utils/test_task_tracker_parsing.py", "tests/workflow_utils/test_task_tracker_incomplete_tasks.py"])` → **83 passed**.

## Commit

`test(workflow_utils): move task tracker incomplete-task tests to own file (#1326)`
