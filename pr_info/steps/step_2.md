# Step 2: Session Status Update Helper

## LLM Prompt

```
Implement Step 2 of Issue #400 (see pr_info/steps/summary.md for context).

This step adds a helper function to update session status in the session store.

Follow TDD: Write tests first, then implement the functionality.
```

## Overview

Add `update_session_status()` function to `sessions.py` for updating the status field of an existing session.

---

## Part A: Add Helper Function to sessions.py

### WHERE
- `src/mcp_coder/workflows/vscodeclaude/sessions.py`
- `tests/workflows/vscodeclaude/test_sessions.py`

### WHAT

```python
def update_session_status(folder: str, new_status: str) -> bool:
    """Update the status field for an existing session.
    
    Args:
        folder: Session folder path (used as session identifier)
        new_status: New status label to set
        
    Returns:
        True if session was found and updated, False otherwise
    """
```

### HOW
- Add after existing `update_session_pid()` function (similar pattern)
- Uses existing `load_sessions()` and `save_sessions()` functions
- No new imports needed

### ALGORITHM

```
1. Load sessions from JSON file
2. Find session with matching folder path
3. If found, update session["status"] = new_status
4. Save sessions back to file
5. Return True if updated, False if not found
```

### DATA

**Input:**
```python
folder = "C:/workspace/mcp-coder_123"
new_status = "status-04:plan-review"
```

**Returns:**
```python
True   # Session found and updated
False  # Session not found
```

**Side effect:** Session store JSON updated with new status

---

## Part B: Tests

### WHERE
- `tests/workflows/vscodeclaude/test_sessions.py`

### TEST CASES

```python
class TestUpdateSessionStatus:
    """Tests for update_session_status function."""
    
    def test_updates_existing_session_status(self, tmp_path, monkeypatch):
        """Should update status for existing session."""
        # Setup: Create session store with one session
        sessions_file = tmp_path / "sessions.json"
        initial_store = {
            "sessions": [{
                "folder": "/workspace/repo_123",
                "repo": "owner/repo",
                "issue_number": 123,
                "status": "status-01:created",
                "vscode_pid": 1234,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            }],
            "last_updated": ""
        }
        sessions_file.write_text(json.dumps(initial_store))
        
        # Patch get_sessions_file_path to use tmp_path
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file
        )
        
        # Act
        result = update_session_status(
            "/workspace/repo_123",
            "status-04:plan-review"
        )
        
        # Assert
        assert result is True
        updated_store = json.loads(sessions_file.read_text())
        assert updated_store["sessions"][0]["status"] == "status-04:plan-review"
        
    def test_returns_false_for_nonexistent_session(self, tmp_path, monkeypatch):
        """Should return False when session not found."""
        sessions_file = tmp_path / "sessions.json"
        initial_store = {"sessions": [], "last_updated": ""}
        sessions_file.write_text(json.dumps(initial_store))
        
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file
        )
        
        result = update_session_status("/nonexistent/path", "status-04:plan-review")
        
        assert result is False
        
    def test_does_not_modify_other_sessions(self, tmp_path, monkeypatch):
        """Should only update the matching session."""
        sessions_file = tmp_path / "sessions.json"
        initial_store = {
            "sessions": [
                {
                    "folder": "/workspace/repo_123",
                    "repo": "owner/repo",
                    "issue_number": 123,
                    "status": "status-01:created",
                    "vscode_pid": 1234,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                },
                {
                    "folder": "/workspace/repo_456",
                    "repo": "owner/repo",
                    "issue_number": 456,
                    "status": "status-01:created",
                    "vscode_pid": 5678,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": ""
        }
        sessions_file.write_text(json.dumps(initial_store))
        
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file
        )
        
        update_session_status("/workspace/repo_123", "status-04:plan-review")
        
        updated_store = json.loads(sessions_file.read_text())
        # First session updated
        assert updated_store["sessions"][0]["status"] == "status-04:plan-review"
        # Second session unchanged
        assert updated_store["sessions"][1]["status"] == "status-01:created"
        
    def test_updates_last_updated_timestamp(self, tmp_path, monkeypatch):
        """Should update the last_updated timestamp."""
        sessions_file = tmp_path / "sessions.json"
        initial_store = {
            "sessions": [{
                "folder": "/workspace/repo_123",
                "repo": "owner/repo",
                "issue_number": 123,
                "status": "status-01:created",
                "vscode_pid": 1234,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            }],
            "last_updated": "old-timestamp"
        }
        sessions_file.write_text(json.dumps(initial_store))
        
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file
        )
        
        update_session_status("/workspace/repo_123", "status-04:plan-review")
        
        updated_store = json.loads(sessions_file.read_text())
        assert updated_store["last_updated"] != "old-timestamp"
```

---

## Verification

After implementation, run:
```bash
pytest tests/workflows/vscodeclaude/test_sessions.py -v -k "update_session_status"
```

All tests should pass, confirming:
1. Status is updated for matching session
2. Returns False when session not found
3. Other sessions remain unchanged
4. Timestamp is updated on save
