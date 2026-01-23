# Step 5: Workspace Setup

## LLM Prompt

```
Implement Step 5 of the coordinator vscodeclaude feature.
Reference: pr_info/steps/summary.md for overall architecture.
This step: Working folder creation, git operations, file generation.
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py` | Add workspace setup functions |
| `tests/cli/commands/coordinator/test_vscodeclaude.py` | Add workspace tests |

## WHAT

### vscodeclaude.py - Workspace Functions

```python
import subprocess
import platform
from pathlib import Path

def get_working_folder_path(
    workspace_base: str,
    repo_name: str,
    issue_number: int,
) -> Path:
    """Get full path for working folder.
    
    Args:
        workspace_base: Base directory from config
        repo_name: Repository short name (sanitized)
        issue_number: GitHub issue number
        
    Returns:
        Path like: workspace_base/mcp-coder_123
    """

def create_working_folder(folder_path: Path) -> bool:
    """Create working folder if it doesn't exist.
    
    Args:
        folder_path: Full path to create
        
    Returns:
        True if created, False if already existed
    """

def setup_git_repo(
    folder_path: Path,
    repo_url: str,
    branch_name: Optional[str],
) -> None:
    """Clone repo or checkout branch and pull.
    
    Args:
        folder_path: Working folder path
        repo_url: Git clone URL
        branch_name: Branch to checkout (None = use main)
        
    Steps:
    1. If folder empty: git clone
    2. If folder has .git: checkout branch, pull
    3. Uses system git credentials
    
    Raises:
        subprocess.CalledProcessError: If git command fails
    """

def validate_mcp_json(folder_path: Path) -> None:
    """Validate .mcp.json exists in repo.
    
    Args:
        folder_path: Working folder path
        
    Raises:
        FileNotFoundError: If .mcp.json missing
    """

def run_setup_commands(
    folder_path: Path,
    commands: List[str],
) -> None:
    """Run platform-specific setup commands.
    
    Args:
        folder_path: Working directory for commands
        commands: List of shell commands to run
        
    Raises:
        subprocess.CalledProcessError: If any command fails
    """

def update_gitignore(folder_path: Path) -> None:
    """Append vscodeclaude entries to .gitignore.
    
    Args:
        folder_path: Working folder path
        
    Idempotent: won't duplicate entries.
    """

def create_workspace_file(
    workspace_base: str,
    folder_name: str,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_name: str,
) -> Path:
    """Create .code-workspace file in workspace_base.
    
    Args:
        workspace_base: Base directory for workspace files
        folder_name: Working folder name (e.g., "mcp-coder_123")
        issue_number: GitHub issue number
        issue_title: Issue title for window title
        status: Status label for window title
        repo_name: Repo short name for window title
        
    Returns:
        Path to created workspace file
    """

def create_startup_script(
    folder_path: Path,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_name: str,
    is_intervention: bool,
) -> Path:
    """Create platform-specific startup script.
    
    Args:
        folder_path: Working folder path
        issue_number: GitHub issue number
        issue_title: Issue title for banner
        status: Status label
        repo_name: Repo short name
        is_intervention: If True, use intervention mode (no automation)
        
    Returns:
        Path to created script (.bat or .sh)
    """

def create_vscode_task(folder_path: Path, script_path: Path) -> None:
    """Create .vscode/tasks.json with runOn: folderOpen.
    
    Args:
        folder_path: Working folder path
        script_path: Path to startup script
    """

def create_status_file(
    folder_path: Path,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_full_name: str,
    branch_name: str,
    issue_url: str,
    is_intervention: bool,
) -> None:
    """Create .vscodeclaude_status.md in project root.
    
    Args:
        folder_path: Working folder path
        issue_number: GitHub issue number
        issue_title: Issue title
        status: Status label
        repo_full_name: Full repo name (owner/repo)
        branch_name: Git branch name
        issue_url: GitHub issue URL
        is_intervention: If True, add intervention warning
    """
```

## HOW

### Integration Points

1. Uses `subprocess.run()` for git commands (system credentials)
2. Uses templates from `vscodeclaude_templates.py`
3. Platform detection via `platform.system()`
4. Existing `HUMAN_ACTION_COMMANDS` for slash command mapping

### Git Operations

```python
def setup_git_repo(folder_path: Path, repo_url: str, branch_name: Optional[str]) -> None:
    is_empty = not any(folder_path.iterdir()) if folder_path.exists() else True
    
    if is_empty:
        # Clone into folder
        subprocess.run(
            ["git", "clone", repo_url, str(folder_path)],
            check=True, capture_output=True, text=True
        )
    
    # Checkout and pull
    branch = branch_name or "main"
    subprocess.run(
        ["git", "checkout", branch],
        cwd=folder_path, check=True, capture_output=True, text=True
    )
    subprocess.run(
        ["git", "pull"],
        cwd=folder_path, check=True, capture_output=True, text=True
    )
```

