# Step 8: Status Display & Cleanup

## LLM Prompt

```
Implement Step 8 of the coordinator vscodeclaude feature.
Reference: pr_info/steps/summary.md for overall architecture.
This step: Status table display, stale detection, cleanup logic.
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py` | Add status and cleanup functions |
| `tests/cli/commands/coordinator/test_vscodeclaude.py` | Add status and cleanup tests |

## WHAT

### vscodeclaude.py - Status Functions

```python
def get_issue_current_status(
    issue_manager: IssueManager,
    issue_number: int,
) -> Optional[str]:
    """Get current status label for an issue.
    
    Args:
        issue_manager: IssueManager for GitHub API
        issue_number: GitHub issue number
        
    Returns:
        Current status label or None if no status found
    """

def is_session_stale(session: VSCodeClaudeSession) -> bool:
    """Check if session's issue status has changed.
    
    Args:
        session: Session to check
        
    Returns:
        True if issue status differs from session status
    """

def check_folder_dirty(folder_path: Path) -> bool:
    """Check if folder has uncommitted changes.
    
    Args:
        folder_path: Path to git repository
        
    Returns:
        True if there are uncommitted changes
        
    Uses: git status --porcelain
    """

def display_status_table(
    sessions: List[VSCodeClaudeSession],
    eligible_issues: List[tuple[str, IssueData]],  # (repo_name, issue)
    repo_filter: Optional[str] = None,
) -> None:
    """Print status table to stdout.
    
    Args:
        sessions: Current sessions from JSON
        eligible_issues: Eligible issues not yet in sessions
        repo_filter: Optional repo name filter
        
    Columns:
    - Folder
    - Issue
    - Status
    - VSCode
    - Repo
    - Next Action
    """

def get_next_action(
    session: VSCodeClaudeSession,
    is_stale: bool,
    is_dirty: bool,
    is_vscode_running: bool,
) -> str:
    """Determine next action for a session.
    
    Args:
        session: Session data
        is_stale: Whether issue status changed
        is_dirty: Whether folder has uncommitted changes
        is_vscode_running: Whether VSCode is still running
        
    Returns:
        Action string like "(active)", "→ Restart", "→ Delete", "⚠️ Manual cleanup"
    """
```

### vscodeclaude.py - Cleanup Functions

```python
def get_stale_sessions() -> List[tuple[VSCodeClaudeSession, bool]]:
    """Get stale sessions with dirty status.
    
    Returns:
        List of (session, is_dirty) tuples for stale sessions
    """

def cleanup_stale_sessions(dry_run: bool = True) -> dict[str, List[str]]:
    """Clean up stale session folders.
    
    Args:
        dry_run: If True, only report what would be deleted
        
    Returns:
        Dict with "deleted" and "skipped" folder lists
        
    Behavior:
    - Stale + clean: delete folder and session
    - Stale + dirty: skip with warning
    """

def delete_session_folder(session: VSCodeClaudeSession) -> bool:
    """Delete session folder and remove from session store.
    
    Args:
        session: Session to delete
        
    Returns:
        True if successfully deleted
        
    Uses shutil.rmtree for folder deletion.
    """
```

## HOW

### Integration Points

1. Uses `subprocess.run(["git", "status", "--porcelain"])` for dirty check
2. Uses `shutil.rmtree` for folder deletion
3. Uses `IssueManager.get_issue()` for current status lookup
4. Table formatting uses simple string formatting (no external library)

### Status Table Format

```
Folder              Issue  Status          VSCode    Repo        Next Action
mcp-coder_123       #123   code-review     Running   mcp-coder   (active)
mcp-coder_456       #456   → ready-pr      Closed    mcp-coder   → Delete (with --cleanup)
mcp-coder_789       #789   → ready-pr      Closed    mcp-coder   ⚠️ Manual cleanup
-                   #101   code-review     -         mcp-coder   → Create and start
```

## ALGORITHM

### is_session_stale()
```
1. Get IssueManager for session's repo
2. Get current issue status via API
3. Compare with session["status"]
4. Return True if different, False if same
```

