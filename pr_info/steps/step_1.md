# Step 1: Create folder_deletion.py Module with Tests

## Reference
See `pr_info/steps/summary.md` for overall architecture and design decisions.

## Goal
Create the `safe_delete_folder()` utility function with comprehensive mock-based tests.

---

## WHERE: File Paths

### Create
- `src/mcp_coder/utils/folder_deletion.py`
- `tests/utils/test_folder_deletion.py`

---

## WHAT: Functions to Implement

### Main Function
```python
def safe_delete_folder(
    path: Path | str,
    *,
    staging_dir: Path | str | None = None,
    cleanup_staging: bool = True,
) -> bool:
    """Safely delete a folder, handling locked files via staging directory."""
```

### Helper Functions
```python
def _get_default_staging_dir() -> Path:
    """Return default staging directory path (%TEMP%/safe_delete_staging)."""

def _move_to_staging(item_path: Path, staging_dir: Path | None) -> bool:
    """Move file or directory to staging with UUID suffix."""

def _cleanup_staging(staging_dir: Path | None) -> tuple[int, int]:
    """Clean up old items from staging. Returns (deleted, remaining)."""

def _rmtree_remove_readonly(func: Callable, path: str, exc: object) -> None:
    """Error handler for shutil.rmtree to handle readonly files."""

def _is_directory_empty(path: Path) -> bool:
    """Check if a directory is empty."""

def _try_delete_empty_directory(path: Path, staging_dir: Path | None) -> bool:
    """Try to delete an empty directory, moving to staging if locked."""
```

---

## HOW: Integration Points

### Imports Required
```python
import logging
import shutil
import stat
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Callable
```

### Module-Level Logger
```python
logger = logging.getLogger(__name__)
```

### Constants
```python
MAX_RETRIES = 50  # Internal, not exposed
```

---

## ALGORITHM: Core Logic

### safe_delete_folder() Pseudocode
```
1. Convert path to Path, return True if not exists (idempotent)
2. Resolve staging_dir (use default if None)
3. Loop up to MAX_RETRIES:
   a. If path gone → return True
   b. If empty dir → try _try_delete_empty_directory()
   c. Try shutil.rmtree() with readonly handler
   d. On PermissionError → move locked item to staging, continue
4. If cleanup_staging → call _cleanup_staging()
5. Return success status
```

### _move_to_staging() Pseudocode
```
1. Create staging_dir if needed
2. Generate unique name: stem_uuid8.suffix
3. Try shutil.move(item_path, staging_dir / unique_name)
4. Return True on success, False on failure
```

### Python 3.12+ Compatibility
```python
if sys.version_info >= (3, 12):
    shutil.rmtree(path, onexc=_rmtree_remove_readonly)
else:
    shutil.rmtree(path, onerror=_rmtree_remove_readonly)
```

---

## DATA: Return Values

### safe_delete_folder()
- Returns `True`: Folder deleted or didn't exist
- Returns `False`: Deletion failed after MAX_RETRIES

### _cleanup_staging()
- Returns `tuple[int, int]`: (deleted_count, remaining_count)

---

## TESTS: Mock-Based Test Suite

### Test Cases
```python
class TestSafeDeleteFolder:
    def test_nonexistent_folder_returns_true(self, tmp_path)
    def test_empty_folder_deleted(self, tmp_path)
    def test_folder_with_files_deleted(self, tmp_path)
    def test_readonly_files_handled(self, tmp_path)
    def test_locked_file_moved_to_staging(self, tmp_path, monkeypatch)
    def test_cleanup_staging_false_skips_cleanup(self, tmp_path, monkeypatch)
    def test_cleanup_staging_true_runs_cleanup(self, tmp_path, monkeypatch)
    def test_max_retries_exceeded_returns_false(self, tmp_path, monkeypatch)
    def test_empty_locked_directory_handled(self, tmp_path, monkeypatch)
    def test_directory_becomes_empty_during_deletion(self, tmp_path, monkeypatch)

class TestMoveToStaging:
    def test_moves_file_with_uuid_suffix(self, tmp_path)
    def test_moves_directory_with_uuid_suffix(self, tmp_path)
    def test_handles_move_failure(self, tmp_path, monkeypatch)

class TestCleanupStaging:
    def test_deletes_unlocked_files(self, tmp_path)
    def test_counts_remaining_locked_files(self, tmp_path, monkeypatch)
    def test_removes_empty_staging_dir(self, tmp_path)
```

---

## LLM Prompt for Step 1

```
Implement Step 1 of Issue #417: Create the folder_deletion.py module.

Reference: pr_info/steps/summary.md and pr_info/steps/step_1.md

Tasks:
1. Create src/mcp_coder/utils/folder_deletion.py with:
   - Module docstring and logger
   - MAX_RETRIES = 50 constant
   - All helper functions as specified
   - safe_delete_folder() main function
   - Python 3.12+ compatibility for shutil.rmtree

2. Create tests/utils/test_folder_deletion.py with:
   - Mock-based tests for reliable CI
   - All test cases listed in step_1.md
   - Follow existing test patterns in tests/utils/

Key requirements:
- Use error.filename only (no regex fallback)
- Handle empty locked directories
- UUID suffix for staging: f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
- Default staging: Path(tempfile.gettempdir()) / "safe_delete_staging" (shared with CLI tool)

Run tests after implementation to verify.
```
