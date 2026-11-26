# Step 3 — Review regression guard: a clean round still pushes

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` exactly.
> Steps 1 and 2 are already committed. This step only changes a test. Run pylint,
> mypy and the fast pytest suite, all with `-n auto` and the non-integration markers
> from CLAUDE.md, then run the formatter. Make exactly one commit for this step. Do
> not edit `pr_info/TASK_TRACKER.md`.

## Precondition

`test_clean_tree_round_proceeds_normally` must exist in
`tests/workflows/review/test_core.py`. If it does not, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- `tests/workflows/review/test_core.py`: modify `test_clean_tree_round_proceeds_normally`.

## WHAT

There is no production change. Add one assertion after the existing ones:

```python
env.push_changes.assert_called()
```

Extend the docstring with the reason: the push must stay, because it carries the
previous round's log, which is flushed with `push=False`.

## HOW

The `env` fixture (`tests/workflows/review/conftest.py`) already mocks
`commit_changes`, which returns `True`, and `push_changes`. Nothing else is needed.

## ALGORITHM

None.

## DATA

None.

## Note

This test passes before and after the change, because `commit_changes` is mocked. It
guards against moving the clean-tree check into `review/core.py` or skipping the push.
If it fails, the production code is wrong, not the test.

## Commit message

`test(review): assert a clean round still pushes`
