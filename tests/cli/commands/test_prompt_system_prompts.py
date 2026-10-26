import argparse
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt
from tests.cli.commands.test_prompt import _make_text_events


class TestAddSystemPromptsFlag:
    """Tests for --add-system-prompts flag wiring."""

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_prompt_add_system_prompts_flag_injects_prompts(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When --add-system-prompts is set, inject_prompts=True reaches prompt_llm_stream."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response with prompts.")
        )

        args = argparse.Namespace(
            prompt="Test prompt",
            add_system_prompts=True,
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        call_kwargs = mock_prompt_llm_stream.call_args[1]
        assert call_kwargs["inject_prompts"] is True
        # project_dir is resolved from CWD since the project_dir arg is None
        assert call_kwargs["project_dir"] == str(Path.cwd())

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_prompt_no_flag_no_prompt_injection(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Without --add-system-prompts, inject_prompts=False is passed."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response without prompts.")
        )

        args = argparse.Namespace(
            prompt="Test prompt",
            add_system_prompts=False,
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        call_kwargs = mock_prompt_llm_stream.call_args[1]
        assert call_kwargs["inject_prompts"] is False

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_prompt_add_system_prompts_with_explicit_project_dir(
        self,
        mock_prompt_llm_stream: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When --add-system-prompts is set with explicit --project-dir, that dir is used."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(tmp_path)}
        mock_prompt_llm_stream.return_value = iter(
            _make_text_events("Response with explicit project dir.")
        )

        args = argparse.Namespace(
            prompt="Test prompt",
            add_system_prompts=True,
            llm_method="claude",
            mcp_config=None,
            settings=None,
            project_dir=str(tmp_path),
        )

        result = execute_prompt(args)

        assert result == 0
        call_kwargs = mock_prompt_llm_stream.call_args[1]
        assert call_kwargs["inject_prompts"] is True
        assert call_kwargs["project_dir"] == str(tmp_path)

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_prompt_add_system_prompts_session_id_format(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Flag works with session-id output format (prompt_llm path)."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm.return_value = {
            "text": "response",
            "session_id": "sess-123",
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }

        args = argparse.Namespace(
            prompt="Test prompt",
            add_system_prompts=True,
            output_format="session-id",
            timeout=30,
            llm_method="claude",
            session_id=None,
            continue_session_from=None,
            continue_session=False,
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        call_kwargs = mock_prompt_llm.call_args[1]
        assert call_kwargs["inject_prompts"] is True

    @patch("mcp_coder.cli.commands.prompt.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.prompt.resolve_llm_method")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_prompt_add_system_prompts_json_format(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Flag works with json output format (prompt_llm path with branch_name)."""
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_resolve_mcp.return_value = None
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_prompt_llm.return_value = {
            "text": "response",
            "session_id": "sess-456",
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "provider": "claude",
            "raw_response": {},
        }

        args = argparse.Namespace(
            prompt="Test prompt",
            add_system_prompts=True,
            output_format="json",
            timeout=30,
            llm_method="claude",
            session_id=None,
            continue_session_from=None,
            continue_session=False,
            store_response=False,
            mcp_config=None,
            settings=None,
            project_dir=None,
        )

        result = execute_prompt(args)

        assert result == 0
        call_kwargs = mock_prompt_llm.call_args[1]
        assert call_kwargs["inject_prompts"] is True
