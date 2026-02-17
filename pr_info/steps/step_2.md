# Step 2 — Implementation: `_try_delete_empty_directory` retry loop

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for context.

The tests in Step 1 are already written and currently failing.
Your goal is to make them pass by modifying source code only — do not change tests.

In `src/mcp_coder/utils/folder_deletion.py`:

1. Add `import time` to the existing stdlib imports block (alphabetical order,
   after `import sys`).

2. Replace the single `path.rmdir()` attempt in `_try_delete_empty_directory()`
   with a 3-attempt loop:
   - Attempt rmdir up to 3 times total (initial + 2 retries)
   - Sleep 1 second between failed attempts (but NOT after the last attempt)
   - If any attempt succeeds (path gone), log and return True immediately
   - Only after all 3 attempts fail, fall through to the existing _move_to_staging call

Do not change anything else in the function or file.
The existing docstring, _move_to_staging fallback, and final return False are unchanged.
```

---

## WHERE

- **File:** `src/mcp_coder/utils/folder_deletion.py`
- **Function:** `_try_delete_empty_directory(path: Path, staging_dir: Path | None) -> bool`
- **Import block:** top of file, stdlib imports

---

## WHAT

```python
import time  # add to imports

def _try_delete_empty_directory(path: Path, staging_dir: Path | None) -> bool:
    # Replace single rmdir attempt with retry loop
    # _move_to_staging fallback and return False are unchanged
```

---

## HOW

- `import time` inserted alphabetically after `import sys`
- The `for attempt in range(3):` loop replaces the existing `try: path.rmdir()` block
- `time.sleep(1)` called in the `except` block only when `attempt < 2` (i.e. not after the final attempt)
- No other changes to the function or module

---

## ALGORITHM

```
for attempt in range(3):           # 3 total attempts
    try:
        path.rmdir()
        if not path.exists():
            log success; return True
    except (PermissionError, OSError):
        if attempt < 2:            # sleep only between attempts, not after last
            time.sleep(1)
# all attempts failed — fall through to existing staging logic
if _move_to_staging(path, staging_dir):
    return True
return False
```

---

## DATA

- Return type: `bool` (unchanged)
- `True` = directory deleted or staged successfully
- `False` = all strategies exhausted
- No changes to callers — `safe_delete_folder()` calls this function unchanged
