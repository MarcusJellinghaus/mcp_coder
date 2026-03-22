# Step 5: src/ W0706 + W4903 — try-except-raise + deprecated arg (4 occurrences)

## Goal
Add inline pylint disables for intentional try-except-raise patterns and deprecated `onerror=` argument.
Both are inline-disable fixes — no code logic changes.

## WHERE — Files Modified

**W0706 — try-except-raise inline-disable (2 total):**
- `src/mcp_coder/utils/subprocess_runner.py` line 355:
  ```python
  raise  # pylint: disable=try-except-raise  # intentional re-raise for subprocess isolation
  ```
- `src/mcp_coder/utils/subprocess_runner.py` line 506: same pattern

**W4903 — deprecated `onerror=` inline-disable (2 total):**

NOTE: Do NOT replace `onerror=` with `onexc=` — `onexc` was added in Python 3.12 and the project's minimum version is Python 3.11. Use inline disable instead.

- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` line 238:
  ```python
  shutil.rmtree(folder_path, onerror=_remove_readonly)  # pylint: disable=deprecated-argument  # onexc requires Python 3.12+
  ```
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` line 215:
  ```python
  shutil.rmtree(..., onerror=_remove_readonly)  # pylint: disable=deprecated-argument  # onexc requires Python 3.12+
  ```

## WHAT

All changes are inline pylint disable comments — no code logic changes.

## DATA

Pylint count reduced by: **4 warnings** (2 W0706 + 2 W4903).

## TDD Note

Run existing tests after changes to confirm nothing broken.

---

## LLM Prompt

```
Please implement Step 5: fix W0706 (try-except-raise) and W4903 (deprecated-argument) in src/.
See pr_info/steps/step_5.md for exact locations.
IMPORTANT: Do NOT replace onerror= with onexc= — use inline pylint disable instead
(onexc requires Python 3.12+, project minimum is 3.11).
Rules: add inline disable comments only. No code changes.
Run pylint, pytest (fast unit tests), and mypy to verify.
```
