"""Tests for CLI utility functions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.utils import parse_llm_method_from_args, resolve_llm_method


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

    def test_explicit_cli_arg_returned_as_is(self) -> None:
        """Test that explicit CLI arg is returned without config lookup."""
        assert resolve_llm_method("claude") == "claude"
        assert resolve_llm_method("langchain") == "langchain"

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_none_with_langchain_config(self, mock_config: MagicMock) -> None:
        """Test that None falls back to config [llm] provider."""
        mock_config.return_value = {("llm", "provider"): "langchain"}
        assert resolve_llm_method(None) == "langchain"

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_none_with_no_config(self, mock_config: MagicMock) -> None:
        """Test that None with no config defaults to claude."""
        mock_config.return_value = {("llm", "provider"): None}
        assert resolve_llm_method(None) == "claude"

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_none_with_unknown_provider(self, mock_config: MagicMock) -> None:
        """Test that unknown config provider falls through to default."""
        mock_config.return_value = {("llm", "provider"): "some_other"}
        assert resolve_llm_method(None) == "claude"


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
