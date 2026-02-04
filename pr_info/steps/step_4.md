# Step 4: Fix Cleanup Order and Include Blocked Sessions

## LLM Prompt

```
Implement Step 4 of Issue #400 (see pr_info/steps/summary.md for context).

This step fixes the cleanup/restart order in vscodeclaude command and includes blocked sessions in cleanup.

Follow TDD: Write tests first, then implement the functionality.
```

## Overview

1. Reorder operations in `execute_coordinator_vscodeclaude()` - cleanup before restart
2. Modify `get_stale_sessions()` in cleanup.py to also return blocked sessions

---

## Part A: Reorder Cleanup and Restart in commands.py

### WHERE
- `src/mcp_coder/cli/commands/coordinator/commands.py`

### WHAT

Change the order of operations in `execute_coordinator_vscodeclaude()`:

**Current order (wrong):**
```python
# Step 1: Restart closed sessions
restarted = restart_closed_sessions(cached_issues_by_repo=cached_issues_by_repo)

# Step 2: Handle cleanup if requested
if args.cleanup:
    cleanup_stale_sessions(dry_run=False)
```

**New order (correct):**
```python
# Step 1: Handle cleanup (BEFORE restart)
# - Always runs: dry_run=True shows what would be cleaned, dry_run=False actually deletes
# - This ensures users always see what's cleanable (Decision #1)
if args.cleanup:
    cleanup_stale_sessions(dry_run=False, cached_issues_by_repo=cached_issues_by_repo)
else:
    cleanup_stale_sessions(dry_run=True, cached_issues_by_repo=cached_issues_by_repo)

# Step 2: Restart closed sessions
restarted = restart_closed_sessions(cached_issues_by_repo=cached_issues_by_repo)
```

