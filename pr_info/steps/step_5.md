# Step 5: Skip Blocked Issues in Restart and Update Status

## LLM Prompt

```
Implement Step 5 of Issue #400 (see pr_info/steps/summary.md for context).

This step modifies restart_closed_sessions() to skip blocked issues and update session status.

Follow TDD: Write tests first, then implement the functionality.
```

## Overview

Modify `restart_closed_sessions()` in `orchestrator.py` to:
1. Skip restarting sessions for issues with ignore labels (blocked/wait)
2. Update session status to current GitHub status when restarting

---

## Part A: Modify restart_closed_sessions()

### WHERE
- `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`
- `tests/workflows/vscodeclaude/test_orchestrator_sessions.py`

### WHAT

Add blocked-issue detection and status update to `restart_closed_sessions()`.

### HOW

**Add imports:**
```python
from .issues import get_ignore_labels, get_matching_ignore_label
from .sessions import update_session_status
```

**Add to function body (after getting issue data, before restarting):**

```python
# Check if issue has ignore label (blocked/wait)
ignore_labels = get_ignore_labels()
blocked_label = get_matching_ignore_label(issue["labels"], ignore_labels)
if blocked_label:
    logger.info(
        "Skipping blocked session for issue #%d (label: %s)",
        issue_number,
        blocked_label,
    )
    continue

# Update session status if changed
current_status = get_issue_status(issue)  # existing helper
if current_status != session["status"]:
    update_session_status(session["folder"], current_status)
    logger.debug(
        "Updated session status for #%d: %s -> %s",
        issue_number,
        session["status"],
        current_status,
    )
```

### ALGORITHM

```
1. Load ignore_labels at start of function (once)
2. For each closed session:
3.   Fetch issue data (existing logic)
4.   Check if issue has ignore label -> skip if blocked
5.   Check if status changed -> update session if so
6.   Regenerate files and restart VSCode (existing logic)
```

### DATA

**Log output for blocked issue:**
```
INFO: Skipping blocked session for issue #123 (label: blocked)
```

**Log output for status update:**
```
DEBUG: Updated session status for #123: status-01:created -> status-04:plan-review
```

---

## Part B: Tests

### WHERE
- `tests/workflows/vscodeclaude/test_orchestrator_sessions.py`

### TEST CASES

