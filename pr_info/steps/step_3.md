# Step 3: Update Cleanup Logic for All Status Cases

## LLM Prompt
```
Read pr_info/steps/summary.md for context on issue #413.
Implement Step 3: Update cleanup.py to handle all git status cases appropriately.
```

## Overview
Update cleanup logic to handle `Missing`, `No Git`, and `Error` status cases appropriately, not just `Dirty` vs `Clean`.

---

## Part A: Update `get_stale_sessions()`

### WHERE
`src/mcp_coder/workflows/vscodeclaude/cleanup.py`

### WHAT
Change return type to include status string instead of just `is_dirty` boolean:

```python
def get_stale_sessions(
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> list[tuple[VSCodeClaudeSession, str]]:  # Changed: bool -> str
    """Get stale sessions with git status.
    
    Returns:
        List of (session, git_status) tuples where git_status is one of:
        "Clean", "Dirty", "Missing", "No Git", "Error"
    """
```

### ALGORITHM
```python
# Change from:
is_dirty = check_folder_dirty(folder_path) if folder_path.exists() else False
stale_sessions.append((session, is_dirty))

# To:
git_status = get_folder_git_status(folder_path)
stale_sessions.append((session, git_status))
```

### HOW
- Import `get_folder_git_status` from `.status`
- Remove the `if folder_path.exists()` check (function handles it)
- Change tuple second element from `bool` to `str`

---

## Part B: Update `cleanup_stale_sessions()`

### WHERE
`src/mcp_coder/workflows/vscodeclaude/cleanup.py`

### WHAT
Handle all status cases with appropriate actions and messages:

```python
def cleanup_stale_sessions(
    dry_run: bool = True,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> dict[str, list[str]]:
    """Clean up stale session folders.
    
    Behavior by status:
    - Clean: delete folder and session
    - Dirty: skip with warning (uncommitted changes)
    - Missing: remove session only (folder already gone)
    - No Git / Error: skip with warning (investigate manually)
    """
```

### ALGORITHM
```python
for session, git_status in stale_sessions:
    folder = session["folder"]
    
    if git_status == "Clean":
        # Delete folder and session
        if not dry_run:
            delete_session_folder(session)
            result["deleted"].append(folder)
        else:
            print(f"Would delete: {folder}")
            
    elif git_status == "Missing":
        # Folder gone, just remove session record
        if not dry_run:
            remove_session(folder)
            result["deleted"].append(folder)
            print(f"Removed session (folder missing): {folder}")
        else:
            print(f"Would remove session (folder missing): {folder}")
            
    elif git_status == "Dirty":
        # Skip - has uncommitted changes
        logger.warning("Skipping dirty folder: %s", folder)
        print(f"⚠️  Skipping (dirty): {folder}")
        result["skipped"].append(folder)
        
    else:  # "No Git" or "Error"
        # Skip - needs manual investigation
        logger.warning("Skipping folder (%s): %s", git_status.lower(), folder)
        print(f"⚠️  Skipping ({git_status.lower()}): {folder}")
        result["skipped"].append(folder)
```

---

## Part C: Update Tests

### WHERE
`tests/workflows/vscodeclaude/test_cleanup.py`

### WHAT
Update tests to use new string-based status:

```python
class TestCleanup:
    def test_get_stale_sessions_returns_stale(...) -> None:
        # Change mock to return status string
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_folder_git_status",
            lambda path: "Clean",
        )
        result = get_stale_sessions()
        assert result[0][1] == "Clean"  # Changed from False
    
    def test_cleanup_handles_missing_folder(...) -> None:
        # New test for missing folder case
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda cached_issues_by_repo=None: [(session, "Missing")],
        )
        result = cleanup_stale_sessions(dry_run=False)
        assert folder in result["deleted"]
    
    def test_cleanup_skips_no_git_folder(...) -> None:
        # New test for no git case
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda cached_issues_by_repo=None: [(session, "No Git")],
        )
        result = cleanup_stale_sessions(dry_run=False)
        assert folder in result["skipped"]
    
    def test_cleanup_skips_error_folder(...) -> None:
        # New test for error case
        ...
```

### TESTS TO UPDATE
1. `test_get_stale_sessions_returns_stale` - change `is_dirty` mock to `get_folder_git_status`
2. `test_cleanup_stale_sessions_skips_dirty` - update tuple assertion
3. `test_cleanup_stale_sessions_deletes_clean` - update tuple assertion

### NEW TESTS TO ADD
1. `test_cleanup_handles_missing_folder` - verifies session removed when folder missing
2. `test_cleanup_skips_no_git_folder` - verifies skip with warning
3. `test_cleanup_skips_error_folder` - verifies skip with warning

---

## Part D: Update Import

### WHERE
`src/mcp_coder/workflows/vscodeclaude/cleanup.py`

### WHAT
```python
from .status import get_folder_git_status, is_session_stale  # Updated import
# Remove: from .status import check_folder_dirty
```

---

## Verification
```bash
# Run cleanup tests
pytest tests/workflows/vscodeclaude/test_cleanup.py -v

# Run all vscodeclaude tests
pytest tests/workflows/vscodeclaude/ -v

# Run full test suite
pytest tests/ -v --tb=short
```
