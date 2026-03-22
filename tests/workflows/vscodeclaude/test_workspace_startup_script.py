"""Test startup script generation for VSCode Claude workspace."""

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.workflows.vscodeclaude.workspace import create_startup_script


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
