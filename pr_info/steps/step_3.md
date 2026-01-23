# Step 3: Session Management

## LLM Prompt

```
Implement Step 3 of the coordinator vscodeclaude feature.
Reference: pr_info/steps/summary.md for overall architecture.
This step: Session loading, saving, and PID checking with psutil.
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py` | Add session functions |
| `tests/cli/commands/coordinator/test_vscodeclaude.py` | Add session tests |

## WHAT

### vscodeclaude.py - Session Functions

```python
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

logger = logging.getLogger(__name__)

def get_sessions_file_path() -> Path:
    """Get path to sessions JSON file.
    
    Returns:
        Path to ~/.mcp_coder/coordinator_cache/vscodeclaude_sessions.json
    """
    
def load_sessions() -> VSCodeClaudeSessionStore:
    """Load sessions from JSON file.
    
    Returns:
        Session store dict. Empty sessions list if file doesn't exist.
    """
    
def save_sessions(store: VSCodeClaudeSessionStore) -> None:
    """Save sessions to JSON file.
    
    Args:
        store: Session store to save
        
    Creates parent directories if needed.
    """

def check_vscode_running(pid: Optional[int]) -> bool:
    """Check if VSCode process is still running.
    
    Args:
        pid: Process ID to check (None returns False)
        
    Returns:
        True if process exists and is running
        
    Uses psutil for cross-platform compatibility.
    """

def get_session_for_issue(
    repo_full_name: str, 
    issue_number: int
) -> Optional[VSCodeClaudeSession]:
    """Find existing session for an issue.
    
    Args:
        repo_full_name: "owner/repo" format
        issue_number: GitHub issue number
        
    Returns:
        Session dict if found, None otherwise
    """

def add_session(session: VSCodeClaudeSession) -> None:
    """Add new session to store.
    
    Args:
        session: Session to add
        
    Automatically updates last_updated timestamp.
    """

def remove_session(folder: str) -> bool:
    """Remove session by folder path.
    
    Args:
        folder: Full path to working folder
        
    Returns:
        True if session was found and removed
    """

def get_active_session_count() -> int:
    """Count sessions with running VSCode processes.
    
    Returns:
        Number of sessions where VSCode PID is still running
    """

def update_session_pid(folder: str, pid: int) -> None:
    """Update VSCode PID for existing session.
    
    Args:
        folder: Session folder path
        pid: New VSCode process ID
    """
```

## HOW

### Integration Points

1. `psutil` imported lazily in `check_vscode_running()`
2. Sessions file uses same cache directory as coordinator (`~/.mcp_coder/coordinator_cache/`)
3. JSON format matches `VSCodeClaudeSessionStore` TypedDict

### File Location

```python
def get_sessions_file_path() -> Path:
    if platform.system() == "Windows":
        base = Path.home() / ".mcp_coder"
    else:
        base = Path.home() / ".config" / "mcp_coder"
    return base / "coordinator_cache" / "vscodeclaude_sessions.json"
```

## ALGORITHM

### load_sessions()
```
1. Get sessions file path
2. If file doesn't exist: return empty store
3. Read and parse JSON
4. Validate structure, return store
5. On parse error: log warning, return empty store
```

### check_vscode_running()
```
1. If pid is None: return False
2. Import psutil
3. Try psutil.pid_exists(pid)
4. If exists, check process name contains "code"
5. Return True if running VSCode, False otherwise
```

### get_active_session_count()
```
1. Load sessions
2. For each session: check if vscode_pid is running
3. Return count of running sessions
```

## DATA

### Session JSON Structure

```json
{
  "sessions": [
    {
      "folder": "C:\\Users\\Marcus\\Documents\\GitHub\\mcp-coder_123",
      "repo": "MarcusJellinghaus/mcp-coder",
      "issue_number": 123,
      "status": "status-07:code-review",
      "vscode_pid": 12345,
      "started_at": "2024-01-22T10:30:00Z",
      "is_intervention": false
    }
  ],
  "last_updated": "2024-01-22T10:35:00Z"
}
```

### Test Coverage

