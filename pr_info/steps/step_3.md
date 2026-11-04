# Step 3: review hand-off text

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`. Steps 1 and 2 are already committed. Write the tests first, then implement, run the checks listed in the summary, and produce exactly one commit. Implement only this step.

## WHERE

| File | Change |
|---|---|
| `tests/workflows/review/test_handoff_route.py` | Outcome builder, explicit lists |
| `src/mcp_coder/workflows/review/handoff.py` | `_REBASE_HANDOFF` |

## WHAT

No new functions. `_REBASE_HANDOFF` changes:

```python
"branch_moved": (
    "Branch moved",
    BRANCH_MOVED_REASON,
    BRANCH_MOVED_NEXT_STEP,
),
"push_failed": (
    "Rebase not pushed",
    "Rebase was not pushed",
    "Check the job log and `origin/<branch>`, update or discard the local "
    "checkout, then re-run",
),
```

The `push_failed` key stays. Its next step must fit both a reset checkout and one left on an unpushed rebase, and it must not mention `git push --force-with-lease`.

## HOW

```python
from mcp_coder.workflow_steps.rebase import (
    BRANCH_MOVED_NEXT_STEP,
    BRANCH_MOVED_REASON,
    RebaseOutcome,
)
```

`branch_moved` routes through the existing path: `_after_steps` returns `"rebase"` for any non-ok outcome, and `_route_to_human` applies `escalate_label_id` (`status-07`). No routing code changes.

## ALGORITHM

None. This step only changes a data table.

## DATA

`_REBASE_HANDOFF: dict[str, tuple[str, str, str]]` gains one key, and one existing value changes.

## Tests

In `tests/workflows/review/test_handoff_route.py`:

- **`_rebase_outcome`:** add a `branch_moved` branch returning `RebaseOutcome("branch_moved", "main", "def5678")`. Its fall-through returns `push_failed`, so a missed reason passes silently.
- **`test_rebase_handoff_reason_line`:** change the `push_failed` text to `"Rebase was not pushed"`, and add `("branch_moved", BRANCH_MOVED_REASON)`.
- **`test_rebase_handoff_does_not_suggest_rebase`:** add `"branch_moved"`.
- **`test_rebase_handoff_base_line`:** add `("branch_moved", "**Base:** origin/main @ def5678")`.
- **New test:** the `push_failed` comment does not contain `--force-with-lease`.

`test_rebase_handoff_fields_follow_the_table` and `test_rebase_handoff_files_field` are parametrized over `sorted(_REBASE_HANDOFF)`, so they pick up the new key without changes. The first already asserts `escalate_label_id`, which covers `branch_moved` routing to `status-07`.
