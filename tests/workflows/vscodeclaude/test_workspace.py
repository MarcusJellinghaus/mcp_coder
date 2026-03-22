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
        "commands": ["/issue_analyse", "/discuss"],
    },
    "status-04:plan-review": {
        "emoji": "📋",
        "display_name": "PLAN REVIEW",
        "stage_short": "plan",
        "commands": ["/plan_review", "/discuss"],
    },
    "status-07:code-review": {
        "emoji": "🔍",
        "display_name": "CODE REVIEW",
        "stage_short": "review",
        "commands": ["/implementation_review_supervisor"],
    },
    "status-10:pr-created": {
        "emoji": "🎉",
        "display_name": "PR CREATED",
        "stage_short": "pr",
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
        assert ".vscodeclaude_status.txt" in content
        assert "*.pyc" in content  # Preserves existing

    def test_update_gitignore_creates_file(self, tmp_path: Path) -> None:
        """Creates .gitignore when doesn't exist."""
        update_gitignore(tmp_path)

        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        assert ".vscodeclaude_status.txt" in gitignore.read_text(encoding="utf-8")

    def test_update_gitignore_idempotent(self, tmp_path: Path) -> None:
        """Doesn't duplicate entry on second call."""
        update_gitignore(tmp_path)
        update_gitignore(tmp_path)

        gitignore = tmp_path / ".gitignore"
        content = gitignore.read_text(encoding="utf-8")
        assert content.count(".vscodeclaude_status.txt") == 1

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
        assert "/implementation_review_supervisor" in content

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
        assert "/implementation_review_supervisor" not in content

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

        status_file = tmp_path / ".vscodeclaude_status.txt"
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

        status_file = tmp_path / ".vscodeclaude_status.txt"
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
        """Generated script uses mcp-coder prompt for multi-command flow."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        # Use status-01:created which has commands=["/issue_analyse", "/discuss"]
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
        assert "mcp-coder prompt" in content
        assert "--output-format session-id" in content
        # 2-command flow: no middle commands, so no --session-id automated resume
        assert "--session-id %SESSION_ID%" not in content
        # Last command is interactive resume
        assert "claude --resume %SESSION_ID%" in content
        assert "/discuss" in content

    def test_creates_script_with_claude_resume(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Single-command flow uses interactive-only (no resume)."""
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
        # Single command: interactive-only with issue number, no resume
        assert 'claude "/implementation_review_supervisor 123"' in content
        # No automated step for single command
        assert "mcp-coder prompt" not in content
        # No step labels for single command
        assert "Step 1" not in content

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

    def test_batch_title_escapes_redirection_characters(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Issue title with > is escaped in .bat to prevent shell redirection."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=453,
            issue_title="Fix issue -> Create and start",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/453",
            is_intervention=False,
        )

        content = script_path.read_text(encoding="utf-8")
        # The > should be escaped as ^> to prevent shell redirection
        assert "^>" in content
        # The unescaped sequence -> should not appear in the title section
        assert "-> Create" not in content

    def test_batch_title_strips_trailing_caret_after_truncation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Trailing ^ from escaping is stripped when it lands at the truncation boundary.

        A title of 57 normal chars + '>' becomes 57 + '^>' (59 chars) after escaping.
        Truncation at 58 chars leaves a lone '^' at the end, which must be stripped
        to prevent batch treating it as a line-continuation character.
        """
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        # 57 'A's + '>' — after escaping: 57 'A's + '^>' (59 chars)
        # After [:58]: 57 'A's + '^'  ← lone caret, must be stripped
        title = "A" * 57 + ">"

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title=title,
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
        )

        content = script_path.read_text(encoding="utf-8")
        # The title section must not contain a lone trailing ^
        # (a lone ^ at end of a batch echo line causes line-continuation)
        for line in content.splitlines():
            if "AAAA" in line:
                assert not line.rstrip().endswith(
                    "^"
                ), f"Lone trailing ^ found in batch line: {line!r}"

    def test_multi_command_has_automated_and_interactive_sections(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Multi-command flow has automated first step and interactive last step."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        # Use status-01:created which has commands=["/issue_analyse", "/discuss"]
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
        # First command is automated
        assert "mcp-coder prompt" in content
        # Last command is interactive resume
        assert "claude --resume %SESSION_ID%" in content
        assert "/discuss" in content
        # Multi-command has step labels
        assert "Step 1" in content

    def test_single_command_uses_interactive_only(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Single-command flow uses interactive-only, no automated step."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        # Use status-07:code-review which has commands=["/implementation_review_supervisor"]
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
        # No automated step for single command
        assert "mcp-coder prompt" not in content
        # Interactive-only with issue number
        assert 'claude "/implementation_review_supervisor 123"' in content
        # No step labels
        assert "Step 1" not in content
        assert "Step 2" not in content
        # No resume (no session ID captured)
        assert "claude --resume %SESSION_ID%" not in content

    def test_creates_script_with_env_var_setup(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Generated script properly implements two-environment setup with venv activation."""
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
        # With the fix: script uses mcp-coder installation path instead of env vars
        # Script should show the install path and set up MCP_CODER_VENV_PATH from it
        assert "MCP-Coder install:" in content
        assert "PATH=%MCP_CODER_VENV_PATH%;%PATH%" in content
        # Should activate project venv for current directory
        assert "activate.bat" in content
        # Should contain check for mcp_coder_install_path, not MCP_CODER_PROJECT_DIR
        assert '" NEQ ""' in content

    def test_three_command_flow_has_automated_resume_middle(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Three-command flow uses automated resume for middle command."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        # Custom 3-command mock config
        three_cmd_configs: dict[str, dict[str, Any]] = {
            "status-triple": {
                "emoji": "🔧",
                "display_name": "TRIPLE",
                "stage_short": "tri",
                "commands": ["/step_one", "/step_two", "/step_three"],
            },
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.get_vscodeclaude_config",
            lambda s: three_cmd_configs.get(s),
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=99,
            issue_title="Triple test",
            status="status-triple",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/99",
            is_intervention=False,
        )

        content = script_path.read_text(encoding="utf-8")
        # First command is automated
        assert "mcp-coder prompt" in content
        assert "--output-format session-id" in content
        # Middle command uses automated resume
        assert "--session-id %SESSION_ID%" in content
        # Last command is interactive resume
        assert "claude --resume %SESSION_ID%" in content
        assert "/step_three" in content
        # All steps have labels
        assert "Step 1" in content
        assert "Step 2" in content
        assert "Step 3" in content

    def test_empty_commands_generates_bare_script(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Config with empty commands list generates script with no command sections."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        empty_cmd_configs: dict[str, dict[str, Any]] = {
            "status-empty": {
                "emoji": "📋",
                "display_name": "EMPTY",
                "stage_short": "emp",
                "commands": [],
            },
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.get_vscodeclaude_config",
            lambda s: empty_cmd_configs.get(s),
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Empty test",
            status="status-empty",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
        )

        content = script_path.read_text(encoding="utf-8")
        # Has venv section but no command sections
        assert "uv venv" in content
        assert "mcp-coder prompt" not in content
        assert "claude --resume" not in content
        assert "Step 1" not in content

    def test_invalid_commands_type_raises_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Config with non-list commands raises ValueError."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        bad_configs: dict[str, dict[str, Any]] = {
            "status-bad": {
                "emoji": "📋",
                "display_name": "BAD",
                "stage_short": "bad",
                "commands": "/single_string",
            },
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.get_vscodeclaude_config",
            lambda s: bad_configs.get(s),
        )

        with pytest.raises(ValueError, match="Invalid commands config"):
            create_startup_script(
                folder_path=tmp_path,
                issue_number=1,
                issue_title="Bad test",
                status="status-bad",
                repo_name="test-repo",
                issue_url="https://github.com/test/repo/issues/1",
                is_intervention=False,
            )

    def test_invalid_commands_element_raises_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Config with non-string elements in commands raises ValueError."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        bad_configs: dict[str, dict[str, Any]] = {
            "status-bad": {
                "emoji": "📋",
                "display_name": "BAD",
                "stage_short": "bad",
                "commands": ["/valid", 123],
            },
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.get_vscodeclaude_config",
            lambda s: bad_configs.get(s),
        )

        with pytest.raises(ValueError, match="Invalid commands config"):
            create_startup_script(
                folder_path=tmp_path,
                issue_number=1,
                issue_title="Bad test",
                status="status-bad",
                repo_name="test-repo",
                issue_url="https://github.com/test/repo/issues/1",
                is_intervention=False,
            )
