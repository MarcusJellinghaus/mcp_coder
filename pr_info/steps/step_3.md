# Step 3 — Move status tests to `test_task_tracker_status.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` exactly. This is a pure
> move-only refactoring: use `mcp__mcp-tools-py__move_symbol`, never move code by hand, and edit only
> import lines plus the one banner deletion and the `.large-files-allowlist` entry described here. Follow the summary's move procedure, checks
> and failure rule. Produce exactly one commit.

## WHERE

- Source: `tests/workflow_utils/test_task_tracker.py`
- Destination (new): `tests/workflow_utils/test_task_tracker_status.py`
- `.large-files-allowlist`: remove the line `tests/workflow_utils/test_task_tracker.py`

## WHAT

Move these top-level test classes verbatim in one call. No new functions or signatures.

| Call | `symbol_names` (source order) | Tests |
|---|---|---:|
| 3 | `["TestGetStepProgress", "TestIsTaskDone", "TestGetTaskCounts"]` | 4 + 10 + 5 |

Then delete the now-empty three-line banner from the base file (the only allowed non-import code edit):

```
# ============================================================================
# get_task_counts() tests
# ============================================================================
```

## HOW

- `TestGetTaskCounts` calls `create_test_tracker_content`. The destination must get
  `from tests.workflow_utils.test_task_tracker import create_test_tracker_content`, and the helper must not move.
- `TestIsTaskDone.test_is_task_done_default_folder` has a method-local `import os`. It must stay inside the method.
- The banner must still be in the base file after the move (it is separated from the class by blank
  lines). If it went to the destination, move `TestGetTaskCounts` back with `move_symbol`, then write
  one line to `pr_info/.blocked.txt` and stop.
- Delete only the three comment lines. `run_format_code` trims the leftover blank lines.
- Expected destination imports: `from pathlib import Path`; `from tempfile import TemporaryDirectory`;
  `import pytest`; `from mcp_coder.workflow_utils.task_tracker import (TaskTrackerFileNotFoundError,
  TaskTrackerSectionNotFoundError, get_step_progress, get_task_counts, has_incomplete_work, is_task_done)`;
  `from tests.workflow_utils.test_task_tracker import create_test_tracker_content`.
- The base file still needs `get_step_progress` (`TestMultiPhaseTaskTracker`). ruff F401 is the judge.
- After this move the base file is ~460 lines, under the 750 limit, so its allowlist entry would be stale.
  Remove the line `tests/workflow_utils/test_task_tracker.py` from `.large-files-allowlist` by matching
  its path with `edit_file`. Change nothing else in that file.

## ALGORITHM

```
precondition: step 2 is committed and dest file does not exist, else write one line to pr_info/.blocked.txt and stop
record collect counts: tests/workflow_utils/ and whole suite
dry_run -> verify only 2 files listed -> real run -> inspect (helper, banner stay; import os local)
delete the 3 banner lines in the base file; remove the allowlist line
fix imports only if they differ from the expected end state (run_ruff_fix F401 for leftovers)
run_format_code; run the summary's per-step checks; verify counts, then commit
```

## DATA (expected after this step)

- `--collect-only -q tests/workflow_utils/test_task_tracker_status.py` → **19**
- `--collect-only -q tests/workflow_utils/test_task_tracker.py` → **22**
- `tests/workflow_utils/` and whole-suite counts: identical to the values recorded at the start of the step
- `search_files(pattern="get_task_counts\\(\\) tests", glob="tests/workflow_utils/*.py")` → 0 matches
- `tests/workflow_utils/test_task_tracker.py` is off `.large-files-allowlist` (~460 lines);
  `check_file_size` passes and reports no stale allowlist entries.

## Tests

No new tests; this is pure refactoring. The 19 moved tests must pass in their new file:
`run_pytest_check(extra_args=["-q", "-n", "auto", "-m", "<FAST>", "tests/workflow_utils/test_task_tracker.py", "tests/workflow_utils/test_task_tracker_parsing.py", "tests/workflow_utils/test_task_tracker_incomplete_tasks.py", "tests/workflow_utils/test_task_tracker_status.py"])` → **83 passed**.

## Commit

`test(workflow_utils): move task tracker status tests to own file (#1326)`
