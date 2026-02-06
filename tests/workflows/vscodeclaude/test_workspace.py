"""Test workspace setup for VSCode Claude."""

import json
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.utils.subprocess_runner import CalledProcessError, CommandResult
from mcp_coder.workflows.vscodeclaude.workspace import (
    create_startup_script,
    create_status_file,
    create_vscode_task,
    create_working_folder,
    create_workspace_file,
    get_working_folder_path,
    run_setup_commands,
    update_gitignore,
    validate_mcp_json,
    validate_setup_commands,
)

# Mock vscodeclaude config data for tests
MOCK_VSCODECLAUDE_CONFIGS: dict[str, dict[str, Any]] = {
    "status-01:created": {
        "emoji": "📝",
        "display_name": "ISSUE ANALYSIS",
        "stage_short": "new",
        "initial_command": "/issue_analyse",
        "followup_command": "/discuss",
    },
    "status-04:plan-review": {
        "emoji": "📋",
        "display_name": "PLAN REVIEW",
        "stage_short": "plan",
        "initial_command": "/plan_review",
        "followup_command": "/discuss",
    },
    "status-07:code-review": {
        "emoji": "🔍",
        "display_name": "CODE REVIEW",
        "stage_short": "review",
        "initial_command": "/implementation_review",
        "followup_command": "/discuss",
    },
    "status-10:pr-created": {
        "emoji": "🎉",
        "display_name": "PR CREATED",
        "stage_short": "pr",
        "initial_command": None,
        "followup_command": None,
    },
}


def _mock_get_vscodeclaude_config(status: str) -> dict[str, Any] | None:
    """Mock implementation for get_vscodeclaude_config."""
    return MOCK_VSCODECLAUDE_CONFIGS.get(status)


@pytest.fixture
def mock_vscodeclaude_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock get_vscodeclaude_config for workspace tests."""
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.workspace.get_vscodeclaude_config",
        _mock_get_vscodeclaude_config,
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
            "mcp_coder.workflows.vscodeclaude.workspace.shutil.which", mock_which
        )

        validate_setup_commands(["python --version", "git status"])

    def test_validate_setup_commands_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises when command not found in PATH."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.shutil.which",
            lambda cmd: None,
        )

        with pytest.raises(FileNotFoundError, match="not found in PATH"):
            validate_setup_commands(["nonexistent_command"])

    def test_run_setup_commands_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Runs commands in correct directory."""

        commands_run: list[tuple[Any, Any]] = []

        def mock_execute(cmd: Any, options: Any = None) -> CommandResult:
            cwd = options.cwd if options else None
            commands_run.append((cmd, cwd))
            return CommandResult(return_code=0, stdout="", stderr="", timed_out=False)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.execute_subprocess",
            mock_execute,
        )

        run_setup_commands(tmp_path, ["echo hello", "echo world"])

        assert len(commands_run) == 2
        assert all(cwd == str(tmp_path) for _, cwd in commands_run)

    def test_run_setup_commands_failure_aborts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises on command failure."""

        def mock_execute(cmd: Any, options: Any = None) -> None:
            raise CalledProcessError(1, cmd)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.execute_subprocess",
            mock_execute,
        )

        with pytest.raises(CalledProcessError):
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

    def test_create_workspace_file(
        self, tmp_path: Path, mock_vscodeclaude_config: None
    ) -> None:
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

    def test_create_workspace_file_truncates_long_title(
        self, tmp_path: Path, mock_vscodeclaude_config: None
    ) -> None:
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
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Creates .bat script on Windows."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/owner/test-repo/issues/123",
            is_intervention=False,
        )

        assert script_path.suffix == ".bat"
        assert script_path.exists()
        content = script_path.read_text(encoding="utf-8")
        assert "claude" in content
        assert "/implementation_review" in content

    def test_create_startup_script_linux_raises_not_implemented(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Linux raises NotImplementedError until Step 17."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Linux",
        )

        with pytest.raises(NotImplementedError, match="Linux templates"):
            create_startup_script(
                folder_path=tmp_path,
                issue_number=123,
                issue_title="Test issue",
                status="status-07:code-review",
                repo_name="test-repo",
                issue_url="https://github.com/owner/test-repo/issues/123",
                is_intervention=False,
            )

    def test_create_startup_script_intervention(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Intervention mode uses plain claude command."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-06:implementing",  # bot_busy status
            repo_name="test-repo",
            issue_url="https://github.com/owner/test-repo/issues/123",
            is_intervention=True,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "INTERVENTION" in content
        assert "/implementation_review" not in content

    def test_create_vscode_task(self, tmp_path: Path) -> None:
        """Creates tasks.json with two tasks that run on folderOpen."""
        script_path = tmp_path / ".vscodeclaude_start.bat"
        script_path.touch()

        create_vscode_task(tmp_path, script_path)

        tasks_file = tmp_path / ".vscode" / "tasks.json"
        assert tasks_file.exists()

        content = json.loads(tasks_file.read_text(encoding="utf-8"))
        assert len(content["tasks"]) == 2
        assert content["tasks"][0]["runOptions"]["runOn"] == "folderOpen"
        assert content["tasks"][1]["label"] == "Open Status File"

    def test_create_status_file(
        self, tmp_path: Path, mock_vscodeclaude_config: None
    ) -> None:
        """Creates status txt file with plain text banner format."""
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
        assert "Branch:" in content
        assert "feature-123" in content
        assert "Started:" in content

    def test_create_status_file_intervention(
        self, tmp_path: Path, mock_vscodeclaude_config: None
    ) -> None:
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
        assert status_file.exists()
        content = status_file.read_text(encoding="utf-8")
        assert "INTERVENTION" in content


class TestCreateStartupScript:
    """Test startup script generation with venv and mcp-coder."""

    def test_creates_script_with_venv_section(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Generated script includes venv setup."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "uv venv" in content
        assert "activate.bat" in content

    def test_creates_script_with_mcp_coder_prompt(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Generated script uses mcp-coder prompt."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "mcp-coder prompt" in content
        assert "--output-format session-id" in content
        assert "--session-id %SESSION_ID%" in content

    def test_creates_script_with_claude_resume(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Generated script ends with claude --resume."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "claude --resume %SESSION_ID%" in content

    def test_uses_custom_timeout(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Timeout parameter is used in script."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-01:created",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
            timeout=600,  # 10 minutes
        )

        content = script_path.read_text(encoding="utf-8")
        assert "--timeout 600" in content

    def test_intervention_mode_no_automation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Intervention mode skips automation."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-06:implementing",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=True,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "INTERVENTION MODE" in content
        assert "mcp-coder prompt" not in content
        assert "uv venv" in content  # Venv still activated

    def test_uses_correct_initial_command_for_status(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Uses correct initial command based on status."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        # Test status-01:created -> /issue_analyse
        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-01:created",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "/issue_analyse 123" in content

    def test_includes_discussion_section(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Generated script includes discussion section."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "/discuss" in content
        assert "Step 2: Automated Discussion" in content

    def test_creates_script_with_env_var_setup(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Generated script sets MCP_CODER_PROJECT_DIR and MCP_CODER_VENV_DIR."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )

        content = script_path.read_text(encoding="utf-8")
        assert 'set "MCP_CODER_PROJECT_DIR=%CD%"' in content
        assert 'set "MCP_CODER_VENV_DIR=%CD%\\.venv"' in content
