# Step 13: tests/ W1404 + W0201 — string concat + attribute-outside-init (6 total)

## Goal
Fix implicit string concatenation and attribute-defined-outside-init in tests/.

## WHERE — Files Modified

**W1404 — Implicit string concatenation (4 total):**
Merge adjacent string literals into one or add explicit `+`.

**W0201 — Attribute defined outside init (2 total):**
Move `self.attr = ...` assignments from test methods into `setUp` or `__init__`.

## DATA

Pylint count reduced by: **6 warnings**.

---

## LLM Prompt

```
Please implement Step 13: fix W1404 and W0201 in tests/.
See pr_info/steps/step_13.md.
Rules: merge string literals, move attribute assignments to setUp.
No test logic changes. Run pylint, pytest (fast unit tests), and mypy to verify.
```
