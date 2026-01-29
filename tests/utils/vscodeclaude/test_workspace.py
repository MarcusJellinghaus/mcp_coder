"""Test workspace setup and git operations for VSCode Claude."""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.utils.vscodeclaude.workspace import (
    create_startup_script,
    create_status_file,
    create_vscode_task,
    create_working_folder,
    create_workspace_file,
    get_working_folder_path,
    run_setup_commands,
    setup_git_repo,
    update_gitignore,
    validate_mcp_json,
    validate_setup_commands,
)


class TestWorkspaceSetup:
    """Test workspace creation and setup."""

    def test_get_working_folder_path(self) -> None:
        """Constructs correct folder path."""
        path = get_working_folder_path(
            workspace_base="/home/user/projects",
            repo_name="mcp-coder",
            issue_number=123,
        )
        assert str(path).endswith("mcp-coder_123")

    def test_get_working_folder_path_sanitizes_repo_name(self) -> None:
        """Sanitizes repo name in folder path."""
        path = get_working_folder_path(
            workspace_base="/home/user/projects",
            repo_name="my repo!@#$",
            issue_number=456,
        )
        # Should sanitize to 'my-repo'
        assert "my-repo_456" in str(path)

    def test_create_working_folder_new(self, tmp_path: Path) -> None:
        """Creates folder when doesn't exist."""
        folder = tmp_path / "new_folder"
        result = create_working_folder(folder)
        assert result is True
        assert folder.exists()

    def test_create_working_folder_exists(self, tmp_path: Path) -> None:
        """Returns False when folder exists."""
        folder = tmp_path / "existing"
        folder.mkdir()
        result = create_working_folder(folder)
        assert result is False

    def test_create_working_folder_nested(self, tmp_path: Path) -> None:
        """Creates nested directories."""
        folder = tmp_path / "a" / "b" / "c"
        result = create_working_folder(folder)
        assert result is True
        assert folder.exists()

    def test_validate_mcp_json_exists(self, tmp_path: Path) -> None:
        """Passes when .mcp.json exists."""
        (tmp_path / ".mcp.json").write_text("{}")
        validate_mcp_json(tmp_path)  # Should not raise

    def test_validate_mcp_json_missing(self, tmp_path: Path) -> None:
        """Raises when .mcp.json missing."""
        with pytest.raises(FileNotFoundError, match=".mcp.json"):
            validate_mcp_json(tmp_path)

    def test_validate_setup_commands_valid(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Passes when all commands exist in PATH."""

        # Mock shutil.which to return a path for known commands
        def mock_which(cmd: str) -> str | None:
            if cmd in ["python", "git", "echo"]:
                return f"/usr/bin/{cmd}"
            return None

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.workspace.shutil.which", mock_which
        )

        validate_setup_commands(["python --version", "git status"])

    def test_validate_setup_commands_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises when command not found in PATH."""
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.workspace.shutil.which",
            lambda cmd: None,
        )

        with pytest.raises(FileNotFoundError, match="not found in PATH"):
            validate_setup_commands(["nonexistent_command"])

    def test_run_setup_commands_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Runs commands in correct directory."""

        commands_run: list[tuple[Any, Any]] = []

        def mock_run(cmd: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            commands_run.append((cmd, kwargs.get("cwd")))
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.workspace.subprocess.run", mock_run
        )

        run_setup_commands(tmp_path, ["echo hello", "echo world"])

        assert len(commands_run) == 2
        assert all(cwd == tmp_path for _, cwd in commands_run)

    def test_run_setup_commands_failure_aborts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises on command failure."""

        def mock_run(cmd: Any, **kwargs: Any) -> None:
            raise subprocess.CalledProcessError(1, cmd)

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.workspace.subprocess.run", mock_run
        )

        with pytest.raises(subprocess.CalledProcessError):
            run_setup_commands(tmp_path, ["failing_command"])

    def test_update_gitignore_adds_entry(self, tmp_path: Path) -> None:
        """Adds vscodeclaude entry to .gitignore."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")

        update_gitignore(tmp_path)

        content = gitignore.read_text(encoding="utf-8")
        assert ".vscodeclaude_status.md" in content
        assert "*.pyc" in content  # Preserves existing

    def test_update_gitignore_creates_file(self, tmp_path: Path) -> None:
        """Creates .gitignore when doesn't exist."""
        update_gitignore(tmp_path)

        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        assert ".vscodeclaude_status.md" in gitignore.read_text(encoding="utf-8")

    def test_update_gitignore_idempotent(self, tmp_path: Path) -> None:
        """Doesn't duplicate entry on second call."""
        update_gitignore(tmp_path)
        update_gitignore(tmp_path)

        gitignore = tmp_path / ".gitignore"
        content = gitignore.read_text(encoding="utf-8")
        assert content.count(".vscodeclaude_status.md") == 1

    def test_create_workspace_file(self, tmp_path: Path) -> None:
        """Creates valid workspace JSON file."""
        workspace_path = create_workspace_file(
            workspace_base=str(tmp_path),
            folder_name="mcp-coder_123",
            issue_number=123,
            issue_title="Add feature",
            status="status-07:code-review",
            repo_name="mcp-coder",
        )

        assert workspace_path.exists()
        assert workspace_path.suffix == ".code-workspace"

        content = json.loads(workspace_path.read_text(encoding="utf-8"))
        assert "folders" in content
        assert "settings" in content
        assert "#123" in content["settings"]["window.title"]

    def test_create_workspace_file_truncates_long_title(self, tmp_path: Path) -> None:
        """Truncates long issue titles."""
        long_title = "A" * 50  # More than 30 chars
        workspace_path = create_workspace_file(
            workspace_base=str(tmp_path),
            folder_name="test_1",
            issue_number=1,
            issue_title=long_title,
            status="status-01:created",
            repo_name="test",
        )

        content = json.loads(workspace_path.read_text(encoding="utf-8"))
        # Title should be truncated with ...
        assert "..." in content["settings"]["window.title"]

    def test_create_startup_script_windows(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Creates .bat script on Windows."""
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            is_intervention=False,
        )

        assert script_path.suffix == ".bat"
        assert script_path.exists()
        content = script_path.read_text(encoding="utf-8")
        assert "claude" in content
        assert "/implementation_review" in content

    def test_create_startup_script_linux(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Creates .sh script on Linux."""
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.workspace.platform.system",
            lambda: "Linux",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            is_intervention=False,
        )

        assert script_path.suffix == ".sh"
        assert script_path.exists()

    def test_create_startup_script_intervention(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Intervention mode uses plain claude command."""
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-06:implementing",  # bot_busy status
            repo_name="test-repo",
            is_intervention=True,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "INTERVENTION" in content
        assert "/implementation_review" not in content

    def test_create_vscode_task(self, tmp_path: Path) -> None:
        """Creates tasks.json with runOn: folderOpen."""
        script_path = tmp_path / ".vscodeclaude_start.bat"
        script_path.touch()

        create_vscode_task(tmp_path, script_path)

        tasks_file = tmp_path / ".vscode" / "tasks.json"
        assert tasks_file.exists()

        content = json.loads(tasks_file.read_text(encoding="utf-8"))
        assert content["tasks"][0]["runOptions"]["runOn"] == "folderOpen"

    def test_create_status_file(self, tmp_path: Path) -> None:
        """Creates status markdown file."""
        create_status_file(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Add feature",
            status="status-07:code-review",
            repo_full_name="owner/repo",
            branch_name="feature-123",
            issue_url="https://github.com/owner/repo/issues/123",
            is_intervention=False,
        )

        status_file = tmp_path / ".vscodeclaude_status.md"
        assert status_file.exists()

        content = status_file.read_text(encoding="utf-8")
        assert "#123" in content
        assert "Add feature" in content
        assert "code-review" in content

    def test_create_status_file_intervention(self, tmp_path: Path) -> None:
        """Status file includes intervention warning when set."""
        create_status_file(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test",
            status="status-07:code-review",
            repo_full_name="owner/repo",
            branch_name="main",
            issue_url="https://github.com/owner/repo/issues/123",
            is_intervention=True,
        )

        status_file = tmp_path / ".vscodeclaude_status.md"
        content = status_file.read_text(encoding="utf-8")
        assert "INTERVENTION" in content


class TestGitOperations:
    """Test git clone/checkout/pull operations."""

    def test_setup_git_repo_clone_new(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Clones when folder is empty."""

        commands: list[Any] = []

        def mock_run(cmd: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            commands.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.workspace.subprocess.run", mock_run
        )

        folder = tmp_path / "new_repo"
        folder.mkdir()

        setup_git_repo(folder, "https://github.com/owner/repo.git", "main")

        # Should have clone, checkout, pull
        assert any("clone" in str(c) for c in commands)

    def test_setup_git_repo_existing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Checkout and pull when .git exists."""

        commands: list[Any] = []

        def mock_run(cmd: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            commands.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.workspace.subprocess.run", mock_run
        )

        # Create folder with .git
        folder = tmp_path / "existing_repo"
        folder.mkdir()
        (folder / ".git").mkdir()

        setup_git_repo(folder, "https://github.com/owner/repo.git", "feature-branch")

        # Should NOT clone, but should checkout and pull
        assert not any("clone" in str(c) for c in commands)
        assert any("checkout" in str(c) for c in commands)
        assert any("pull" in str(c) for c in commands)

    def test_setup_git_repo_uses_main_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Uses main branch when branch_name is None."""

        commands: list[Any] = []

        def mock_run(cmd: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            commands.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.workspace.subprocess.run", mock_run
        )

        folder = tmp_path / "repo"
        folder.mkdir()
        (folder / ".git").mkdir()

        setup_git_repo(folder, "https://github.com/owner/repo.git", None)

        checkout_cmd = [c for c in commands if "checkout" in str(c)][0]
        assert "main" in checkout_cmd

    def test_setup_git_repo_folder_with_content_no_git(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises error when folder has content but no .git."""

        def mock_run(cmd: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.workspace.subprocess.run", mock_run
        )

        folder = tmp_path / "has_content"
        folder.mkdir()
        (folder / "somefile.txt").write_text("content")

        with pytest.raises(ValueError, match="not a git repository"):
            setup_git_repo(folder, "https://github.com/owner/repo.git", "main")
