from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.llm.interface import prompt_llm, prompt_llm_stream
from tests.llm.test_interface import PROJECT_DIR


class TestPromptLlmInjectPrompts:
    """Tests for the inject_prompts switch in prompt_llm and prompt_llm_stream."""

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_no_inject_prompts_loads_nothing(
        self,
        mock_ask_claude_code_cli: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """With inject_prompts left at its default, no prompts are loaded."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        prompt_llm("Test question", project_dir=PROJECT_DIR)

        mock_load_prompts.assert_not_called()
        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_project_dir_loads_prompts(
        self,
        mock_ask_claude_code_cli: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """When project_dir is provided, load_prompts is called and results passed to provider."""
        from mcp_coder.utils.pyproject_config import PromptsConfig

        mock_config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )
        mock_load_prompts.return_value = (
            "system prompt content",
            "project prompt content",
            mock_config,
        )
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with prompts",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm(
            "Test question", project_dir="/my/project", inject_prompts=True
        )

        mock_load_prompts.assert_called_once_with(Path("/my/project"))
        expected_combined = (
            "## System Prompt\n\nsystem prompt content\n\n"
            "## Project Prompt\n\nproject prompt content"
        )
        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=str(Path("/my/project")),
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=expected_combined,
            system_prompt_replace=None,
        )
        assert result["text"] == "Response with prompts"

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_prompt_llm_stream_project_dir_loads_prompts(
        self,
        mock_stream: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """prompt_llm_stream with project_dir loads prompts and passes to provider."""
        from mcp_coder.utils.pyproject_config import PromptsConfig

        mock_config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )
        mock_load_prompts.return_value = (
            "sys prompt",
            "proj prompt",
            mock_config,
        )
        mock_stream.return_value = iter(
            [{"type": "text_delta", "text": "Hi"}, {"type": "done", "usage": {}}]
        )

        events = list(
            prompt_llm_stream(
                "Hello",
                provider="claude",
                project_dir="/my/project",
                inject_prompts=True,
            )
        )

        mock_load_prompts.assert_called_once_with(Path("/my/project"))
        expected_combined = (
            "## System Prompt\n\nsys prompt\n\n" + "## Project Prompt\n\nproj prompt"
        )
        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=str(Path("/my/project")),
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=expected_combined,
            system_prompt_replace=None,
        )
        assert len(events) == 2

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch("mcp_coder.llm.providers.langchain.ask_langchain")
    def test_prompt_llm_langchain_project_dir_loads_prompts(
        self,
        mock_ask_langchain: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """prompt_llm with langchain provider and project_dir passes prompts."""
        from mcp_coder.utils.pyproject_config import PromptsConfig

        mock_config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )
        mock_load_prompts.return_value = (
            "sys prompt",
            "proj prompt",
            mock_config,
        )
        mock_ask_langchain.return_value = {
            "text": "langchain reply",
            "session_id": "lc-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "langchain",
            "raw_response": {},
        }

        result = prompt_llm(
            "Test question",
            provider="langchain",
            project_dir="/my/project",
            inject_prompts=True,
        )

        mock_load_prompts.assert_called_once_with(Path("/my/project"))
        call_kwargs = mock_ask_langchain.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs["system_prompt"] == "sys prompt"
        assert kwargs["project_prompt"] == "proj prompt"
        assert result["text"] == "langchain reply"


class TestBuildClaudeSystemPrompts:
    """Tests for _build_claude_system_prompts helper."""

    def test_append_mode_returns_combined_in_first_slot(self) -> None:
        """In append mode, combined prompt goes to append_system_prompt."""
        from mcp_coder.llm.interface import _build_claude_system_prompts
        from mcp_coder.utils.pyproject_config import PromptsConfig

        config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )

        append, replace = _build_claude_system_prompts(
            "System text", "Project text", config, "/fake/dir"
        )

        expected = (
            "## System Prompt\n\nSystem text\n\n" + "## Project Prompt\n\nProject text"
        )
        assert append == expected
        assert replace is None

    def test_replace_mode_returns_combined_in_second_slot(self) -> None:
        """In replace mode, combined prompt goes to system_prompt_replace."""
        from mcp_coder.llm.interface import _build_claude_system_prompts
        from mcp_coder.utils.pyproject_config import PromptsConfig

        config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="replace",
        )

        append, replace = _build_claude_system_prompts(
            "System text", "Project text", config, "/fake/dir"
        )

        expected = (
            "## System Prompt\n\nSystem text\n\n" + "## Project Prompt\n\nProject text"
        )
        assert append is None
        assert replace == expected

    @patch("mcp_coder.prompts.prompt_loader.is_claude_md", return_value=True)
    @patch(
        "mcp_coder.prompts.prompt_loader.get_project_prompt_path",
        return_value=Path("/fake/dir/CLAUDE.md"),
    )
    def test_skips_project_prompt_when_claude_md(
        self,
        _mock_path: MagicMock,
        _mock_is_claude: MagicMock,
    ) -> None:
        """Project prompt is skipped when pointing at CLAUDE.md."""
        from mcp_coder.llm.interface import _build_claude_system_prompts
        from mcp_coder.utils.pyproject_config import PromptsConfig

        config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )

        append, replace = _build_claude_system_prompts(
            "System text", "Project text", config, "/fake/dir"
        )

        assert append == "## System Prompt\n\nSystem text"
        assert replace is None

    def test_no_prompts_returns_none(self) -> None:
        """When both prompts are None, returns (None, None)."""
        from mcp_coder.llm.interface import _build_claude_system_prompts
        from mcp_coder.utils.pyproject_config import PromptsConfig

        config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )

        append, replace = _build_claude_system_prompts(None, None, config, None)

        assert append is None
        assert replace is None

    def test_only_system_prompt(self) -> None:
        """When only system_prompt is set, only system section present."""
        from mcp_coder.llm.interface import _build_claude_system_prompts
        from mcp_coder.utils.pyproject_config import PromptsConfig

        config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )

        append, replace = _build_claude_system_prompts(
            "System only", None, config, None
        )

        assert append == "## System Prompt\n\nSystem only"
        assert replace is None
