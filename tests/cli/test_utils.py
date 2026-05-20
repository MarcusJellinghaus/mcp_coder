"""Tests for CLI utility functions."""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.utils import (
    log_command_startup,
    parse_llm_method_from_args,
    resolve_issue_interaction_flags,
    resolve_llm_method,
)


class TestLogCommandStartup:
    """Test cases for log_command_startup function."""

    @patch(
        "mcp_coder.mcp_workspace_git.get_current_branch_name",
        return_value="feat/my-branch",
    )
    @patch("mcp_coder.__version__", new="1.2.3")
    def test_happy_path_with_project_dir(
        self,
        mock_branch: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Version, command, branch, and project_dir all present."""
        with caplog.at_level(logging.INFO, logger="mcp_coder.cli.utils"):
            log_command_startup("implement", project_dir=Path("/tmp/myproject"))

        assert "mcp-coder v1.2.3" in caplog.text
        assert "implement" in caplog.text
        assert "branch: feat/my-branch" in caplog.text
        assert "project:" in caplog.text
        assert "myproject" in caplog.text

    @patch("mcp_coder.__version__", new="0.9.0")
    def test_no_project_dir(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Coordinator case: no project_dir, only version and command."""
        with caplog.at_level(logging.INFO, logger="mcp_coder.cli.utils"):
            log_command_startup("coordinator")

        assert "mcp-coder v0.9.0 — coordinator" in caplog.text
        assert "branch" not in caplog.text
        assert "project" not in caplog.text

    @patch(
        "mcp_coder.mcp_workspace_git.get_current_branch_name",
        return_value=None,
    )
    @patch("mcp_coder.__version__", new="2.0.0")
    def test_unknown_branch(
        self,
        mock_branch: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """get_current_branch_name returns None -> '(unknown)' appears."""
        with caplog.at_level(logging.INFO, logger="mcp_coder.cli.utils"):
            log_command_startup("create-pr", project_dir=Path("/tmp/repo"))

        assert "branch: (unknown)" in caplog.text
        assert "mcp-coder v2.0.0" in caplog.text

    @patch(
        "mcp_coder.mcp_workspace_git.get_current_branch_name",
        side_effect=OSError("git not found"),
    )
    @patch("mcp_coder.__version__", new="3.0.0")
    def test_branch_query_exception_falls_back(
        self,
        mock_branch: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Branch query raising OSError falls back to '(unknown)'."""
        with caplog.at_level(logging.DEBUG, logger="mcp_coder.cli.utils"):
            log_command_startup("implement", project_dir=Path("/tmp/repo"))

        assert "branch: (unknown)" in caplog.text
        assert "mcp-coder v3.0.0" in caplog.text
        assert "Failed to query branch name" in caplog.text


class TestParseLLMMethodFromArgs:
    """Test cases for parse_llm_method_from_args function."""

    @patch("mcp_coder.cli.utils.parse_llm_method")
    def test_parse_llm_method_from_args_cli(self, mock_parse: MagicMock) -> None:
        """Test parsing CLI method parameter."""
        mock_parse.return_value = "claude"

        result = parse_llm_method_from_args("claude")

        assert result == "claude"
        mock_parse.assert_called_once_with("claude")

    @patch("mcp_coder.cli.utils.parse_llm_method")
    def test_parse_llm_method_from_args_invalid(self, mock_parse: MagicMock) -> None:
        """Test error handling for invalid method."""
        mock_parse.side_effect = ValueError("Unsupported llm_method: invalid_method")

        with pytest.raises(ValueError, match="Unsupported llm_method: invalid_method"):
            parse_llm_method_from_args("invalid_method")

        mock_parse.assert_called_once_with("invalid_method")

    @patch("mcp_coder.cli.utils.parse_llm_method")
    def test_parse_llm_method_from_args_empty_string(
        self, mock_parse: MagicMock
    ) -> None:
        """Test error handling for empty string."""
        mock_parse.side_effect = ValueError("Unsupported llm_method: ")

        with pytest.raises(ValueError, match="Unsupported llm_method: "):
            parse_llm_method_from_args("")

        mock_parse.assert_called_once_with("")

    @patch("mcp_coder.cli.utils.parse_llm_method")
    def test_parse_llm_method_from_args_delegates_to_original(
        self, mock_parse: MagicMock
    ) -> None:
        """Test that function properly delegates to underlying parse_llm_method."""
        expected_result = "test_provider"
        mock_parse.return_value = expected_result

        result = parse_llm_method_from_args("test_input")

        assert result == expected_result
        mock_parse.assert_called_once_with("test_input")

    def test_parse_llm_method_from_args_integration_claude(self) -> None:
        """Integration test for claude method without mocking."""
        provider = parse_llm_method_from_args("claude")

        assert provider == "claude"

    def test_parse_llm_method_from_args_integration_invalid(self) -> None:
        """Integration test for invalid method without mocking."""
        with pytest.raises(ValueError, match="Unsupported llm_method: invalid"):
            parse_llm_method_from_args("invalid")


class TestResolveLlmMethod:
    """Test cases for resolve_llm_method function."""

    def test_resolve_llm_method_cli_arg(self) -> None:
        """Test that explicit CLI arg returns (provider, 'cli argument') tuple."""
        assert resolve_llm_method("claude") == ("claude", "cli argument")
        assert resolve_llm_method("langchain") == ("langchain", "cli argument")

    def test_resolve_llm_method_cli_arg_invalid(self) -> None:
        """Test that invalid CLI arg raises ValueError via shared validation."""
        with pytest.raises(ValueError, match="invalid_method"):
            resolve_llm_method("invalid_method")

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_llm_method_config_default_provider(
        self, mock_config: MagicMock
    ) -> None:
        """Test that config default_provider=langchain returns tuple with config source."""
        mock_config.return_value = {("llm", "default_provider"): "langchain"}
        assert resolve_llm_method(None) == ("langchain", "config default_provider")

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_llm_method_env_var(
        self, mock_config: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that env var MCP_CODER_LLM_PROVIDER is checked before config."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        assert resolve_llm_method(None) == (
            "langchain",
            "env MCP_CODER_LLM_PROVIDER",
        )

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_llm_method_cli_overrides_env(
        self, mock_config: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that CLI arg takes precedence over env var."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        assert resolve_llm_method("claude") == ("claude", "cli argument")

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_llm_method_env_var_invalid(
        self, mock_config: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that invalid env var value raises ValueError."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "invalid_provider")
        with pytest.raises(ValueError, match="invalid_provider"):
            resolve_llm_method(None)

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_llm_method_default(self, mock_config: MagicMock) -> None:
        """Test that no CLI arg, no env var, no config returns ('claude', 'default')."""
        mock_config.return_value = {("llm", "default_provider"): None}
        assert resolve_llm_method(None) == ("claude", "default")

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_llm_method_invalid_config_provider(
        self, mock_config: MagicMock
    ) -> None:
        """Test that invalid config provider raises ValueError."""
        mock_config.return_value = {("llm", "default_provider"): "some_other"}
        with pytest.raises(ValueError, match="some_other"):
            resolve_llm_method(None)

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_llm_method_config_claude(self, mock_config: MagicMock) -> None:
        """Test that config default_provider=claude returns tuple with config source."""
        mock_config.return_value = {("llm", "default_provider"): "claude"}
        assert resolve_llm_method(None) == ("claude", "config default_provider")


class TestResolveExecutionDir:
    """Test cases for resolve_execution_dir function."""

    def test_none_returns_cwd(self) -> None:
        """None input should return current working directory."""
        from mcp_coder.cli.utils import resolve_execution_dir

        result = resolve_execution_dir(None)
        assert result == Path.cwd()

    def test_existing_absolute_path(self, tmp_path: Path) -> None:
        """Absolute paths to existing directories should be validated and returned."""
        from mcp_coder.cli.utils import resolve_execution_dir

        result = resolve_execution_dir(str(tmp_path))
        assert result == tmp_path.resolve()

    def test_existing_relative_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Relative paths should resolve relative to CWD."""
        from mcp_coder.cli.utils import resolve_execution_dir

        # Create a subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        # Change to tmp_path as CWD
        monkeypatch.chdir(tmp_path)

        result = resolve_execution_dir("subdir")
        assert result == subdir.resolve()

    def test_nonexistent_path_raises_error(self) -> None:
        """Non-existent paths should raise ValueError."""
        from mcp_coder.cli.utils import resolve_execution_dir

        with pytest.raises(ValueError, match="Execution directory does not exist"):
            resolve_execution_dir("/nonexistent/path/12345")

    @pytest.mark.parametrize(
        "dir_name",
        ["simple", "with-dash", "with_underscore", "nested/path"],
    )
    def test_various_directory_names(self, tmp_path: Path, dir_name: str) -> None:
        """Test various valid directory name patterns."""
        from mcp_coder.cli.utils import resolve_execution_dir

        # Create directory structure
        test_dir = tmp_path / dir_name
        test_dir.mkdir(parents=True, exist_ok=True)

        result = resolve_execution_dir(str(test_dir))
        assert result == test_dir.resolve()


class TestResolveIssueInteractionFlags:
    """Test cases for resolve_issue_interaction_flags function."""

    @patch("mcp_coder.cli.utils.get_repository_identifier", return_value=None)
    def test_defaults_to_false_false_when_no_cli_no_config(
        self, _mock_git_url: MagicMock
    ) -> None:
        """Args have both None, no config match -> (False, False)."""
        args = MagicMock(
            spec=["update_issue_labels", "post_issue_comments"],
            update_issue_labels=None,
            post_issue_comments=None,
        )
        result = resolve_issue_interaction_flags(args, Path("/tmp/project"))
        assert result == (False, False)

    @patch("mcp_coder.cli.utils.get_config_values")
    @patch(
        "mcp_coder.cli.utils.find_repo_section_by_url",
        return_value="coordinator.repos.myrepo",
    )
    @patch(
        "mcp_coder.cli.utils.get_repository_identifier",
        return_value=MagicMock(https_url="https://github.com/org/repo"),
    )
    def test_cli_flags_override_config(
        self,
        _mock_git_url: MagicMock,
        mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Config has both true, CLI has both False -> (False, False)."""
        mock_config.return_value = {
            ("coordinator.repos.myrepo", "update_issue_labels"): True,
            ("coordinator.repos.myrepo", "post_issue_comments"): True,
        }
        args = MagicMock(
            spec=["update_issue_labels", "post_issue_comments"],
            update_issue_labels=False,
            post_issue_comments=False,
        )
        result = resolve_issue_interaction_flags(args, Path("/tmp/project"))
        assert result == (False, False)

    @patch("mcp_coder.cli.utils.get_config_values")
    @patch(
        "mcp_coder.cli.utils.find_repo_section_by_url",
        return_value="coordinator.repos.myrepo",
    )
    @patch(
        "mcp_coder.cli.utils.get_repository_identifier",
        return_value=MagicMock(https_url="https://github.com/org/repo"),
    )
    def test_config_values_used_when_cli_none(
        self,
        _mock_git_url: MagicMock,
        mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Config has update_issue_labels=true, CLI is None -> (True, False)."""
        mock_config.return_value = {
            ("coordinator.repos.myrepo", "update_issue_labels"): True,
            ("coordinator.repos.myrepo", "post_issue_comments"): None,
        }
        args = MagicMock(
            spec=["update_issue_labels", "post_issue_comments"],
            update_issue_labels=None,
            post_issue_comments=None,
        )
        result = resolve_issue_interaction_flags(args, Path("/tmp/project"))
        assert result == (True, False)

    @patch("mcp_coder.cli.utils.get_config_values")
    @patch(
        "mcp_coder.cli.utils.find_repo_section_by_url",
        return_value="coordinator.repos.myrepo",
    )
    @patch(
        "mcp_coder.cli.utils.get_repository_identifier",
        return_value=MagicMock(https_url="https://github.com/org/repo"),
    )
    def test_cli_true_overrides_config_false(
        self,
        _mock_git_url: MagicMock,
        mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Config has both false, CLI has both True -> (True, True)."""
        mock_config.return_value = {
            ("coordinator.repos.myrepo", "update_issue_labels"): False,
            ("coordinator.repos.myrepo", "post_issue_comments"): False,
        }
        args = MagicMock(
            spec=["update_issue_labels", "post_issue_comments"],
            update_issue_labels=True,
            post_issue_comments=True,
        )
        result = resolve_issue_interaction_flags(args, Path("/tmp/project"))
        assert result == (True, True)

    @patch("mcp_coder.cli.utils.get_repository_identifier", return_value=None)
    def test_no_git_remote_falls_back_to_defaults(
        self, _mock_git_url: MagicMock
    ) -> None:
        """get_repository_identifier returns None -> (False, False)."""
        args = MagicMock(
            spec=["update_issue_labels", "post_issue_comments"],
            update_issue_labels=None,
            post_issue_comments=None,
        )
        result = resolve_issue_interaction_flags(args, Path("/tmp/project"))
        assert result == (False, False)

    @patch("mcp_coder.cli.utils.find_repo_section_by_url", return_value=None)
    @patch(
        "mcp_coder.cli.utils.get_repository_identifier",
        return_value=MagicMock(https_url="https://github.com/org/unknown-repo"),
    )
    def test_no_matching_repo_section_falls_back_to_defaults(
        self, _mock_git_url: MagicMock, mock_find: MagicMock
    ) -> None:
        """Remote URL doesn't match any config section -> (False, False)."""
        args = MagicMock(
            spec=["update_issue_labels", "post_issue_comments"],
            update_issue_labels=None,
            post_issue_comments=None,
        )
        result = resolve_issue_interaction_flags(args, Path("/tmp/project"))
        assert result == (False, False)

    @patch("mcp_coder.cli.utils.get_config_values")
    @patch(
        "mcp_coder.cli.utils.find_repo_section_by_url",
        return_value="coordinator.repos.myrepo",
    )
    @patch(
        "mcp_coder.cli.utils.get_repository_identifier",
        return_value=MagicMock(https_url="https://github.com/org/repo"),
    )
    def test_partial_cli_override(
        self,
        _mock_git_url: MagicMock,
        mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """CLI sets update_issue_labels=True, post_issue_comments=None, config has post_issue_comments=true -> (True, True)."""
        mock_config.return_value = {
            ("coordinator.repos.myrepo", "update_issue_labels"): False,
            ("coordinator.repos.myrepo", "post_issue_comments"): True,
        }
        args = MagicMock(
            spec=["update_issue_labels", "post_issue_comments"],
            update_issue_labels=True,
            post_issue_comments=None,
        )
        result = resolve_issue_interaction_flags(args, Path("/tmp/project"))
        assert result == (True, True)


class TestResolveLlmMethodCopilot:
    """Test cases for copilot provider in resolve_llm_method."""

    def test_resolve_llm_method_copilot_cli_arg(self) -> None:
        """Test that copilot CLI arg returns (copilot, 'cli argument')."""
        assert resolve_llm_method("copilot") == ("copilot", "cli argument")

    def test_resolve_llm_method_invalid_mentions_all_providers(self) -> None:
        """Test that invalid provider error mentions all three providers."""
        with pytest.raises(ValueError, match="claude") as exc_info:
            resolve_llm_method("invalid")
        error_msg = str(exc_info.value)
        assert "copilot" in error_msg
        assert "langchain" in error_msg