**Note:** Cleanup always runs - in dry-run mode when `--cleanup` is not passed. This shows actionable messages like `Add --cleanup to delete: XYZ` so users know what would be cleaned up (see Decision #1).

### HOW
- Move the cleanup block before restart_closed_sessions() call
- Pass `cached_issues_by_repo` to `cleanup_stale_sessions()` for blocked detection
- No new imports needed

---

## Part B: Update cleanup_stale_sessions() to Accept Cache

### WHERE
- `src/mcp_coder/workflows/vscodeclaude/cleanup.py`

### WHAT

Update function signature to accept cache:

```python
def cleanup_stale_sessions(
    dry_run: bool = True,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> dict[str, list[str]]:
```

And pass it to `get_stale_sessions()`.

---

## Part C: Update get_stale_sessions() to Include Blocked Sessions

### WHERE
- `src/mcp_coder/workflows/vscodeclaude/cleanup.py`

### WHAT

Modify `get_stale_sessions()` to also return sessions for issues with ignore labels (blocked/wait).

**Current signature:**
```python
def get_stale_sessions() -> list[tuple[VSCodeClaudeSession, bool]]:
```

**New signature:**
```python
def get_stale_sessions(
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> list[tuple[VSCodeClaudeSession, bool]]:
```

### HOW
- Add import: `from .issues import get_ignore_labels, get_matching_ignore_label`
- Add import for IssueData type: `from ...utils.github_operations.issue_manager import IssueData`
- Check for ignore labels in addition to staleness check

### ALGORITHM

```
1. Load sessions and configured repos
2. Load ignore_labels using get_ignore_labels()
3. For each session (skip if running or unconfigured):
4.   Get issue from cache or skip if unavailable
5.   Check if stale OR has ignore label
6.   If either, add to stale_sessions with dirty status
7. Return list of (session, is_dirty) tuples
```

### DATA

**Returns same type but includes blocked sessions:**
```python
[
    (session_stale, False),      # Stale session, clean
    (session_blocked, False),    # Blocked session, clean  
    (session_blocked_dirty, True),  # Blocked session, dirty
]
```

---

## Part D: Tests

### WHERE
- `tests/workflows/vscodeclaude/test_cleanup.py`
- `tests/cli/commands/coordinator/test_commands.py`

### TEST CASES for cleanup.py

```python
class TestGetStaleSessions:
    """Tests for get_stale_sessions function."""
    
    def test_includes_blocked_sessions(self, monkeypatch):
        """Should include sessions with blocked label."""
        # Setup: Session for issue with "blocked" label
        mock_sessions = {
            "sessions": [{
                "folder": "/workspace/repo_123",
                "repo": "owner/repo",
                "issue_number": 123,
                "status": "status-01:created",
                "vscode_pid": None,  # Not running
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
        
        # Monkeypatch load_sessions, check_vscode_running, _get_configured_repos
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.load_sessions",
            lambda: mock_sessions
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.check_vscode_running",
            lambda pid: False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"}
        )
        
        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)
        
        assert len(result) == 1
        session, is_dirty = result[0]
        assert session["issue_number"] == 123
        
    def test_includes_wait_labeled_sessions(self, monkeypatch):
        """Should include sessions with wait label."""
        mock_sessions = {
            "sessions": [{
                "folder": "/workspace/repo_456",
                "repo": "owner/repo",
                "issue_number": 456,
                "status": "status-04:plan-review",
                "vscode_pid": None,
                "started_at": "2024-01-01T00:00:00Z",
            }],
            "last_updated": ""
        }
        
        mock_cached_issues = {
            "owner/repo": {
                456: {
                    "number": 456,
                    "title": "Test",
                    "state": "open",
                    "labels": ["status-04:plan-review", "wait"],  # Has wait label
                    "assignees": [],
                    "url": "",
                }
            }
        }
        
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.load_sessions",
            lambda: mock_sessions
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.check_vscode_running",
            lambda pid: False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"}
        )
        
        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)
        
        assert len(result) == 1
        
    def test_case_insensitive_blocked_detection(self, monkeypatch):
        """Should detect BLOCKED label case-insensitively."""
        mock_sessions = {
            "sessions": [{
                "folder": "/workspace/repo_789",
                "repo": "owner/repo",
                "issue_number": 789,
                "status": "status-01:created",
                "vscode_pid": None,
                "started_at": "2024-01-01T00:00:00Z",
            }],
            "last_updated": ""
        }
        
        mock_cached_issues = {
            "owner/repo": {
                789: {
                    "number": 789,
                    "title": "Test",
                    "state": "open",
                    "labels": ["status-01:created", "BLOCKED"],  # Uppercase
                    "assignees": [],
                    "url": "",
                }
            }
        }
        
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.load_sessions",
            lambda: mock_sessions
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.check_vscode_running",
            lambda pid: False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"}
        )
        
        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)
        
        assert len(result) == 1
        
    def test_excludes_running_blocked_sessions(self, monkeypatch):
        """Should not include blocked sessions with running VSCode."""
        mock_sessions = {
            "sessions": [{
                "folder": "/workspace/repo_123",
                "repo": "owner/repo",
                "issue_number": 123,
                "status": "status-01:created",
                "vscode_pid": 1234,  # Running
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
                    "labels": ["status-01:created", "blocked"],
                    "assignees": [],
                    "url": "",
                }
            }
        }
        
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.load_sessions",
            lambda: mock_sessions
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.check_vscode_running",
            lambda pid: True  # Running
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"}
        )
        
        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)
        
        assert len(result) == 0  # Excluded because running
```

---

## Part E: Update Dry-run Message Format in cleanup_stale_sessions()

### WHERE
- `src/mcp_coder/workflows/vscodeclaude/cleanup.py`

### WHAT

Change dry-run output to be actionable and skip dirty folders:

**Current (in cleanup_stale_sessions):**
```python
if dry_run:
    print(f"Would delete: {folder}")
```

**New:**
```python
if dry_run:
    print(f"Add --cleanup to delete: {folder}")
```

Also, in dry-run mode, skip printing dirty folders (they can't be auto-cleaned anyway).

---

## Verification

After implementation, run:
```bash
pytest tests/workflows/vscodeclaude/test_cleanup.py -v
pytest tests/cli/commands/coordinator/test_commands.py -v -k "vscodeclaude"
```

All tests should pass, confirming:
1. Cleanup runs before restart
2. Blocked sessions are included in cleanup candidates
3. Case-insensitive label matching works
4. Running sessions are excluded from cleanup
