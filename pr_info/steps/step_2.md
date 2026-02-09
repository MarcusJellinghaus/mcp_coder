# Step 2: Update cleanup.py and Module Exports

## Reference
See `pr_info/steps/summary.md` for overall architecture and design decisions.

## Goal
Integrate `safe_delete_folder()` into the existing codebase by updating `cleanup.py` and exporting from `utils/__init__.py`.

---

## WHERE: File Paths

### Modify
- `src/mcp_coder/utils/__init__.py`
- `src/mcp_coder/workflows/vscodeclaude/cleanup.py`
- `tests/workflows/vscodeclaude/test_cleanup.py` (add integration test)
- `tools/safe_delete_folder.py` (add comments pointing to library functions)

---

## WHAT: Changes Required

### utils/__init__.py

**Add to Layer 1 imports:**
```python
from .folder_deletion import safe_delete_folder
```

**Add to __all__:**
```python
"safe_delete_folder",
```

### cleanup.py

**Add import:**
```python
from ...utils.folder_deletion import safe_delete_folder
```

**Modify delete_session_folder():**
```python
def delete_session_folder(session: VSCodeClaudeSession) -> bool:
    """Delete session folder and remove from session store."""
    folder_path = Path(session["folder"])

    try:
        # Use safe_delete_folder for robust folder deletion
        if folder_path.exists():
            if not safe_delete_folder(folder_path):
                logger.error("Failed to delete session folder: %s", folder_path)
                return False
            logger.info("Deleted folder: %s", folder_path)

        # Keep existing workspace file and session removal logic
        workspace_base = folder_path.parent
        workspace_file = workspace_base / f"{folder_path.name}.code-workspace"
        if workspace_file.exists():
            workspace_file.unlink()
            logger.info("Deleted workspace file: %s", workspace_file)

        remove_session(session["folder"])
        return True
    except Exception as e:
        logger.error("Failed to delete session folder %s: %s", folder_path, e)
        return False
```

---

## HOW: Integration Points

### Import Changes in cleanup.py

**Remove:**
```python
import shutil  # No longer needed directly
```

**Add:**
```python
from ...utils.folder_deletion import safe_delete_folder
```

### Layer 1 Export Pattern

The `folder_deletion` module has no dependencies on other utils submodules, so it belongs in Layer 1 (same as `clipboard`, `log_utils`, `subprocess_runner`, `user_config`).

---

## ALGORITHM: Updated delete_session_folder()

```
1. Get folder_path from session
2. If folder exists:
   a. Call safe_delete_folder(folder_path)
   b. If returns False → log error, return False
   c. Log success
3. Delete workspace file if exists
4. Remove session from store
5. Return True
```

---

## DATA: No New Data Structures

The function signature and return type remain the same:
```python
def delete_session_folder(session: VSCodeClaudeSession) -> bool
```

---

## TESTS: Integration Test

### Add to test_cleanup.py
```python
def test_delete_session_folder_uses_safe_delete(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifies safe_delete_folder is called for folder deletion."""
    folder = tmp_path / "test_folder"
    folder.mkdir()
    
    safe_delete_called = []
    
    def mock_safe_delete(path, **kwargs):
        safe_delete_called.append(path)
        # Actually delete for the test
        if Path(path).exists():
            shutil.rmtree(path)
        return True
    
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.cleanup.safe_delete_folder",
        mock_safe_delete,
    )
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.cleanup.remove_session",
        lambda f: True,
    )
    
    session: VSCodeClaudeSession = {
        "folder": str(folder),
        "repo": "owner/repo",
        "issue_number": 123,
        "status": "status-07:code-review",
        "vscode_pid": None,
        "started_at": "2024-01-01T00:00:00Z",
        "is_intervention": False,
    }
    
    result = delete_session_folder(session)
    
    assert result is True
    assert len(safe_delete_called) == 1
    assert Path(safe_delete_called[0]) == folder
```

---

## LLM Prompt for Step 2

```
Implement Step 2 of Issue #417: Update cleanup.py and module exports.

Reference: pr_info/steps/summary.md and pr_info/steps/step_2.md

Tasks:
1. Update src/mcp_coder/utils/__init__.py:
   - Add `from .folder_deletion import safe_delete_folder` to Layer 1 imports
   - Add "safe_delete_folder" to __all__ list

2. Update src/mcp_coder/workflows/vscodeclaude/cleanup.py:
   - Add import: `from ...utils.folder_deletion import safe_delete_folder`
   - Remove `import shutil` (no longer needed)
   - Replace shutil.rmtree() call with safe_delete_folder() in delete_session_folder()
   - Handle the boolean return value appropriately

3. Add integration test to tests/workflows/vscodeclaude/test_cleanup.py:
   - Test that safe_delete_folder is called when deleting session folders

4. Add comments to tools/safe_delete_folder.py:
   - Add note near similar functions pointing to library equivalents
   - Example: "# Note: Similar function exists in src/mcp_coder/utils/folder_deletion.py"

Run all tests after implementation to verify nothing is broken.
```
