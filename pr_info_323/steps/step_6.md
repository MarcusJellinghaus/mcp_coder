# Step 6: VSCode Launch & Session Orchestration

## LLM Prompt

```
Implement Step 6 of the coordinator vscodeclaude feature.
Reference: pr_info/steps/summary.md for overall architecture.
This step: VSCode launch, session preparation, main orchestration.
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py` | Add launch and orchestration functions |
| `tests/cli/commands/coordinator/test_vscodeclaude.py` | Add launch tests |

## WHAT

### vscodeclaude.py - Launch Functions

```python
def launch_vscode(workspace_file: Path) -> int:
    """Launch VSCode with workspace file.
    
    Args:
        workspace_file: Path to .code-workspace file
        
    Returns:
        VSCode process PID
        
    Uses subprocess.Popen for non-blocking launch.
    """

def get_stage_display_name(status: str) -> str:
    """Get human-readable stage name for display.
    
    Args:
        status: Status label (e.g., "status-07:code-review")
        
    Returns:
        Display name (e.g., "CODE REVIEW")
    """

def truncate_title(title: str, max_length: int = 50) -> str:
    """Truncate title for display, adding ellipsis if needed.
    
    Args:
        title: Original title
        max_length: Maximum length
        
    Returns:
        Truncated title with "..." if needed
    """
```

### vscodeclaude.py - Main Orchestration

```python
def prepare_and_launch_session(
    issue: IssueData,
    repo_config: dict[str, str],
    vscodeclaude_config: VSCodeClaudeConfig,
    repo_vscodeclaude_config: RepoVSCodeClaudeConfig,
    branch_name: Optional[str],
    is_intervention: bool = False,
) -> VSCodeClaudeSession:
    """Full session preparation and launch.
    
    Args:
        issue: GitHub issue data
        repo_config: Repository config (repo_url, etc.)
        vscodeclaude_config: VSCodeClaude config (workspace_base, etc.)
        repo_vscodeclaude_config: Per-repo setup commands
        branch_name: Branch to checkout (None = main)
        is_intervention: If True, intervention mode
        
    Returns:
        Created session data
        
    Raises:
        FileNotFoundError: If .mcp.json missing
        subprocess.CalledProcessError: If git or setup fails
        
    Steps:
    1. Create working folder
    2. Setup git repo
    3. Validate .mcp.json
    4. Run setup commands (if configured) - validates commands first
    5. Update .gitignore
    6. Create workspace file
    7. Create startup script
    8. Create VSCode task
    9. Create status file
    10. Launch VSCode
    11. Create and save session
    
    On failure after folder creation: cleans up working folder.
    """

def process_eligible_issues(
    repo_name: str,
    repo_config: dict[str, str],
    vscodeclaude_config: VSCodeClaudeConfig,
    max_sessions: int,
    repo_filter: Optional[str] = None,
) -> List[VSCodeClaudeSession]:
    """Process eligible issues for a repository.
    
    Args:
        repo_name: Repository config name
        repo_config: Repository config
        vscodeclaude_config: VSCodeClaude config
        max_sessions: Maximum concurrent sessions
        repo_filter: Optional repo filter (skip if doesn't match)
        
    Returns:
        List of sessions that were started
        
    Handles:
    - Checking current session count
    - Getting eligible issues
    - Skipping issues with existing sessions
    - Starting new sessions up to max
    """

def restart_closed_sessions() -> List[VSCodeClaudeSession]:
    """Restart sessions where VSCode was closed.
    
    Finds sessions where:
    - VSCode PID no longer running
    - Issue status unchanged (not stale)
    - Folder still exists
    
    Returns:
        List of restarted sessions
    """

def handle_pr_created_issues(
    issues: List[IssueData],
    issue_manager: IssueManager,
) -> None:
    """Display PR URLs for status-10:pr-created issues.
    
    Args:
        issues: Issues with status-10:pr-created
        issue_manager: IssueManager for PR lookup
        
    Prints PR URLs to stdout (no session created).
    """
```

## HOW

### Integration Points

1. `subprocess.Popen` for non-blocking VSCode launch
2. All workspace functions from Step 5
3. Session management from Step 3
4. Issue selection from Step 4
5. GitHub managers from coordinator package

### VSCode Launch

```python
def launch_vscode(workspace_file: Path) -> int:
    process = subprocess.Popen(
        ["code", str(workspace_file)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return process.pid
```

