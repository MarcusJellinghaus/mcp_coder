import argparse
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt
from tests.cli.commands.test_prompt import _make_text_events


class TestPromptClaudeCwd:
    """Tests for Claude working directory handling in prompt command."""

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_no_project_dir_falls_back_to_cwd(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """No --project-dir: the subprocess cwd is the shell's CWD.

        This documents the no-``project_dir`` fallback, not the default. The
        default is ``project_dir`` (see ``test_claude_cwd_is_project_dir``
        below); this test only reaches the CWD because ``project_dir`` is None.
        """
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response from the working directory.")
        )

        args = argparse.Namespace(
            prompt="Test prompt",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        # Verify the subprocess cwd was passed to prompt_llm_stream and is CWD
        call_kwargs = mock_prompt_llm_stream.call_args[1]
        assert "project_dir" in call_kwargs
        assert call_kwargs["project_dir"] == str(Path.cwd())
        captured = capsys.readouterr()
        assert "Response from the working directory." in captured.out

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_claude_cwd_is_project_dir(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The subprocess cwd is --project-dir, not the shell's cwd."""
        project_dir = tmp_path / "repo"
        project_dir.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()

        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(project_dir)}
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response from the project directory.")
        )

        args = argparse.Namespace(
            prompt="Test prompt",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=str(project_dir),
        )

        # Stand outside the project directory: "from any shell working directory"
        # is half the acceptance criterion.
        monkeypatch.chdir(elsewhere)

        result = execute_prompt(args)

        assert result == 0
        call_kwargs = mock_prompt_llm_stream.call_args[1]
        assert call_kwargs["project_dir"] == str(project_dir)
        assert call_kwargs["project_dir"] != str(Path.cwd())
        captured = capsys.readouterr()
        assert "Response from the project directory." in captured.out

    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_claude_cwd_with_all_other_args(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Resolving the Claude cwd works with all other args (no conflicts)."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response with all args.")
        )

        project_dir = tmp_path / "project_dir"
        project_dir.mkdir()

        args = argparse.Namespace(
            prompt="Test prompt",
            project_dir=str(project_dir),
            timeout=60,
            llm_method="claude",
            output_format="text",
            session_id="test-session-123",
            mcp_config=None,
            settings=None,
        )

        result = execute_prompt(args)

        assert result == 0
        # Verify all arguments were passed correctly
        call_kwargs = mock_prompt_llm_stream.call_args[1]
        assert call_kwargs["project_dir"] == str(project_dir)
        assert call_kwargs["timeout"] == 60
        assert call_kwargs["session_id"] == "test-session-123"
        captured = capsys.readouterr()
        assert "Response with all args." in captured.out