### check_folder_dirty()
```
1. Run: git status --porcelain
2. If output is empty: return False (clean)
3. If output has content: return True (dirty)
4. On error: return True (assume dirty to be safe)
```

### display_status_table()
```
1. Build header row
2. For each session:
   - Get VSCode running status
   - Get stale status
   - Get dirty status
   - Get next action
   - Build row
3. For each eligible issue not in sessions:
   - Build row with "→ Create and start"
4. Apply repo_filter if specified
5. Print formatted table
```

### cleanup_stale_sessions()
```
1. Get all stale sessions with dirty status
2. For each (session, is_dirty):
   - If is_dirty: add to skipped, print warning
   - If not dry_run and not is_dirty:
     - delete_session_folder(session)
     - add to deleted
3. Return {"deleted": [...], "skipped": [...]}
```

### get_next_action()
```
1. If is_vscode_running: return "(active)"
2. If is_stale and is_dirty: return "⚠️ Manual cleanup"
3. If is_stale and not is_dirty: return "→ Delete (with --cleanup)"
4. If not is_stale: return "→ Restart"
```

## DATA

### Status Display

| Column | Width | Description |
|--------|-------|-------------|
| Folder | 20 | Folder name (truncated) |
| Issue | 6 | #number |
| Status | 16 | Status label or "→ newstatus" |
| VSCode | 10 | Running/Closed |
| Repo | 15 | Short repo name |
| Next Action | 20 | Action indicator |

### Next Action Values

| Condition | Display |
|-----------|---------|
| VSCode running | `(active)` |
| Closed, not stale | `→ Restart` |
| Stale, clean | `→ Delete (with --cleanup)` |
| Stale, dirty | `⚠️ Manual cleanup` |
| New eligible issue | `→ Create and start` |

### Test Coverage