## ALGORITHM

### prepare_and_launch_session()
```
1. Build folder path: workspace_base/{repo}_{issue_number}
2. create_working_folder(folder_path)
3. try:
4.   setup_git_repo(folder_path, repo_url, branch_name)
5.   validate_mcp_json(folder_path)
6.   If setup_commands: validate_setup_commands(), then run_setup_commands()
7.   update_gitignore(folder_path)
8.   workspace_file = create_workspace_file(...)
9.   script_path = create_startup_script(...)
10.  create_vscode_task(folder_path, script_path)
11.  create_status_file(...)
12.  pid = launch_vscode(workspace_file)
13.  session = build_session_dict(folder, issue, pid, ...)
14.  add_session(session)
15.  Return session
16. except Exception:
17.   # Cleanup working folder on failure
18.   shutil.rmtree(folder_path, ignore_errors=True)
19.   raise
```

### process_eligible_issues()
```
1. current_count = get_active_session_count()
2. If current_count >= max_sessions: return []
3. Get github_username
4. Create issue_manager, branch_manager
5. eligible = get_eligible_vscodeclaude_issues(issue_manager, username)
6. Filter out issues that already have sessions
7. Separate pr-created issues (handle separately)
8. For each issue (up to max_sessions - current_count):
   - Get linked branch
   - Get status from labels
   - prepare_and_launch_session(...)
   - Add to started list
9. handle_pr_created_issues(pr_issues)
10. Return started sessions
```

### restart_closed_sessions()
```
1. Load all sessions
2. For each session:
   - If vscode_pid still running: skip
   - If folder doesn't exist: remove session, skip
   - Check current issue status
   - If status changed: mark stale, skip
   - Else: relaunch via prepare_and_launch_session
3. Return restarted sessions
```

## DATA

### Session Creation

```python
def _build_session(
    folder: str,
    repo: str,
    issue_number: int,
    status: str,
    vscode_pid: int,
    is_intervention: bool,
) -> VSCodeClaudeSession:
    return {
        "folder": folder,
        "repo": repo,
        "issue_number": issue_number,
        "status": status,
        "vscode_pid": vscode_pid,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "is_intervention": is_intervention,
    }
```

### Stage Display Names

```python
STAGE_DISPLAY_NAMES = {
    "status-01:created": "ISSUE ANALYSIS",
    "status-04:plan-review": "PLAN REVIEW",
    "status-07:code-review": "CODE REVIEW",
    "status-10:pr-created": "PR CREATED",
}
```

### Test Coverage

