# Step 5: Modify `restart_closed_sessions()` for Branch-Aware Restart

## LLM Prompt

```
Implement Step 5 of Issue #422 (see pr_info/steps/summary.md for full context).

Modify `restart_closed_sessions()` in orchestrator.py to use `_prepare_restart_branch()`.
This integrates the branch handling helper into the restart flow.
```

---

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/orchestrator.py` | MODIFY function |
| `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` | ADD tests |

---

## WHAT

### Modified Logic in `restart_closed_sessions()`

Add branch preparation after status eligibility check, before regenerating files.

Current flow (simplified):
```python
for session in store["sessions"]:
    # ... validation checks ...
    if not is_status_eligible_for_session(current_status):
        continue
    # ... regenerate files ...
    # ... relaunch VSCode ...
```

New flow:
```python
for session in store["sessions"]:
    # ... validation checks ...
    if not is_status_eligible_for_session(current_status):
        continue
    
    # NEW: Branch preparation
    branch_manager = IssueBranchManager(repo_url=repo_url)
    should_proceed, skip_reason, new_branch = _prepare_restart_branch(
        folder_path=folder_path,
        current_status=current_status,
        branch_manager=branch_manager,
        issue_number=issue_number,
    )
    
    if not should_proceed:
        logger.warning(
            "Skipping restart for issue #%d: %s",
            issue_number,
            skip_reason,
        )
        continue
    
    # ... regenerate files (use new_branch if set) ...
    # ... relaunch VSCode ...
```

---

## HOW

### Integration Points

1. Create `IssueBranchManager` instance (similar to `process_eligible_issues`)
2. Call `_prepare_restart_branch()` after eligibility check
3. If `skip_reason` is set, log warning and skip restart
4. If `new_branch` is set, pass to `create_status_file()` for correct branch display
5. Update `regenerate_session_files()` or create status file with new branch

---

## ALGORITHM

```python
# Inside restart_closed_sessions(), after is_status_eligible_for_session check:

# Create branch manager for this repo
branch_manager = IssueBranchManager(repo_url=repo_url)

# Prepare branch (fetch, check, switch if needed)
should_proceed, skip_reason, new_branch = _prepare_restart_branch(
    folder_path=folder_path,
    current_status=current_status,
    branch_manager=branch_manager,
    issue_number=issue_number,
)

if not should_proceed:
    logger.warning("Skipping restart for issue #%d: %s", issue_number, skip_reason)
    # Store skip_reason for potential status table display
    continue

# If branch was switched, update status file with new branch
if new_branch:
    create_status_file(
        folder_path=folder_path,
        ...,
        branch_name=new_branch,
        ...
    )

# Continue with existing regenerate and relaunch logic
regenerate_session_files(session, issue)
```

---

## DATA

### Session Restart Scenarios

| Session Status | Current Status | Linked Branch | Dirty | Result |
|----------------|----------------|---------------|-------|--------|
| `status-01` | `status-01` | any | any | Restart (fetch only) |
| `status-01` | `status-04` | `None` | - | Skip (No branch) |
| `status-01` | `status-04` | `"feat-123"` | Yes | Skip (Dirty) |
| `status-01` | `status-04` | `"feat-123"` | No | Restart + switch branch |
| `status-04` | `status-04` | `"feat-123"` | No | Restart + verify branch |
| `status-04` | `status-07` | `"feat-123"` | No | Restart + switch branch |

---

## TEST IMPLEMENTATION

### File: `tests/workflows/vscodeclaude/test_orchestrator_sessions.py`

Add tests to existing class or new class:

```python
class TestRestartClosedSessionsBranchHandling:
    """Tests for branch handling in restart_closed_sessions()."""

    def test_restart_runs_git_fetch_for_status_01(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """Status-01 restart runs git fetch origin."""
        # Setup session
        session: VSCodeClaudeSession = {
            "folder": str(tmp_path),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-01:created",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        
        # Mock dependencies
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.load_sessions",
            return_value={"sessions": [session], "last_updated": ""},
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            return_value=False,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_window_open_for_folder",
            return_value=False,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_open_for_folder",
            return_value=(False, None),
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos",
            return_value={"owner/repo"},
        )
        mock_prepare = mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator._prepare_restart_branch",
            return_value=(True, None, None),
        )
        # ... more mocks for issue fetch, regenerate, launch ...
        
        restart_closed_sessions({})
        
        # Verify _prepare_restart_branch was called
        mock_prepare.assert_called_once()

    def test_restart_skips_status_04_without_branch(
        self, tmp_path: Path, mocker: MockerFixture, caplog
    ) -> None:
        """Status-04 without linked branch skips restart."""
        session: VSCodeClaudeSession = {
            "folder": str(tmp_path),
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-04:plan-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.load_sessions",
            return_value={"sessions": [session], "last_updated": ""},
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running",
            return_value=False,
        )
        # ... setup mocks ...
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator._prepare_restart_branch",
            return_value=(False, "No branch", None),
        )
        mock_launch = mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode"
        )
        
        with caplog.at_level(logging.WARNING):
            restart_closed_sessions({})
        
        # VSCode should NOT be launched
        mock_launch.assert_not_called()
        assert "No branch" in caplog.text

    def test_restart_skips_dirty_repo(
        self, tmp_path: Path, mocker: MockerFixture, caplog
    ) -> None:
        """Dirty repo skips restart with Dirty reason."""
        session: VSCodeClaudeSession = {
            "folder": str(tmp_path),
            "repo": "owner/repo",
            "issue_number": 789,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        
        # ... setup mocks ...
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator._prepare_restart_branch",
            return_value=(False, "Dirty", None),
        )
        mock_launch = mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode"
        )
        
        with caplog.at_level(logging.WARNING):
            restart_closed_sessions({})
        
        mock_launch.assert_not_called()
        assert "Dirty" in caplog.text

    def test_restart_switches_branch_on_status_change(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """Status change from 01 to 04 switches branch."""
        session: VSCodeClaudeSession = {
            "folder": str(tmp_path),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-01:created",  # Session recorded at status-01
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        
        # Issue is now at status-04
        mock_issue: IssueData = {
            "number": 123,
            "title": "Test",
            "labels": ["status-04:plan-review"],
            "assignees": [],
            "state": "open",
            "url": "",
        }
        
        # ... setup mocks to return issue at status-04 ...
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator._prepare_restart_branch",
            return_value=(True, None, "feat-123"),  # Branch switched
        )
        mock_create_status = mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.create_status_file"
        )
        
        restart_closed_sessions({})
        
        # Status file should be created with new branch
        mock_create_status.assert_called()
        call_kwargs = mock_create_status.call_args.kwargs
        assert call_kwargs["branch_name"] == "feat-123"

    def test_intervention_session_follows_same_rules(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """Intervention sessions follow same branch rules."""
        session: VSCodeClaudeSession = {
            "folder": str(tmp_path),
            "repo": "owner/repo",
            "issue_number": 999,
            "status": "status-04:plan-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": True,  # Intervention session
        }
        
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator._prepare_restart_branch",
            return_value=(False, "No branch", None),
        )
        mock_launch = mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode"
        )
        
        restart_closed_sessions({})
        
        # Should skip even for intervention
        mock_launch.assert_not_called()
```

---

## VERIFICATION

After implementation, run:

```bash
pytest tests/workflows/vscodeclaude/test_orchestrator_sessions.py::TestRestartClosedSessionsBranchHandling -v
```

All 5 tests should pass.