## ALGORITHM

### create_workspace_file()
```
1. Build folder_path relative to workspace_base
2. Format WORKSPACE_FILE_TEMPLATE with:
   - folder_path (relative)
   - window title: [#123 review] Title - repo
3. Write to workspace_base/{folder_name}.code-workspace
4. Return path
```

### create_startup_script()
```
1. Determine platform (Windows/Linux)
2. Get initial_command, followup_command from HUMAN_ACTION_COMMANDS
3. If intervention: use INTERVENTION_SECTION template
4. Else: format AUTOMATED_SECTION and INTERACTIVE_SECTION
5. Format main script template with all sections
6. Write to folder_path/.vscodeclaude_start.{bat|sh}
7. On Linux: chmod +x
8. Return script path
```

### update_gitignore()
```
1. Read existing .gitignore (or empty string)
2. Check if ".vscodeclaude_status.md" already present
3. If not: append GITIGNORE_ENTRY
4. Write back to .gitignore
```

## DATA

### File Locations

| File | Location |
|------|----------|
| Working folder | `{workspace_base}/{repo}_{issue}` |
| Workspace file | `{workspace_base}/{repo}_{issue}.code-workspace` |
| Startup script | `{folder}/.vscodeclaude_start.{bat\|sh}` |
| Tasks file | `{folder}/.vscode/tasks.json` |
| Status file | `{folder}/.vscodeclaude_status.md` |

### Test Coverage

