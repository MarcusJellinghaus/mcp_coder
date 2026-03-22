# Step 11: tests/ W0718 — broad-exception-caught inline-disables (31 occurrences)

## Goal
Add inline pylint disables for all `except Exception` clauses in test files.

## WHERE — Files Modified

Key files: `tests/utils/github_operations/test_base_manager.py` and scattered others.
Run `pylint tests/ --disable=all --enable=W0718` to get exact list after steps 9-10.

## WHAT

```python
except Exception:  # pylint: disable=broad-exception-caught  # test helper — broad catch intentional
```

## DATA

Pylint count reduced by: **31 warnings**.

---

## LLM Prompt

```
Please implement Step 11: fix W0718 (broad-exception-caught) in tests/.
See pr_info/steps/step_11.md.
Rules: add inline disable comment to each `except Exception` line.
No code changes. Run pylint, pytest (fast unit tests), and mypy to verify.
```
