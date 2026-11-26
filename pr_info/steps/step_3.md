# Step 3: blank lines in `TASK_TRACKER_TEMPLATE`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`.
> Write the test first, then the change. Run pylint, mypy and the fast pytest
> set (`-n auto`). Format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflow_utils/task_tracker.py`: `TASK_TRACKER_TEMPLATE`
- `tests/workflow_utils/test_task_tracker_template.py` (new)

## WHAT

Insert one empty line directly after `**How to update tasks:**` and after
`**Task format:**`, so each bold label line is followed by a blank line before
its list. Nothing else in the template changes.

## HOW

Plain string edit. `classify_tracker_content`, `CHECKBOX_PATTERN` and the
prep code read the template; their tests must keep passing. Do not edit
`pr_info/TASK_TRACKER.md` or the fixtures under `tests/workflow_utils/test_data/`.

## ALGORITHM

```
lines = TASK_TRACKER_TEMPLATE.splitlines()
for i, line in enumerate(lines):
    if line.startswith("**") and line.endswith(":**"): assert lines[i + 1] == ""
```

## DATA

None (string constant).

## Tests first

`test_task_tracker_template.py`:

- Every line of `TASK_TRACKER_TEMPLATE` that starts with `**` and ends with
  `:**` is followed by an empty line (both labels exist; assert the count is 2).
- `classify_tracker_content(TASK_TRACKER_TEMPLATE)` still returns
  `TrackerState.EMPTY`.

## Commit

`fix(tracker): add blank lines after the template's bold labels`