```python
# test_vscodeclaude.py

class TestWorkspaceSetup:
    """Test workspace creation and setup."""
    
    def test_get_working_folder_path(self):
        """Constructs correct folder path."""
        path = get_working_folder_path(
            workspace_base="/home/user/projects",
            repo_name="mcp-coder",
            issue_number=123
        )
        assert str(path).endswith("mcp-coder_123")
    
    def test_create_working_folder_new(self, tmp_path):
        """Creates folder when doesn't exist."""
        folder = tmp_path / "new_folder"
        result = create_working_folder(folder)
        assert result is True
        assert folder.exists()
    
    def test_create_working_folder_exists(self, tmp_path):
        """Returns False when folder exists."""
        folder = tmp_path / "existing"
        folder.mkdir()
        result = create_working_folder(folder)
        assert result is False
    
    def test_validate_mcp_json_exists(self, tmp_path):
        """Passes when .mcp.json exists."""
        (tmp_path / ".mcp.json").write_text("{}")
        validate_mcp_json(tmp_path)  # Should not raise
    
    def test_validate_mcp_json_missing(self, tmp_path):
        """Raises when .mcp.json missing."""
        with pytest.raises(FileNotFoundError, match=".mcp.json"):
            validate_mcp_json(tmp_path)
    
    def test_run_setup_commands_success(self, tmp_path, monkeypatch):
        """Runs commands in correct directory."""
        commands_run = []
        
        def mock_run(cmd, **kwargs):
            commands_run.append((cmd, kwargs.get("cwd")))
            return Mock(returncode=0)
        
        monkeypatch.setattr("subprocess.run", mock_run)
        
        run_setup_commands(tmp_path, ["echo hello", "echo world"])
        
        assert len(commands_run) == 2
        assert all(cwd == tmp_path for _, cwd in commands_run)
    
    def test_run_setup_commands_failure_aborts(self, tmp_path, monkeypatch):
        """Raises on command failure."""
        def mock_run(cmd, **kwargs):
            raise subprocess.CalledProcessError(1, cmd)
        
        monkeypatch.setattr("subprocess.run", mock_run)
        
        with pytest.raises(subprocess.CalledProcessError):
            run_setup_commands(tmp_path, ["failing_command"])
    
    def test_update_gitignore_adds_entry(self, tmp_path):
        """Adds vscodeclaude entry to .gitignore."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")
        
        update_gitignore(tmp_path)
        
        content = gitignore.read_text()
        assert ".vscodeclaude_status.md" in content
        assert "*.pyc" in content  # Preserves existing
    
    def test_update_gitignore_idempotent(self, tmp_path):
        """Doesn't duplicate entry on second call."""
        gitignore = tmp_path / ".gitignore"
        
        update_gitignore(tmp_path)
        update_gitignore(tmp_path)
        
        content = gitignore.read_text()
        assert content.count(".vscodeclaude_status.md") == 1
    
    def test_create_workspace_file(self, tmp_path):
        """Creates valid workspace JSON file."""
        workspace_path = create_workspace_file(
            workspace_base=str(tmp_path),
            folder_name="mcp-coder_123",
            issue_number=123,
            issue_title="Add feature",
            status="status-07:code-review",
            repo_name="mcp-coder"
        )
        
        assert workspace_path.exists()
        assert workspace_path.suffix == ".code-workspace"
        
        import json
        content = json.loads(workspace_path.read_text())
        assert "folders" in content
        assert "settings" in content
        assert "#123" in content["settings"]["window.title"]
    
    def test_create_startup_script_windows(self, tmp_path, monkeypatch):
        """Creates .bat script on Windows."""
        monkeypatch.setattr("platform.system", lambda: "Windows")
        
        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            is_intervention=False
        )
        
        assert script_path.suffix == ".bat"
        assert script_path.exists()
        content = script_path.read_text()
        assert "claude" in content
        assert "/implementation_review" in content
    
    def test_create_startup_script_linux(self, tmp_path, monkeypatch):
        """Creates .sh script on Linux."""
        monkeypatch.setattr("platform.system", lambda: "Linux")
        
        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            is_intervention=False
        )
        
        assert script_path.suffix == ".sh"
        assert script_path.exists()
    
    def test_create_startup_script_intervention(self, tmp_path, monkeypatch):
        """Intervention mode uses plain claude command."""
        monkeypatch.setattr("platform.system", lambda: "Windows")
        
        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-06:implementing",  # bot_busy status
            repo_name="test-repo",
            is_intervention=True
        )
        
        content = script_path.read_text()
        assert "INTERVENTION" in content
        assert "/implementation_review" not in content
    
    def test_create_vscode_task(self, tmp_path):
        """Creates tasks.json with runOn: folderOpen."""
        script_path = tmp_path / ".vscodeclaude_start.bat"
        script_path.touch()
        
        create_vscode_task(tmp_path, script_path)
        
        tasks_file = tmp_path / ".vscode" / "tasks.json"
        assert tasks_file.exists()
        
        import json
        content = json.loads(tasks_file.read_text())
        assert content["tasks"][0]["runOptions"]["runOn"] == "folderOpen"
    
    def test_create_status_file(self, tmp_path):
        """Creates status markdown file."""
        create_status_file(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Add feature",
            status="status-07:code-review",
            repo_full_name="owner/repo",
            branch_name="feature-123",
            issue_url="https://github.com/owner/repo/issues/123",
            is_intervention=False
        )
        
        status_file = tmp_path / ".vscodeclaude_status.md"
        assert status_file.exists()
        
        content = status_file.read_text()
        assert "#123" in content
        assert "Add feature" in content
        assert "code-review" in content


class TestGitOperations:
    """Test git clone/checkout/pull operations."""
    
    def test_setup_git_repo_clone_new(self, tmp_path, monkeypatch):
        """Clones when folder is empty."""
        commands = []
        
        def mock_run(cmd, **kwargs):
            commands.append(cmd)
            return Mock(returncode=0)
        
        monkeypatch.setattr("subprocess.run", mock_run)
        
        folder = tmp_path / "new_repo"
        folder.mkdir()
        
        setup_git_repo(folder, "https://github.com/owner/repo.git", "main")
        
        # Should have clone, checkout, pull
        assert any("clone" in str(c) for c in commands)
    
    def test_setup_git_repo_existing(self, tmp_path, monkeypatch):
        """Checkout and pull when .git exists."""
        commands = []
        
        def mock_run(cmd, **kwargs):
            commands.append(cmd)
            return Mock(returncode=0)
        
        monkeypatch.setattr("subprocess.run", mock_run)
        
        # Create folder with .git
        folder = tmp_path / "existing_repo"
        folder.mkdir()
        (folder / ".git").mkdir()
        
        setup_git_repo(folder, "https://github.com/owner/repo.git", "feature-branch")
        
        # Should NOT clone, but should checkout and pull
        assert not any("clone" in str(c) for c in commands)
        assert any("checkout" in str(c) for c in commands)
        assert any("pull" in str(c) for c in commands)
    
    def test_setup_git_repo_uses_main_default(self, tmp_path, monkeypatch):
        """Uses main branch when branch_name is None."""
        commands = []
        
        def mock_run(cmd, **kwargs):
            commands.append(cmd)
            return Mock(returncode=0)
        
        monkeypatch.setattr("subprocess.run", mock_run)
        
        folder = tmp_path / "repo"
        folder.mkdir()
        (folder / ".git").mkdir()
        
        setup_git_repo(folder, "https://github.com/owner/repo.git", None)
        
        checkout_cmd = [c for c in commands if "checkout" in str(c)][0]
        assert "main" in checkout_cmd
```

## Verification

```bash
# Run workspace setup tests
pytest tests/cli/commands/coordinator/test_vscodeclaude.py::TestWorkspaceSetup -v
pytest tests/cli/commands/coordinator/test_vscodeclaude.py::TestGitOperations -v

# Type check
mypy src/mcp_coder/cli/commands/coordinator/vscodeclaude.py
```
