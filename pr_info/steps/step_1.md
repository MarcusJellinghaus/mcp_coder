# Step 1 — Move parsing tests to `test_task_tracker_parsing.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly. This is a pure
> move-only refactoring: use `mcp__mcp-tools-py__move_symbol`, never move code by hand, and edit only
> import lines. Follow the summary's move procedure, checks and failure rule. Produce exactly one commit.

## WHERE

- Source: `tests/workflow_utils/test_task_tracker.py`
- Destination (new): `tests/workflow_utils/test_task_tracker_parsing.py`

## WHAT

Move these top-level test classes verbatim. No new functions or signatures.

| Call | `symbol_names` (source order) | Tests |
|---|---|---:|
| 1a | `["TestFindImplementationSection", "TestParseTaskLines"]` | 6 + 12 |
| 1b | `["TestNormalizeTaskName"]` | 6 |

## HOW

- `TestParseTaskLines` calls `create_test_tracker_content`, which stays in the base file. So the destination
  must get `from tests.workflow_utils.test_task_tracker import create_test_tracker_content`, and the helper
  must not move.
- Expected destination imports: `from pathlib import Path`; `from tempfile import TemporaryDirectory`;
  `import pytest`; `from mcp_coder.workflow_utils.task_tracker import (TaskTrackerSectionNotFoundError,
  _find_implementation_section, _normalize_task_name, _parse_task_lines, get_incomplete_tasks)`;
  `from tests.workflow_utils.test_task_tracker import create_test_tracker_content`.
- The base file keeps every other import that is still used (`get_incomplete_tasks` is still used by
  `TestGetIncompleteTasks*` at this point). ruff F401 is the judge.

## ALGORITHM

```
precondition: dest file does not exist, else write one line to pr_info/.blocked.txt and stop
record collect counts: tests/workflow_utils/ and whole suite
for call in [1a, 1b]: dry_run -> verify only 2 files listed -> real run -> inspect
fix imports only if they differ from the expected end state (run_ruff_fix F401 for leftovers)
run_format_code; run the summary's per-step checks
verify counts (below), then commit
```

## DATA (expected after this step)

- `--collect-only -q tests/workflow_utils/test_task_tracker_parsing.py` → **24**
- `--collect-only -q tests/workflow_utils/test_task_tracker.py` → **59**
- `tests/workflow_utils/` and whole-suite counts: identical to the values recorded at the start of the step
- `tests/workflow_utils/test_task_tracker.py` stays on `.large-files-allowlist` (still > 750 lines)

## Tests

No new tests; this is pure refactoring. The 24 moved tests are the safety net. Before the move they
pass in the base file, and after it they must pass in the new file:
`run_pytest_check(extra_args=["-q", "-n", "auto", "-m", "<FAST>", "tests/workflow_utils/test_task_tracker.py", "tests/workflow_utils/test_task_tracker_parsing.py"])` → **83 passed**.

## Commit

`test(workflow_utils): move task tracker parsing tests to own file (#1326)`
