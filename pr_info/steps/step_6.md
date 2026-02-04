# Step 6: Fix Status Command Display

## LLM Prompt

```
Implement Step 6 of Issue #400 (see pr_info/steps/summary.md for context).

This step fixes the status command to show current GitHub status instead of stored status.

Follow TDD: Write tests first, then implement the functionality.
```

## Overview

Modify `execute_coordinator_vscodeclaude_status()` in `commands.py` to:
1. Build cached issues for all repos (for fetching current status)
2. Display current GitHub status instead of stored session status
3. Show `(?)` indicator on API failure (per-repo)
4. Update session file when status changed
5. Show `Blocked (label-name)` in Next Action for blocked issues

---

## Part A: Modify execute_coordinator_vscodeclaude_status()

### WHERE
- `src/mcp_coder/cli/commands/coordinator/commands.py`
- `tests/cli/commands/coordinator/test_commands.py`

### WHAT

Rewrite the status display loop to use current GitHub data.

### HOW

**Add imports:**
```python
from ....workflows.vscodeclaude.issues import get_ignore_labels, get_matching_ignore_label
from ....workflows.vscodeclaude.sessions import update_session_status
from ....workflows.vscodeclaude.status import get_next_action
```

**Modify function to:**
1. Build `cached_issues_by_repo` at the start (reuse `_build_cached_issues_by_repo`)
2. Track `failed_repos: set[str]` for API failures
3. In the display loop, get current status from cache
4. Update session if status changed
5. Check for blocked labels
6. Use `get_next_action()` with `blocked_label` parameter

### ALGORITHM

```
1. Get repo_names from config
2. Build cached_issues_by_repo, track failed_repos
3. Load sessions
4. For each session:
5.   Get issue from cache (or show (?) if failed repo)
6.   Get current_status from issue labels
7.   If current_status != session.status: update session
8.   Check for blocked_label
9.   Call get_next_action() with blocked_label
10.  Display row with current_status (or stored+(?) if failed)
```

### DATA

**Status display examples:**

Normal case (status from GitHub):
```
Issue    Repo       Status           VSCode    Changes    Next Action
#306     mcp_coder  04:plan-review   Closed    Clean      -> Restart
```

API failure case:
```
Issue    Repo       Status           VSCode    Changes    Next Action
#306     mcp_coder  01:created (?)   Closed    Clean      -> Restart
```

Blocked case:
```
Issue    Repo       Status           VSCode    Changes    Next Action
#340     mcp_coder  01:created       Closed    Clean      Blocked (blocked)
```

---

## Part B: Refactor Status Loop

### WHERE
- `src/mcp_coder/cli/commands/coordinator/commands.py` - `execute_coordinator_vscodeclaude_status()`

### CURRENT CODE (simplified)
```python
for session in sessions:
    status_raw = session["status"]
    status = status_raw.replace("status-", "")
    # ... determine next_action based on is_running, is_dirty, folder_exists
    next_action = "-> Restart"  # hardcoded logic
```

### NEW CODE (simplified)
```python
# At function start:
config_data = load_config()
repos_section = config_data.get("coordinator", {}).get("repos", {})
repo_names = list(repos_section.keys())

# Build cache (track failures)
cached_issues_by_repo: dict[str, dict[int, IssueData]] = {}
failed_repos: set[str] = set()
for repo_name in repo_names:
    try:
        # ... existing _build_cached_issues_by_repo logic inline
        # Add repo to cached_issues_by_repo
    except Exception as e:
        logger.warning(f"Failed to fetch issues for {repo_name}: {e}")
        failed_repos.add(repo_full_name)

# Load ignore labels
ignore_labels = get_ignore_labels()

# In display loop:
for session in sessions:
    repo_full_name = session["repo"]
    issue_number = session["issue_number"]
    
    # Get current status from cache
    api_failed = repo_full_name in failed_repos
    current_status = session["status"]  # fallback
    blocked_label: str | None = None
    
    if not api_failed:
        repo_issues = cached_issues_by_repo.get(repo_full_name, {})
        if issue_number in repo_issues:
            issue = repo_issues[issue_number]
            # Get current status from issue labels
            for label in issue["labels"]:
                if label.startswith("status-"):
                    current_status = label
                    break
            # Check for blocked label
            blocked_label = get_matching_ignore_label(issue["labels"], ignore_labels)
            
            # Update session if status changed
            if current_status != session["status"]:
                update_session_status(session["folder"], current_status)
    
    # Format status for display
    status_display = current_status.replace("status-", "")
    if api_failed:
        status_display += " (?)"
    
    # Get next action (with blocked support)
    next_action = get_next_action(
        is_stale=...,  # existing logic
        is_dirty=is_dirty,
        is_vscode_running=is_running,
        blocked_label=blocked_label,
    )
```

---

## Part C: Tests

### WHERE
- `tests/cli/commands/coordinator/test_commands.py`

### TEST CASES

