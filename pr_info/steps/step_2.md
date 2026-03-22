# Step 2: Fix `src/` mechanical fixes — W0707, W0719, W4903, W0706

## Goal
Apply four small, well-defined mechanical fixes to `src/` that correct genuine code
quality issues with zero ambiguity. Each fix is a targeted one-liner change.

## WHERE — Files Modified

**W0707 — Add `from e` to 7 raise statements:**
- `src/mcp_coder/prompt_manager.py`
  - line 582: `raise FileNotFoundError(...)` → `raise FileNotFoundError(...) from e`
  - line 600: `raise FileNotFoundError(...)` → `raise FileNotFoundError(...) from e`
  - line 612: `except FileNotFoundError:` → `except FileNotFoundError as exc:` + `raise ... from exc`
  - line 614: `raise FileNotFoundError(...)` → `raise FileNotFoundError(...) from e`
- `src/mcp_coder/cli/parsers.py`
  - line 481: `except ValueError:` → `except ValueError as exc:` + `raise argparse.ArgumentTypeError(...) from exc`
- `src/mcp_coder/utils/timezone_utils.py`
  - line 66: `raise ValueError(...)` → `raise ValueError(...) from e`
- `src/mcp_coder/workflows/implement/task_processing.py`
  - line 217: `raise Exception(...)` → `raise RuntimeError(...) from e`  ← also fixes W0719

**W0719 — Replace broad exception raised (1 total):**
- `src/mcp_coder/workflows/implement/task_processing.py` line 217 — handled above
  (`raise Exception(...)` → `raise RuntimeError(...)` — covered in W0707 fix above)

**W4903 — Replace deprecated `onerror=` with `onexc=` (2 total):**
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` line 238:
  `shutil.rmtree(folder_path, onerror=_remove_readonly)`
  → `shutil.rmtree(folder_path, onexc=_remove_readonly)`
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` line 215:
  `shutil.rmtree(..., onerror=_remove_readonly)`
  → `shutil.rmtree(..., onexc=_remove_readonly)`

**W0706 — Add inline disable for intentional try-except-raise (2 total):**
- `src/mcp_coder/utils/subprocess_runner.py` line 355:
  ```python
  except ...:
      raise  # pylint: disable=try-except-raise  # intentional re-raise for subprocess isolation
  ```
- `src/mcp_coder/utils/subprocess_runner.py` line 506:
  Same pattern.

## WHAT

No new functions. All changes are single-line edits:

**W0707 pattern:**
```python
# Before
except SomeError:
    raise NewError("message")

# After
except SomeError as exc:
    raise NewError("message") from exc
```

**W4903 pattern:**
```python
# Before
shutil.rmtree(path, onerror=handler)

# After (Python 3.12+ compatible)
shutil.rmtree(path, onexc=handler)
```

Note: `onexc=` receives `(func, path, excinfo)` instead of `(func, path, exc_info_tuple)`.
Check the existing `_remove_readonly` handler signature — it currently takes `(func, path, exc)`.
Update the handler signature if needed:
```python
# In workspace.py / session_launch.py
def _remove_readonly(func, path, _exc):  # onexc passes the exception object directly
    ...
```

**W0706 pattern:**
```python
except ...:
    raise  # pylint: disable=try-except-raise  # intentional re-raise for subprocess isolation
```

## HOW

- `from e` / `from exc` — standard Python exception chaining; no behaviour change for callers
- `onexc=` — Python 3.12 deprecation of `onerror=`; functionally equivalent on Python 3.11
  (both are supported in 3.11, `onerror` just emits a deprecation warning)
- Inline disable comments — no code effect

## ALGORITHM

```
For each W0707 location:
    Find the except clause, rename bare variable if needed (e → exc where already used)
    Append "from <exception_var>" to the raise statement on the next line

For W0719 (combined with W0707 in task_processing.py):
    Change raise Exception(...) to raise RuntimeError(...)
    Append from e

For each W4903 location:
    Replace onerror= with onexc= in the shutil.rmtree call
    Verify _remove_readonly signature is compatible with onexc callback

For each W0706 location in subprocess_runner.py:
    Add  # pylint: disable=try-except-raise  # intentional re-raise
    to the bare `raise` line
```

## DATA

No return value changes. No type signature changes.
Pylint count reduced by: 7 + 1 + 2 + 2 = **12 warnings**.

## TDD Note

No new tests needed — these are exception-chaining and API-compatibility fixes.
Existing tests for `prompt_manager`, `subprocess_runner`, `timezone_utils`,
`task_processing`, and `session_launch` cover the affected code paths.
Verify existing tests still pass after changes.

---

## LLM Prompt

```
Please implement Step 2 of the pylint warning cleanup described in
`pr_info/steps/summary.md` and `pr_info/steps/step_2.md`.

This step fixes W0707 (raise-missing-from), W0719 (broad-exception-raised),
W4903 (deprecated onerror= argument), and W0706 (try-except-raise) in `src/`.

Rules:
- W0707: Add `from e` (or `from exc`) to each raise inside an except block.
  If the except clause has no variable, add one: `except Err as exc:`.
- W0719: Change `raise Exception(...)` to `raise RuntimeError(...)`.
  The one occurrence is in task_processing.py and is also a W0707 — fix both together.
- W4903: Replace `shutil.rmtree(path, onerror=handler)` with
  `shutil.rmtree(path, onexc=handler)` in session_launch.py and workspace.py.
  Verify the _remove_readonly handler signature is compatible.
- W0706: Add inline disable comment to the two bare `raise` statements in
  subprocess_runner.py that immediately re-raise the caught exception.
  Comment: `# pylint: disable=try-except-raise  # intentional re-raise for subprocess isolation`
- Do NOT change any other logic
- Run pylint src/ to verify W0707/W0719/W4903/W0706 are resolved
- Run pytest (fast unit tests) to confirm no regressions
- Run mypy to confirm type safety

Exact locations are in step_2.md.
```