```python
# test_vscodeclaude.py

class TestSessionManagement:
    """Test session load/save/check functions."""
    
    def test_get_sessions_file_path_windows(self, monkeypatch):
        """Sessions file is in .mcp_coder on Windows."""
        monkeypatch.setattr("platform.system", lambda: "Windows")
        path = get_sessions_file_path()
        assert ".mcp_coder" in str(path)
        assert "vscodeclaude_sessions.json" in str(path)
    
    def test_get_sessions_file_path_linux(self, monkeypatch):
        """Sessions file is in .config/mcp_coder on Linux."""
        monkeypatch.setattr("platform.system", lambda: "Linux")
        path = get_sessions_file_path()
        assert ".config/mcp_coder" in str(path) or ".config\\mcp_coder" in str(path)
    
    def test_load_sessions_empty_when_no_file(self, tmp_path, monkeypatch):
        """Returns empty store when file doesn't exist."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: tmp_path / "nonexistent.json"
        )
        store = load_sessions()
        assert store["sessions"] == []
    
    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        """Sessions survive save/load cycle."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file
        )
        
        session: VSCodeClaudeSession = {
            "folder": str(tmp_path / "test_123"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False
        }
        
        store: VSCodeClaudeSessionStore = {
            "sessions": [session],
            "last_updated": "2024-01-22T10:30:00Z"
        }
        
        save_sessions(store)
        loaded = load_sessions()
        
        assert len(loaded["sessions"]) == 1
        assert loaded["sessions"][0]["issue_number"] == 123
    
    def test_check_vscode_running_none_pid(self):
        """None PID returns False."""
        assert check_vscode_running(None) is False
    
    def test_check_vscode_running_nonexistent_pid(self):
        """Nonexistent PID returns False."""
        # Use a PID that almost certainly doesn't exist
        assert check_vscode_running(999999999) is False
    
    def test_get_session_for_issue_found(self, tmp_path, monkeypatch):
        """Finds session by repo and issue number."""
        # Setup session store with test data
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file
        )
        
        session = {
            "folder": "/test/folder",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))
        
        found = get_session_for_issue("owner/repo", 123)
        assert found is not None
        assert found["issue_number"] == 123
    
    def test_get_session_for_issue_not_found(self, tmp_path, monkeypatch):
        """Returns None when no matching session."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file
        )
        store = {"sessions": [], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))
        
        found = get_session_for_issue("owner/repo", 999)
        assert found is None
    
    def test_add_session(self, tmp_path, monkeypatch):
        """Adds session to store."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file
        )
        
        session: VSCodeClaudeSession = {
            "folder": "/test/folder",
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-04:plan-review",
            "vscode_pid": 5678,
            "started_at": "2024-01-22T11:00:00Z",
            "is_intervention": False
        }
        
        add_session(session)
        
        loaded = load_sessions()
        assert len(loaded["sessions"]) == 1
        assert loaded["sessions"][0]["issue_number"] == 456
    
    def test_remove_session(self, tmp_path, monkeypatch):
        """Removes session by folder path."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file
        )
        
        session = {
            "folder": "/test/folder",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))
        
        result = remove_session("/test/folder")
        assert result is True
        
        loaded = load_sessions()
        assert len(loaded["sessions"]) == 0
    
    def test_get_active_session_count_with_mocked_pid_check(self, tmp_path, monkeypatch):
        """Counts only sessions with running PIDs."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file
        )
        
        # Mock check_vscode_running to return True for specific PID
        def mock_check(pid):
            return pid == 1111
        
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.check_vscode_running",
            mock_check
        )
        
        sessions = [
            {"folder": "/a", "repo": "o/r", "issue_number": 1, "status": "s", 
             "vscode_pid": 1111, "started_at": "2024-01-01T00:00:00Z", "is_intervention": False},
            {"folder": "/b", "repo": "o/r", "issue_number": 2, "status": "s",
             "vscode_pid": 2222, "started_at": "2024-01-01T00:00:00Z", "is_intervention": False},
        ]
        store = {"sessions": sessions, "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))
        
        count = get_active_session_count()
        assert count == 1  # Only PID 1111 is "running"
```

## Verification

```bash
# Run session management tests
pytest tests/cli/commands/coordinator/test_vscodeclaude.py::TestSessionManagement -v

# Type check
mypy src/mcp_coder/cli/commands/coordinator/vscodeclaude.py
```
