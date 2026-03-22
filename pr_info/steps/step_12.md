# Step 12: tests/ W0107 + W0108 + W0702 + W0719 — small mechanical fixes (10 total)

## Goal
Fix four small warning types in tests/ with straightforward mechanical changes.

## WHERE — Files Modified

**W0107 — Unnecessary pass (3 total):**
Remove `pass` from blocks that have other statements.

**W0108 — Unnecessary lambda (4 total):**
Replace `lambda x: some_func(x)` with `some_func`.

**W0702 — Bare except (2 total):**
Replace `except:` with `except Exception:  # pylint: disable=broad-exception-caught  # test helper`.

**W0719 — Broad exception raised (1 total):**
Replace `raise Exception("test error")` with `raise RuntimeError("test error")`.

## DATA

Pylint count reduced by: **10 warnings**.

---

## LLM Prompt

```
Please implement Step 12: fix W0107, W0108, W0702, W0719 in tests/.
See pr_info/steps/step_12.md.
Rules: remove unnecessary pass, replace unnecessary lambdas, fix bare excepts,
change raise Exception to raise RuntimeError. No test logic changes.
Run pylint, pytest (fast unit tests), and mypy to verify.
```
