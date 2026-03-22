# Step 10: tests/ W1514 — unspecified encoding (23 occurrences)

## Goal
Add `encoding="utf-8"` to all `open()` calls in test files that lack an encoding argument.

## WHERE — Files Modified

Every `open(path, "r")` or `open(path, "w")` call in test files needs `encoding="utf-8"`:
```python
# Before
with open(tmp_file, "r") as f:
# After
with open(tmp_file, "r", encoding="utf-8") as f:
```

Run `pylint tests/ --disable=all --enable=W1514` to get exact list of files/lines.
Expected files include test files under `tests/workflows/`, `tests/utils/`, `tests/formatters/`.

If a test deliberately tests platform-default encoding, keep as-is and add inline disable instead.

## DATA

Pylint count reduced by: **23 warnings**.

---

## LLM Prompt

```
Please implement Step 10: fix W1514 (unspecified-encoding) in tests/.
See pr_info/steps/step_10.md.
Rules: add encoding="utf-8" to every open() call missing it. No test logic changes.
Run pylint, pytest (fast unit tests), and mypy to verify.
```