```python
class TestExecuteCoordinatorVscodeclaudeStatus:
    """Tests for execute_coordinator_vscodeclaude_status command."""
    
    def test_displays_current_github_status(self, monkeypatch, capsys):
        """Should display current GitHub status, not stored session status."""
        # Session has old status
        mock_sessions = {
            "sessions": [{
                "folder": "/workspace/repo_123",
                "repo": "owner/repo",
                "issue_number": 123,
                "status": "status-01:created",  # Old stored status
                "vscode_pid": None,
                "started_at": "2024-01-01T00:00:00Z",
            }],
            "last_updated": ""
        }
        
        # GitHub has new status
        mock_cached_issues = {
            "owner/repo": {
                123: {
                    "number": 123,
                    "title": "Test",
                    "state": "open",
                    "labels": ["status-04:plan-review"],  # Current status
                    "assignees": [],
                    "url": "",
                }
            }
        }
        
        # Setup monkeypatches for all dependencies
        # ...
        
        args = argparse.Namespace(repo=None)
        execute_coordinator_vscodeclaude_status(args)
        
        captured = capsys.readouterr()
        assert "04:plan-review" in captured.out  # Current status shown
        assert "01:created" not in captured.out  # Old status not shown
        
    def test_shows_question_mark_on_api_failure(self, monkeypatch, capsys):
        """Should show (?) indicator when API fails for a repo."""
        mock_sessions = {
            "sessions": [{
                "folder": "/workspace/repo_123",
                "repo": "owner/repo",
                "issue_number": 123,
                "status": "status-01:created",
                "vscode_pid": None,
                "started_at": "2024-01-01T00:00:00Z",
            }],
            "last_updated": ""
        }
        
        # Simulate API failure - empty cache for this repo
        mock_cached_issues: dict = {}  # No data = failure
        
        # Setup monkeypatches
        # Make _build_cached_issues_by_repo raise exception for this repo
        # ...
        
        args = argparse.Namespace(repo=None)
        execute_coordinator_vscodeclaude_status(args)
        
        captured = capsys.readouterr()
        assert "(?)" in captured.out  # Uncertainty indicator shown
        assert "01:created" in captured.out  # Stored status used as fallback
        
    def test_updates_session_when_status_changed(self, monkeypatch, tmp_path):
        """Should update session file when GitHub status differs."""
        sessions_file = tmp_path / "sessions.json"
        mock_sessions = {
            "sessions": [{
                "folder": "/workspace/repo_123",
                "repo": "owner/repo",
                "issue_number": 123,
                "status": "status-01:created",
                "vscode_pid": None,
                "started_at": "2024-01-01T00:00:00Z",
            }],
            "last_updated": ""
        }
        sessions_file.write_text(json.dumps(mock_sessions))
        
        mock_cached_issues = {
            "owner/repo": {
                123: {
                    "number": 123,
                    "title": "Test",
                    "state": "open",
                    "labels": ["status-04:plan-review"],
                    "assignees": [],
                    "url": "",
                }
            }
        }
        
        # Track update calls
        update_calls = []
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.update_session_status",
            lambda folder, status: update_calls.append((folder, status))
        )
        # ... other monkeypatches
        
        args = argparse.Namespace(repo=None)
        execute_coordinator_vscodeclaude_status(args)
        
        assert len(update_calls) == 1
        assert update_calls[0] == ("/workspace/repo_123", "status-04:plan-review")
        
    def test_shows_blocked_in_next_action(self, monkeypatch, capsys):
        """Should show Blocked (label) in Next Action for blocked issues."""
        mock_sessions = {
            "sessions": [{
                "folder": "/workspace/repo_123",
                "repo": "owner/repo",
                "issue_number": 123,
                "status": "status-01:created",
                "vscode_pid": None,
                "started_at": "2024-01-01T00:00:00Z",
            }],
            "last_updated": ""
        }
        
        mock_cached_issues = {
            "owner/repo": {
                123: {
                    "number": 123,
                    "title": "Test",
                    "state": "open",
                    "labels": ["status-01:created", "blocked"],  # Has blocked label
                    "assignees": [],
                    "url": "",
                }
            }
        }
        
        # Setup monkeypatches
        # ...
        
        args = argparse.Namespace(repo=None)
        execute_coordinator_vscodeclaude_status(args)
        
        captured = capsys.readouterr()
        assert "Blocked (blocked)" in captured.out
        
    def test_api_failure_only_affects_that_repo(self, monkeypatch, capsys):
        """API failure for one repo should not affect other repos."""
        mock_sessions = {
            "sessions": [
                {
                    "folder": "/workspace/repo1_123",
                    "repo": "owner/repo1",  # This repo fails
                    "issue_number": 123,
                    "status": "status-01:created",
                    "vscode_pid": None,
                    "started_at": "2024-01-01T00:00:00Z",
                },
                {
                    "folder": "/workspace/repo2_456",
                    "repo": "owner/repo2",  # This repo succeeds
                    "issue_number": 456,
                    "status": "status-01:created",
                    "vscode_pid": None,
                    "started_at": "2024-01-01T00:00:00Z",
                }
            ],
            "last_updated": ""
        }
        
        # Only repo2 has cached data
        mock_cached_issues = {
            "owner/repo2": {
                456: {
                    "number": 456,
                    "title": "Test",
                    "state": "open",
                    "labels": ["status-04:plan-review"],
                    "assignees": [],
                    "url": "",
                }
            }
        }
        
        # Setup monkeypatches
        # ...
        
        args = argparse.Namespace(repo=None)
        execute_coordinator_vscodeclaude_status(args)
        
        captured = capsys.readouterr()
        # repo1 shows (?) because API failed
        assert "(?)" in captured.out
        # repo2 shows actual status (no ?)
        lines = captured.out.split("\n")
        repo2_line = [l for l in lines if "repo2" in l][0]
        assert "(?)" not in repo2_line
        assert "04:plan-review" in repo2_line
```

---

## Verification

After implementation, run:
```bash
pytest tests/cli/commands/coordinator/test_commands.py -v -k "status"
```

All tests should pass, confirming:
1. Current GitHub status is displayed
2. `(?)` indicator shown on API failure (per-repo)
3. Session file updated when status changed
4. `Blocked (label)` shown in Next Action column