```python
# test_vscodeclaude.py

class TestLaunch:
    """Test VSCode launch functions."""
    
    def test_launch_vscode_returns_pid(self, tmp_path, monkeypatch):
        """Returns PID from Popen."""
        mock_process = Mock()
        mock_process.pid = 12345
        
        monkeypatch.setattr(
            "subprocess.Popen",
            lambda *args, **kwargs: mock_process
        )
        
        workspace = tmp_path / "test.code-workspace"
        workspace.touch()
        
        pid = launch_vscode(workspace)
        assert pid == 12345
    
    def test_launch_vscode_uses_code_command(self, tmp_path, monkeypatch):
        """Calls 'code' with workspace path."""
        called_args = []
        
        def mock_popen(args, **kwargs):
            called_args.extend(args)
            return Mock(pid=1)
        
        monkeypatch.setattr("subprocess.Popen", mock_popen)
        
        workspace = tmp_path / "test.code-workspace"
        workspace.touch()
        
        launch_vscode(workspace)
        
        assert "code" in called_args
        assert str(workspace) in called_args
    
    def test_get_stage_display_name(self):
        """Returns human-readable stage names."""
        assert get_stage_display_name("status-07:code-review") == "CODE REVIEW"
        assert get_stage_display_name("status-04:plan-review") == "PLAN REVIEW"
        assert get_stage_display_name("status-01:created") == "ISSUE ANALYSIS"
    
    def test_truncate_title_short(self):
        """Returns unchanged if under max length."""
        assert truncate_title("Short title", 50) == "Short title"
    
    def test_truncate_title_long(self):
        """Truncates with ellipsis if over max."""
        long_title = "A" * 100
        result = truncate_title(long_title, 50)
        assert len(result) == 50
        assert result.endswith("...")


class TestOrchestration:
    """Test main orchestration functions."""
    
    def test_prepare_and_launch_session_success(self, tmp_path, monkeypatch):
        """Creates session with all components."""
        # Mock all dependencies
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.create_working_folder",
            lambda p: True
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.setup_git_repo",
            lambda *args: None
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.validate_mcp_json",
            lambda p: None
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.update_gitignore",
            lambda p: None
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.create_workspace_file",
            lambda *args, **kwargs: tmp_path / "test.code-workspace"
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.create_startup_script",
            lambda *args, **kwargs: tmp_path / ".vscodeclaude_start.bat"
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.create_vscode_task",
            lambda *args: None
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.create_status_file",
            lambda *args, **kwargs: None
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.launch_vscode",
            lambda p: 9999
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.add_session",
            lambda s: None
        )
        
        issue = {
            "number": 123,
            "title": "Test issue",
            "labels": ["status-07:code-review"],
            "url": "https://github.com/owner/repo/issues/123",
        }
        
        repo_config = {
            "repo_url": "https://github.com/owner/repo.git",
        }
        
        vscodeclaude_config = {
            "workspace_base": str(tmp_path),
            "max_sessions": 3,
        }
        
        session = prepare_and_launch_session(
            issue=issue,
            repo_config=repo_config,
            vscodeclaude_config=vscodeclaude_config,
            repo_vscodeclaude_config={},
            branch_name="main",
            is_intervention=False,
        )
        
        assert session["issue_number"] == 123
        assert session["vscode_pid"] == 9999
        assert session["is_intervention"] is False
    
    def test_prepare_and_launch_aborts_on_setup_failure(self, tmp_path, monkeypatch):
        """Aborts session and cleans up folder if setup commands fail."""
        folder_path = tmp_path / "test_123"
        
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.create_working_folder",
            lambda p: True
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.setup_git_repo",
            lambda *args: None
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.validate_mcp_json",
            lambda p: None
        )
        
        # Create folder to verify cleanup
        folder_path.mkdir()
        assert folder_path.exists()
        
        def failing_setup(*args):
            raise subprocess.CalledProcessError(1, "uv sync")
        
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.run_setup_commands",
            failing_setup
        )
        
        issue = {"number": 123, "title": "Test", "labels": ["status-07:code-review"], "url": "..."}
        repo_config = {"repo_url": "https://github.com/owner/repo.git"}
        vscodeclaude_config = {"workspace_base": str(tmp_path), "max_sessions": 3}
        repo_vscodeclaude_config = {"setup_commands_windows": ["uv sync"]}
        
        with pytest.raises(subprocess.CalledProcessError):
            prepare_and_launch_session(
                issue=issue,
                repo_config=repo_config,
                vscodeclaude_config=vscodeclaude_config,
                repo_vscodeclaude_config=repo_vscodeclaude_config,
                branch_name="main",
                is_intervention=False,
            )
        
        # Folder should be cleaned up on failure
        assert not folder_path.exists()
    
    def test_process_eligible_issues_respects_max_sessions(self, monkeypatch):
        """Doesn't start sessions beyond max."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_active_session_count",
            lambda: 2
        )
        
        # Should return empty since already at/above max
        sessions = process_eligible_issues(
            repo_name="test",
            repo_config={"repo_url": "..."},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 2},
            max_sessions=2,
        )
        
        assert sessions == []
    
    def test_handle_pr_created_issues_prints_url(self, capsys, monkeypatch):
        """Prints PR URL for pr-created issues."""
        mock_issue_manager = Mock()
        
        # Mock getting PR for issue
        mock_pr = Mock()
        mock_pr.html_url = "https://github.com/owner/repo/pull/456"
        mock_issue_manager.repo.get_pull.return_value = mock_pr
        
        issues = [
            {"number": 123, "title": "Test", "labels": ["status-10:pr-created"]},
        ]
        
        handle_pr_created_issues(issues, mock_issue_manager)
        
        captured = capsys.readouterr()
        # Should print something about PR
        assert "#123" in captured.out or "PR" in captured.out
```

## Verification

```bash
# Run launch tests
pytest tests/cli/commands/coordinator/test_vscodeclaude.py::TestLaunch -v

# Run orchestration tests
pytest tests/cli/commands/coordinator/test_vscodeclaude.py::TestOrchestration -v

# Type check
mypy src/mcp_coder/cli/commands/coordinator/vscodeclaude.py
```
