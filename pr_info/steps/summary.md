# Summary — Issue #457: coordinator vscodeclaude --cleanup: also delete empty No Git / Error folders

## Overview

Two targeted bug fixes to make `mcp-coder coordinator vscodeclaude --cleanup` handle edge cases it currently skips silently.

---

## Problem

`cleanup_stale_sessions()` skips **all** "No Git" and "Error" status folders with a warning, even when they are completely empty and safe to delete.

`_try_delete_empty_directory()` gives up immediately after one failed `rmdir`, falling back to staging — when a brief Windows Explorer handle-hold would release within seconds.

---

## Architectural / Design Changes

### No structural changes

Both fixes are **in-place behaviour extensions** — no new modules, no new classes, no API surface changes. The call graph and module dependencies are unchanged.

| Aspect | Before | After |
|---|---|---|
| Module structure | unchanged | unchanged |
| Public API | unchanged | unchanged |
| Cross-module imports | unchanged | unchanged |

### Change 1 — `cleanup.py`: empty-folder gate in the `else` branch

The `else` branch in `cleanup_stale_sessions()` previously treated all "No Git" / "Error" folders identically (skip + warn). After this fix, an emptiness check is inserted **before** the skip logic. Empty folders are processed identically to "Clean" folders (delete or dry-run report). Non-empty folders are still skipped with a warning.

No new imports are needed — `Path` is already imported.

### Change 2 — `folder_deletion.py`: retry loop in `_try_delete_empty_directory()`

The single `path.rmdir()` attempt is replaced with a **3-attempt loop** (initial + 2 retries) with `time.sleep(1)` between failures before falling back to `_move_to_staging()`. This handles the common Windows case where a process briefly holds a directory handle open after its files are removed.

Only `import time` is added to the module.

---

## Files Modified

| File | Change |
|---|---|
| `src/mcp_coder/utils/folder_deletion.py` | Add `import time`; convert single `rmdir` to 3-attempt retry loop in `_try_delete_empty_directory()` |
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | Add emptiness check in `else` branch of `cleanup_stale_sessions()` |
| `tests/utils/test_folder_deletion.py` | Add retry-loop tests for `_try_delete_empty_directory` |
| `tests/workflows/vscodeclaude/test_cleanup.py` | Update existing "No Git"/"Error" tests; add 4 new empty-folder tests |

## Files Created

_None._

---

## Implementation Steps

| Step | File(s) | What |
|---|---|---|
| Step 1 | `test_folder_deletion.py` | Tests for `_try_delete_empty_directory` retry behaviour |
| Step 2 | `folder_deletion.py` | Implement retry loop to make Step 1 tests pass |
| Step 3 | `test_cleanup.py` | Tests for empty "No Git"/"Error" folder deletion |
| Step 4 | `cleanup.py` | Implement emptiness gate to make Step 3 tests pass |
