# Step 2: Add the `checks_exhausted` failure reason

`implement_final` will fail with this reason when the fix loop reaches its cap (step 3). It reuses the existing `implementing_failed` label; no new GitHub label.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement step 2 only: write the tests first, then add the `checks_exhausted` reason to `failure_reporting.py`. Run pylint, mypy and the fast pytest suite; all must pass. Format, then make one commit.

## WHERE
- `src/mcp_coder/workflows/implement/failure_reporting.py`
- `tests/workflows/implement/test_failure_reporting.py`

## WHAT
```python
FAILURE_LABELS["checks_exhausted"] = "implementing_failed"   # entry in the dict literal
CATEGORY_DISPLAY["checks_exhausted"] = "Checks Exhausted"     # entry in the dict literal
```
Add a short comment above the `FAILURE_LABELS` entry: the fix loop hit its cap; shares the general label so the label set and coordinator stay unchanged.

## HOW
Dict entries only. `_fail` and `_comment_parts` already look reasons up in these dicts.

## ALGORITHM
None.

## DATA
- `FAILURE_LABELS["checks_exhausted"] == "implementing_failed"`
- `CATEGORY_DISPLAY["checks_exhausted"] == "Checks Exhausted"`

## Tests (write first)
In `test_failure_reporting.py`:
- `FAILURE_LABELS["checks_exhausted"] == "implementing_failed"`.
- `_comment_parts("checks_exhausted", tmp_path)` yields the Category `"Checks Exhausted"`.
- If the file has a test asserting that `FAILURE_LABELS` and `CATEGORY_DISPLAY` have the same keys, it must still pass.
