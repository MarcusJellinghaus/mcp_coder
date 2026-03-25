"""Tests for CLI utility functions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.utils import (
    parse_llm_method_from_args,
    resolve_llm_method,
    resolve_mcp_config_path,
)
from mcp_coder.utils.user_config import _get_standard_env_var


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


class TestResolveMcpConfigPath:
    """Test cases for resolve_mcp_config_path function."""

    def test_resolve_mcp_config_auto_detect_project_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that .mcp.json in project_dir is auto-detected when mcp_config is None."""
        monkeypatch.delenv("MCP_CODER_MCP_CONFIG", raising=False)
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text("{}")

        result = resolve_mcp_config_path(None, project_dir=str(tmp_path))
        assert result == str(mcp_json.resolve())

    def test_resolve_mcp_config_auto_detect_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that .mcp.json in CWD is auto-detected when no project_dir given."""
        monkeypatch.delenv("MCP_CODER_MCP_CONFIG", raising=False)
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text("{}")
        monkeypatch.chdir(tmp_path)

        result = resolve_mcp_config_path(None)
        assert result == str(mcp_json.resolve())

    def test_resolve_mcp_config_auto_detect_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that None is returned when no .mcp.json exists."""
        monkeypatch.delenv("MCP_CODER_MCP_CONFIG", raising=False)
        monkeypatch.chdir(tmp_path)

        result = resolve_mcp_config_path(None)
        assert result is None

    def test_resolve_mcp_config_explicit_still_works(self, tmp_path: Path) -> None:
        """Test that explicit mcp_config path still resolves as before."""
        mcp_json = tmp_path / "custom.json"
        mcp_json.write_text("{}")

        result = resolve_mcp_config_path(str(mcp_json))
        assert result == str(mcp_json.resolve())

    def test_resolve_mcp_config_explicit_not_found(self) -> None:
        """Test that explicit path to non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            resolve_mcp_config_path("/nonexistent/path/config.json")

    def test_resolve_mcp_config_env_var(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that MCP_CODER_MCP_CONFIG env var is used when mcp_config is None."""
        config_file = tmp_path / "mcp_config.json"
        config_file.write_text("{}")
        monkeypatch.setenv("MCP_CODER_MCP_CONFIG", str(config_file))

        result = resolve_mcp_config_path(None)
        assert result == str(config_file.resolve())

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_mcp_config_config_file(
        self, mock_config: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that [mcp] default_config_path from config file is used."""
        monkeypatch.delenv("MCP_CODER_MCP_CONFIG", raising=False)
        config_file = tmp_path / "mcp_from_config.json"
        config_file.write_text("{}")
        mock_config.return_value = {("mcp", "default_config_path"): str(config_file)}
        # No .mcp.json in tmp_path
        monkeypatch.chdir(tmp_path)

        result = resolve_mcp_config_path(None)
        assert result == str(config_file.resolve())

    def test_resolve_mcp_config_cli_overrides_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that explicit CLI mcp_config overrides env var."""
        cli_file = tmp_path / "cli_config.json"
        cli_file.write_text("{}")
        env_file = tmp_path / "env_config.json"
        env_file.write_text("{}")
        monkeypatch.setenv("MCP_CODER_MCP_CONFIG", str(env_file))

        result = resolve_mcp_config_path(str(cli_file))
        assert result == str(cli_file.resolve())

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_mcp_config_env_overrides_config(
        self, mock_config: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that env var takes precedence over config file."""
        env_file = tmp_path / "env_config.json"
        env_file.write_text("{}")
        cfg_file = tmp_path / "cfg_config.json"
        cfg_file.write_text("{}")
        monkeypatch.setenv("MCP_CODER_MCP_CONFIG", str(env_file))
        mock_config.return_value = {("mcp", "default_config_path"): str(cfg_file)}

        result = resolve_mcp_config_path(None)
        assert result == str(env_file.resolve())

    def test_resolve_mcp_config_env_missing_file_falls_back(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that missing env var file warns and falls back to auto-detect."""
        monkeypatch.setenv("MCP_CODER_MCP_CONFIG", "/nonexistent/mcp.json")
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text("{}")
        monkeypatch.chdir(tmp_path)

        import logging

        with caplog.at_level(logging.WARNING, logger="mcp_coder.cli.utils"):
            result = resolve_mcp_config_path(None)

        assert result == str(mcp_json.resolve())
        assert "MCP_CODER_MCP_CONFIG" in caplog.text
        assert "file not found" in caplog.text

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_mcp_config_config_missing_file_falls_back(
        self,
        mock_config: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that missing config file path warns and falls back to auto-detect."""
        monkeypatch.delenv("MCP_CODER_MCP_CONFIG", raising=False)
        mock_config.return_value = {
            ("mcp", "default_config_path"): "/nonexistent/mcp.json"
        }
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text("{}")
        monkeypatch.chdir(tmp_path)

        import logging

        with caplog.at_level(logging.WARNING, logger="mcp_coder.cli.utils"):
            result = resolve_mcp_config_path(None)

        assert result == str(mcp_json.resolve())
        assert "default_config_path" in caplog.text
        assert "file not found" in caplog.text

    def test_get_standard_env_var_mcp_config(self) -> None:
        """Test that _get_standard_env_var maps mcp/default_config_path correctly."""
        result = _get_standard_env_var("mcp", "default_config_path")
        assert result == "MCP_CODER_MCP_CONFIG"


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
