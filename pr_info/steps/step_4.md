# Step 4 — Move validation tests to `test_task_tracker_validation.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md` exactly. This is a pure
> move-only refactoring: use `mcp__mcp-tools-py__move_symbol`, never move code by hand, and edit only
> import lines. Follow the summary's move procedure, checks and
> failure rule, then run the final verification below. Produce exactly one commit.

## WHERE

- Source: `tests/workflow_utils/test_task_tracker.py`
- Destination (new): `tests/workflow_utils/test_task_tracker_validation.py`

## WHAT

Move these top-level test classes verbatim in one call. No new functions or signatures.

| Call | `symbol_names` (source order) | Tests |
|---|---|---:|
| 4 | `["TestValidateTaskTracker", "TestTaskTrackerTemplate"]` | 6 + 3 |

The base file is already under the 750 limit and off `.large-files-allowlist` after step 3; this move
takes it from ~460 to ~285 lines.

## HOW

- `TestValidateTaskTracker.test_validate_default_folder_path` has a method-local `import os`. It must stay inside the method.
- Expected destination imports: `from pathlib import Path`; `from tempfile import TemporaryDirectory`;
  `import pytest`; `from mcp_coder.workflow_utils.task_tracker import (TASK_TRACKER_TEMPLATE,
  TaskTrackerFileNotFoundError, TaskTrackerSectionNotFoundError, validate_task_tracker)`.
- Expected final base-file imports: `from pathlib import Path`; `from tempfile import TemporaryDirectory`;
  `import pytest`; `from mcp_coder.workflow_utils.task_tracker import (TaskInfo, TaskTrackerError,
  TaskTrackerFileNotFoundError, TaskTrackerSectionNotFoundError, _find_implementation_section,
  _get_incomplete_tasks, _read_task_tracker, get_step_progress)`. The module docstring,
  `MULTI_PHASE_CONTENT` (with its 2-line comment) and `create_test_tracker_content` are unchanged.

## ALGORITHM

```
precondition: step 3 is committed and dest file does not exist, else write one line to pr_info/.blocked.txt and stop
record collect counts: tests/workflow_utils/ and whole suite
dry_run -> verify only 2 files listed -> real run -> inspect (import os local)
fix imports only if they differ from the expected end state
run_format_code; run the summary's per-step checks plus the final verification below
verify counts, then commit
```

## DATA (expected after this step)

Per-file `--collect-only -q` results:

| File | Collected |
|---|---:|
| `test_task_tracker.py` | 13 |
| `test_task_tracker_parsing.py` | 24 |
| `test_task_tracker_incomplete_tasks.py` | 18 |
| `test_task_tracker_status.py` | 19 |
| `test_task_tracker_validation.py` | 9 |

`tests/workflow_utils/` and whole-suite counts must be identical to the values recorded at the start of
the step (232 / 6587 on 2026-10-26 unless the branch was rebased).

## Final verification (all MCP)

- [ ] `run_format_code`, `run_ruff_check`, `run_pylint_check`, `run_mypy_check`
- [ ] Fast unit tests: `run_pytest_check(extra_args=["-n", "auto", "-m", "<FAST>"])`
- [ ] The five files directly: `run_pytest_check(extra_args=["-q", "-n", "auto", "-m", "<FAST>", "tests/workflow_utils/test_task_tracker.py", "tests/workflow_utils/test_task_tracker_parsing.py", "tests/workflow_utils/test_task_tracker_incomplete_tasks.py", "tests/workflow_utils/test_task_tracker_status.py", "tests/workflow_utils/test_task_tracker_validation.py"])` → **83 passed**
- [ ] `run_lint_imports_check`, `run_tach_check`, `run_vulture_check`
- [ ] `check_file_size` passes and reports no stale allowlist entries
- [ ] `search_files(pattern="test_task_tracker\\w*\\.(?!py\\b)\\w", glob="tests/**/*.py")` → 0 matches
- [ ] Compact diff of the whole branch against the base branch (`git` diff, `compact=true`). It may contain only:
  - the shortened import list in `test_task_tracker.py`
  - the headers and import blocks of the four new files
  - the 3 deleted banner lines
  - moved-block summaries and blank-line-only hunks
  - the one `.large-files-allowlist` removal

  Anything else → write one line to `pr_info/.blocked.txt` and stop.

## Tests

No new tests; this is pure refactoring. All 83 original tests pass across the five files (see above).

## Commit

`test(workflow_utils): move task tracker validation tests to own file (#1326)`