```python
# test_vscodeclaude.py

class TestStatusDisplay:
    """Test status table and display functions."""
    
    def test_is_session_stale_same_status(self, monkeypatch):
        """Returns False when status unchanged."""
        mock_issue = {"labels": ["status-07:code-review"]}
        mock_manager = Mock()
        mock_manager.get_issue.return_value = mock_issue
        
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.IssueManager",
            lambda *args: mock_manager
        )
        
        session = {
            "folder": "/test",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False
        }
        
        assert is_session_stale(session) is False
    
    def test_is_session_stale_status_changed(self, monkeypatch):
        """Returns True when status changed."""
        mock_issue = {"labels": ["status-08:ready-pr"]}  # Changed
        mock_manager = Mock()
        mock_manager.get_issue.return_value = mock_issue
        
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.IssueManager",
            lambda *args: mock_manager
        )
        
        session = {
            "folder": "/test",
            "repo": "owner/repo", 
            "issue_number": 123,
            "status": "status-07:code-review",  # Original
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False
        }
        
        assert is_session_stale(session) is True
    
    def test_check_folder_dirty_clean(self, tmp_path, monkeypatch):
        """Returns False for clean git repo."""
        def mock_run(cmd, **kwargs):
            return Mock(stdout="", returncode=0)
        
        monkeypatch.setattr("subprocess.run", mock_run)
        
        assert check_folder_dirty(tmp_path) is False
    
    def test_check_folder_dirty_with_changes(self, tmp_path, monkeypatch):
        """Returns True when uncommitted changes exist."""
        def mock_run(cmd, **kwargs):
            return Mock(stdout="M  file.py\n", returncode=0)
        
        monkeypatch.setattr("subprocess.run", mock_run)
        
        assert check_folder_dirty(tmp_path) is True
    
    def test_get_next_action_active(self):
        """Returns (active) when VSCode running."""
        session = {"status": "status-07:code-review"}
        action = get_next_action(session, is_stale=False, is_dirty=False, is_vscode_running=True)
        assert action == "(active)"
    
    def test_get_next_action_restart(self):
        """Returns Restart when closed but not stale."""
        session = {"status": "status-07:code-review"}
        action = get_next_action(session, is_stale=False, is_dirty=False, is_vscode_running=False)
        assert "Restart" in action
    
    def test_get_next_action_delete(self):
        """Returns Delete when stale and clean."""
        session = {"status": "status-07:code-review"}
        action = get_next_action(session, is_stale=True, is_dirty=False, is_vscode_running=False)
        assert "Delete" in action
    
    def test_get_next_action_manual(self):
        """Returns Manual cleanup when stale and dirty."""
        session = {"status": "status-07:code-review"}
        action = get_next_action(session, is_stale=True, is_dirty=True, is_vscode_running=False)
        assert "Manual" in action
    
    def test_display_status_table_empty(self, capsys):
        """Handles empty sessions and issues."""
        display_status_table(sessions=[], eligible_issues=[], repo_filter=None)
        
        captured = capsys.readouterr()
        assert "Folder" in captured.out or "No sessions" in captured.out


class TestCleanup:
    """Test cleanup functions."""
    
    def test_cleanup_stale_sessions_dry_run(self, tmp_path, monkeypatch):
        """Dry run reports but doesn't delete."""
        stale_session = {
            "folder": str(tmp_path / "stale_folder"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False
        }
        
        # Create the folder
        (tmp_path / "stale_folder").mkdir()
        
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_stale_sessions",
            lambda: [(stale_session, False)]  # Not dirty
        )
        
        result = cleanup_stale_sessions(dry_run=True)
        
        # Folder should still exist
        assert (tmp_path / "stale_folder").exists()
        # Should be reported as would-be-deleted
        assert len(result.get("deleted", [])) == 0  # dry_run doesn't delete
    
    def test_cleanup_stale_sessions_skips_dirty(self, tmp_path, monkeypatch):
        """Skips dirty folders with warning."""
        dirty_session = {
            "folder": str(tmp_path / "dirty_folder"),
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False
        }
        
        (tmp_path / "dirty_folder").mkdir()
        
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_stale_sessions",
            lambda: [(dirty_session, True)]  # Dirty
        )
        
        result = cleanup_stale_sessions(dry_run=False)
        
        # Folder should still exist (dirty)
        assert (tmp_path / "dirty_folder").exists()
        assert str(tmp_path / "dirty_folder") in result.get("skipped", [])
    
    def test_cleanup_stale_sessions_deletes_clean(self, tmp_path, monkeypatch):
        """Deletes clean stale folders."""
        clean_session = {
            "folder": str(tmp_path / "clean_folder"),
            "repo": "owner/repo",
            "issue_number": 789,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False
        }
        
        (tmp_path / "clean_folder").mkdir()
        
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_stale_sessions",
            lambda: [(clean_session, False)]  # Clean
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.delete_session_folder",
            lambda s: True
        )
        
        result = cleanup_stale_sessions(dry_run=False)
        
        assert str(tmp_path / "clean_folder") in result.get("deleted", [])
    
    def test_delete_session_folder_removes_folder(self, tmp_path, monkeypatch):
        """Deletes folder and removes session."""
        folder = tmp_path / "to_delete"
        folder.mkdir()
        (folder / "file.txt").write_text("test")
        
        session = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False
        }
        
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.remove_session",
            lambda f: True
        )
        
        result = delete_session_folder(session)
        
        assert result is True
        assert not folder.exists()
```

## Verification

```bash
# Run status tests
pytest tests/cli/commands/coordinator/test_vscodeclaude.py::TestStatusDisplay -v

# Run cleanup tests
pytest tests/cli/commands/coordinator/test_vscodeclaude.py::TestCleanup -v

# Run all vscodeclaude tests
pytest tests/cli/commands/coordinator/test_vscodeclaude.py -v

# Type check
mypy src/mcp_coder/cli/commands/coordinator/vscodeclaude.py

# Manual integration test
mcp-coder coordinator vscodeclaude status
mcp-coder coordinator vscodeclaude --cleanup  # dry run effect
```
