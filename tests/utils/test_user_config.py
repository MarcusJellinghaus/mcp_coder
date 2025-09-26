"""Tests for user_config module."""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from mcp_coder.utils.user_config import get_config_file_path, get_config_value


class TestGetConfigFilePath:
    """Tests for get_config_file_path function."""

    def test_get_config_file_path_returns_correct_path(self) -> None:
        """Test that config file path is returned correctly."""
        # Execute
        result = get_config_file_path()

        # Verify
        expected = Path.home() / ".mcp_coder" / "config.toml"
        assert result == expected
        assert result.name == "config.toml"
        assert ".mcp_coder" in str(result)


class TestGetConfigValue:
    """Tests for get_config_value function."""

    @pytest.fixture
    def sample_config_content(self) -> str:
        """Sample TOML config content for testing."""
        return """
[tokens]
github = "ghp_test_token_123"
api_key = "test_api_key_456"

[settings]
default_branch = "main"
timeout = 30
debug = true
"""

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_success_string(
        self, mock_get_path: MagicMock, sample_config_content: str
    ) -> None:
        """Test successful retrieval of string configuration value."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        with patch(
            "builtins.open", mock_open(read_data=sample_config_content.encode())
        ):
            # Execute
            result = get_config_value("tokens", "github")

            # Verify
            assert result == "ghp_test_token_123"

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_success_non_string(
        self, mock_get_path: MagicMock, sample_config_content: str
    ) -> None:
        """Test successful retrieval and conversion of non-string value."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        with patch(
            "builtins.open", mock_open(read_data=sample_config_content.encode())
        ):
            # Execute - timeout is an integer in TOML, should be converted to string
            result = get_config_value("settings", "timeout")

            # Verify
            assert result == "30"

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_success_boolean(
        self, mock_get_path: MagicMock, sample_config_content: str
    ) -> None:
        """Test successful retrieval and conversion of boolean value."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        with patch(
            "builtins.open", mock_open(read_data=sample_config_content.encode())
        ):
            # Execute - debug is a boolean in TOML, should be converted to string
            result = get_config_value("settings", "debug")

            # Verify
            assert result == "True"

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_missing_file(self, mock_get_path: MagicMock) -> None:
        """Test that None is returned when config file doesn't exist."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        mock_get_path.return_value = mock_path

        # Execute
        result = get_config_value("tokens", "github")

        # Verify
        assert result is None

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_missing_section(
        self, mock_get_path: MagicMock, sample_config_content: str
    ) -> None:
        """Test that None is returned when section doesn't exist."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        with patch(
            "builtins.open", mock_open(read_data=sample_config_content.encode())
        ):
            # Execute
            result = get_config_value("nonexistent_section", "some_key")

            # Verify
            assert result is None

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_missing_key(
        self, mock_get_path: MagicMock, sample_config_content: str
    ) -> None:
        """Test that None is returned when key doesn't exist in section."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        with patch(
            "builtins.open", mock_open(read_data=sample_config_content.encode())
        ):
            # Execute
            result = get_config_value("tokens", "nonexistent_key")

            # Verify
            assert result is None

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_invalid_toml(self, mock_get_path: MagicMock) -> None:
        """Test that None is returned when TOML file is invalid."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        invalid_toml = b"[invalid toml content without closing bracket"

        with patch("builtins.open", mock_open(read_data=invalid_toml)):
            # Execute
            result = get_config_value("tokens", "github")

            # Verify
            assert result is None

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_io_error(self, mock_get_path: MagicMock) -> None:
        """Test that None is returned when file cannot be read (IO error)."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            # Execute
            result = get_config_value("tokens", "github")

            # Verify
            assert result is None

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_null_value(self, mock_get_path: MagicMock) -> None:
        """Test that None is returned when value is null in TOML."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        # TOML content with null value isn't valid, but we test with empty string
        toml_content = b'[section]\nkey = ""'

        with patch("builtins.open", mock_open(read_data=toml_content)):
            # Execute
            result = get_config_value("section", "key")

            # Verify - empty string should be converted to string
            assert result == ""