```python
class TestRestartClosedSessionsBlocked:
    """Tests for blocked issue handling in restart_closed_sessions."""
    
    def test_skips_blocked_issues(self, monkeypatch, tmp_path):
        """Should not restart sessions for issues with blocked label."""
        # Setup session
        mock_sessions = {
            "sessions": [{
                "folder": str(tmp_path / "repo_123"),
                "repo": "owner/repo",
                "issue_number": 123,
                "status": "status-01:created",
                "vscode_pid": None,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            }],
            "last_updated": ""
        }
        
        # Create folder so it passes existence check
        (tmp_path / "repo_123").mkdir()
        
        # Setup cached issues with blocked label
        mock_cached_issues = {
            "owner/repo": {
                123: {
                    "number": 123,
                    "title": "Test Issue",
                    "state": "open",
                    "labels": ["status-01:created", "blocked"],
                    "assignees": ["user"],
                    "url": "https://github.com/owner/repo/issues/123",
                }
            }
        }
        
        # Monkeypatch dependencies
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.load_sessions",
            lambda: mock_sessions
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_window_open_for_folder",
            lambda *args, **kwargs: False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_open_for_folder",
            lambda folder: (False, None)
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"}
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_session_stale",
            lambda session, cached_issues=None: False
        )
        
        # Track if launch_vscode was called
        launch_called = []
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode",
            lambda ws: launch_called.append(ws)
        )
        
        result = restart_closed_sessions(cached_issues_by_repo=mock_cached_issues)
        
        assert len(result) == 0  # No sessions restarted
        assert len(launch_called) == 0  # VSCode not launched
        
    def test_skips_wait_labeled_issues(self, monkeypatch, tmp_path):
        """Should not restart sessions for issues with wait label."""
        mock_sessions = {
            "sessions": [{
                "folder": str(tmp_path / "repo_456"),
                "repo": "owner/repo",
                "issue_number": 456,
                "status": "status-04:plan-review",
                "vscode_pid": None,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            }],
            "last_updated": ""
        }
        
        (tmp_path / "repo_456").mkdir()
        
        mock_cached_issues = {
            "owner/repo": {
                456: {
                    "number": 456,
                    "title": "Test Issue",
                    "state": "open",
                    "labels": ["status-04:plan-review", "wait"],  # wait label
                    "assignees": ["user"],
                    "url": "",
                }
            }
        }
        
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.load_sessions",
            lambda: mock_sessions
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_window_open_for_folder",
            lambda *args, **kwargs: False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_open_for_folder",
            lambda folder: (False, None)
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"}
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_session_stale",
            lambda session, cached_issues=None: False
        )
        
        launch_called = []
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode",
            lambda ws: launch_called.append(ws)
        )
        
        result = restart_closed_sessions(cached_issues_by_repo=mock_cached_issues)
        
        assert len(result) == 0
        assert len(launch_called) == 0
        
    def test_case_insensitive_blocked_detection(self, monkeypatch, tmp_path):
        """Should detect BLOCKED label case-insensitively."""
        mock_sessions = {
            "sessions": [{
                "folder": str(tmp_path / "repo_789"),
                "repo": "owner/repo",
                "issue_number": 789,
                "status": "status-01:created",
                "vscode_pid": None,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            }],
            "last_updated": ""
        }
        
        (tmp_path / "repo_789").mkdir()
        
        mock_cached_issues = {
            "owner/repo": {
                789: {
                    "number": 789,
                    "title": "Test",
                    "state": "open",
                    "labels": ["status-01:created", "BLOCKED"],  # UPPERCASE
                    "assignees": ["user"],
                    "url": "",
                }
            }
        }
        
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.load_sessions",
            lambda: mock_sessions
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_window_open_for_folder",
            lambda *args, **kwargs: False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_open_for_folder",
            lambda folder: (False, None)
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"}
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_session_stale",
            lambda session, cached_issues=None: False
        )
        
        launch_called = []
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode",
            lambda ws: launch_called.append(ws)
        )
        
        result = restart_closed_sessions(cached_issues_by_repo=mock_cached_issues)
        
        assert len(result) == 0  # Blocked detected
        

class TestRestartClosedSessionsStatusUpdate:
    """Tests for status update in restart_closed_sessions."""
    
    def test_updates_session_status_when_changed(self, monkeypatch, tmp_path):
        """Should update session status when GitHub status differs."""
        sessions_file = tmp_path / "sessions.json"
        session_folder = tmp_path / "repo_123"
        session_folder.mkdir()
        
        mock_sessions = {
            "sessions": [{
                "folder": str(session_folder),
                "repo": "owner/repo",
                "issue_number": 123,
                "status": "status-01:created",  # Old status
                "vscode_pid": None,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            }],
            "last_updated": ""
        }
        sessions_file.write_text(json.dumps(mock_sessions))
        
        # Issue now has different status
        mock_cached_issues = {
            "owner/repo": {
                123: {
                    "number": 123,
                    "title": "Test",
                    "state": "open",
                    "labels": ["status-04:plan-review"],  # Changed status
                    "assignees": ["user"],
                    "url": "",
                }
            }
        }
        
        # Track status updates
        status_updates = []
        
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.load_sessions",
            lambda: json.loads(sessions_file.read_text())
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            lambda pid: False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_window_open_for_folder",
            lambda *args, **kwargs: False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_open_for_folder",
            lambda folder: (False, None)
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            lambda: {"owner/repo"}
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_session_stale",
            lambda session, cached_issues=None: False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.update_session_status",
            lambda folder, status: status_updates.append((folder, status))
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.regenerate_session_files",
            lambda session, issue: tmp_path / "script.bat"
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode",
            lambda ws: 9999
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.orchestrator.update_session_pid",
            lambda folder, pid: None
        )
        
        # Create workspace file
        workspace_file = tmp_path / f"{session_folder.name}.code-workspace"
        workspace_file.write_text("{}")
        
        restart_closed_sessions(cached_issues_by_repo=mock_cached_issues)
        
        # Verify status was updated
        assert len(status_updates) == 1
        assert status_updates[0][0] == str(session_folder)
        assert status_updates[0][1] == "status-04:plan-review"
```

---

## Verification

After implementation, run:
```bash
pytest tests/workflows/vscodeclaude/test_orchestrator_sessions.py -v -k "blocked or status_update"
```

All tests should pass, confirming:
1. Blocked sessions are not restarted
2. Wait-labeled sessions are not restarted  
3. Case-insensitive label matching works
4. Session status is updated when restarting
