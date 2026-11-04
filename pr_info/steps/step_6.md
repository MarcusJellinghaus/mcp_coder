# Step 6: auto-merge next step

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_6.md`. Steps 1 to 5 are already committed. Write the tests first, then implement, run the checks listed in the summary, and produce exactly one commit. Implement only this step.

## WHERE

| File | Change |
|---|---|
| `tests/workflow_steps/test_merge.py` | New tests in the rebase-failure test class, next to `test_other_rebase_failure_no_reset` |
| `src/mcp_coder/workflow_steps/merge.py` | `_failed` |

## WHAT

No new functions. `_failed(result, state, rebase)` adds a `Next step` field when `rebase.reason == "branch_moved"`.

## HOW

Extend the existing import from `workflow_steps.rebase` with `BRANCH_MOVED_NEXT_STEP`. Keep the existing fields and `Stage` "Auto-merge" as they are. The reason stays the raw `rebase.reason`.

## ALGORITHM

Inside the existing `if rebase is not None:` block:

```text
fields += [("Reason", rebase.reason), ("Base", rebase.base_branch)]
if rebase.reason == "branch_moved":
    fields.append(("Next step", BRANCH_MOVED_NEXT_STEP))
```

## DATA

`MergeOutcome("merge_failed", fields)`. `build_failure_comment` already sorts `Next step` through `FIELD_ORDER`.

## Tests

In `tests/workflow_steps/test_merge.py`, with `mocks.pr_manager.merge_pull_request.return_value = REFUSED_405`:

| `mocks.rebase.return_value` | Expected |
|---|---|
| `RebaseOutcome("branch_moved", "main", "1234567")` | `label_id == "merge_failed"`; `Reason` is `branch_moved`; `Next step` is `BRANCH_MOVED_NEXT_STEP`; `reset_hard` not called; one merge attempt |
| `RebaseOutcome("push_failed", "main", "1234567")` | No `Next step` key |
