"""Tests for user_config module."""

import platform
import tomllib
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from mcp_coder.utils.user_config import (
    _format_toml_error,
    create_default_config,
    get_config_file_path,
    get_config_value,
    load_config,
)


class TestFormatTomlError:
    """Tests for _format_toml_error helper function."""

    def test_format_includes_file_path(self, tmp_path: Path) -> None:
        """Error message includes the file path."""
        # Setup - create a file with invalid TOML to generate real error
        config_file = tmp_path / "config.toml"
        config_file.write_text('key = "unclosed string\n', encoding="utf-8")

        # Parse to get real TOMLDecodeError
        try:
            with open(config_file, "rb") as f:
                tomllib.load(f)
            pytest.fail("Expected TOMLDecodeError")
        except tomllib.TOMLDecodeError as error:
            # Execute
            result = _format_toml_error(config_file, error)

            # Verify
            assert str(config_file) in result
            assert 'File "' in result

    def test_format_includes_line_number(self, tmp_path: Path) -> None:
        """Error message includes line number from error."""
        # Setup - create file with error on line 3
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'line1 = "ok"\nline2 = "ok"\nline3 = "unclosed\n', encoding="utf-8"
        )

        try:
            with open(config_file, "rb") as f:
                tomllib.load(f)
            pytest.fail("Expected TOMLDecodeError")
        except tomllib.TOMLDecodeError as error:
            # Execute
            result = _format_toml_error(config_file, error)

            # Verify - line number should be in the output
            assert "line 3" in result

    def test_format_includes_error_line_content(self, tmp_path: Path) -> None:
        """Error message includes the actual line content."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text('my_special_key = "unclosed\n', encoding="utf-8")

        try:
            with open(config_file, "rb") as f:
                tomllib.load(f)
            pytest.fail("Expected TOMLDecodeError")
        except tomllib.TOMLDecodeError as error:
            # Execute
            result = _format_toml_error(config_file, error)

            # Verify - the line content should be included
            assert "my_special_key" in result

    def test_format_includes_pointer_at_column(self, tmp_path: Path) -> None:
        """Error message includes ^ pointer at error column."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text('key = "unclosed\n', encoding="utf-8")

        try:
            with open(config_file, "rb") as f:
                tomllib.load(f)
            pytest.fail("Expected TOMLDecodeError")
        except tomllib.TOMLDecodeError as error:
            # Execute
            result = _format_toml_error(config_file, error)

            # Verify - should have a caret pointer
            assert "^" in result

    def test_format_handles_file_read_error(self, tmp_path: Path) -> None:
        """Gracefully handles if file cannot be read for context."""
        # Setup - create error but then delete file
        config_file = tmp_path / "config.toml"
        config_file.write_text('key = "unclosed\n', encoding="utf-8")

        try:
            with open(config_file, "rb") as f:
                tomllib.load(f)
            pytest.fail("Expected TOMLDecodeError")
        except tomllib.TOMLDecodeError as error:
            # Delete file so it can't be read for context
            config_file.unlink()

            # Execute - should not raise
            result = _format_toml_error(config_file, error)

            # Verify - should still have file path and error message
            assert str(config_file) in result
            assert "TOML parse error" in result

    def test_format_handles_line_out_of_range(self, tmp_path: Path) -> None:
        """Handles when error line number exceeds file lines."""
        # Setup - create error, then modify file to have fewer lines
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'line1 = "ok"\nline2 = "ok"\nline3 = "unclosed\n', encoding="utf-8"
        )

        try:
            with open(config_file, "rb") as f:
                tomllib.load(f)
            pytest.fail("Expected TOMLDecodeError")
        except tomllib.TOMLDecodeError as error:
            # Reduce file to 1 line so error line (3) is out of range
            config_file.write_text('only_one_line = "ok"\n', encoding="utf-8")

            # Execute - should not raise
            result = _format_toml_error(config_file, error)

            # Verify - should have file path and error message
            assert str(config_file) in result
            assert "TOML parse error" in result


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_returns_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Successfully loads valid TOML config."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text('[github]\ntoken = "ghp_test123"\n', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = load_config()

        # Verify
        assert isinstance(result, dict)
        assert result == {"github": {"token": "ghp_test123"}}

    def test_load_config_returns_empty_dict_if_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns empty dict when config file doesn't exist."""
        # Setup - point to non-existent file
        config_file = tmp_path / "nonexistent.toml"
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = load_config()

        # Verify
        assert result == {}

    def test_load_config_raises_on_invalid_toml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises ValueError on TOML parse error."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text('key = "unclosed\n', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            load_config()

        # Should have formatted error message
        assert "TOML parse error" in str(exc_info.value)

    def test_load_config_error_includes_file_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ValueError message includes the config file path."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text('key = "unclosed\n', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            load_config()

        # Should include file path
        assert str(config_file) in str(exc_info.value)

    def test_load_config_error_includes_line_content(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ValueError message includes the error line content."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text('my_unique_key = "unclosed\n', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            load_config()

        # Should include line content
        assert "my_unique_key" in str(exc_info.value)

    def test_load_config_preserves_nested_structure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Correctly loads nested TOML sections."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_content = """[github]
token = "ghp_test"

[coordinator.repos.mcp_coder]
repo_url = "https://github.com/test/mcp_coder.git"
executor_os = "linux"
"""
        config_file.write_text(config_content, encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = load_config()

        # Verify nested structure is preserved
        assert result["github"]["token"] == "ghp_test"
        assert (
            result["coordinator"]["repos"]["mcp_coder"]["repo_url"]
            == "https://github.com/test/mcp_coder.git"
        )
        assert result["coordinator"]["repos"]["mcp_coder"]["executor_os"] == "linux"


class TestGetConfigFilePath:
    """Tests for get_config_file_path function."""

    def test_get_config_file_path_returns_correct_path(self) -> None:
        """Test that config file path is returned correctly."""
        # Execute
        result = get_config_file_path()

        # Verify platform-specific behavior
        if platform.system() == "Windows":
            expected = Path.home() / ".mcp_coder" / "config.toml"
            assert result == expected
            assert ".mcp_coder" in str(result)
        else:
            # Linux/macOS - XDG Base Directory Specification
            expected = Path.home() / ".config" / "mcp_coder" / "config.toml"
            assert result == expected
            assert "mcp_coder" in str(result)

        # Common assertions
        assert result.name == "config.toml"


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

[coordinator.repos.mcp_coder]
repo_url = "https://github.com/test/mcp_coder.git"
test_job = "MCP_Coder/mcp-coder-test-job"
github_credentials_id = "github-general-pat"

[coordinator.repos.test_repo]
repo_url = "https://github.com/test/test_repo.git"
test_job = "Test/test-job"
github_credentials_id = "github-pat"
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
    def test_get_config_value_invalid_toml_raises(
        self, mock_get_path: MagicMock
    ) -> None:
        """Test that ValueError is raised when TOML file is invalid."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        invalid_toml = b"[invalid toml content without closing bracket"

        with patch("builtins.open", mock_open(read_data=invalid_toml)):
            # Execute & Verify
            with pytest.raises(ValueError) as exc_info:
                get_config_value("tokens", "github")

            # Verify error message includes file path
            assert str(mock_path) in str(exc_info.value)

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_io_error_raises(self, mock_get_path: MagicMock) -> None:
        """Test that ValueError is raised when file cannot be read (IO error)."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            # Execute & Verify
            with pytest.raises(ValueError) as exc_info:
                get_config_value("tokens", "github")

            # Verify error message includes file path
            assert str(mock_path) in str(exc_info.value)

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

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_nested_section_success(
        self, mock_get_path: MagicMock, sample_config_content: str
    ) -> None:
        """Test successful retrieval from nested section using dot notation."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        with patch(
            "builtins.open", mock_open(read_data=sample_config_content.encode())
        ):
            # Execute
            result = get_config_value("coordinator.repos.mcp_coder", "repo_url")

            # Verify
            assert result == "https://github.com/test/mcp_coder.git"

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_nested_section_different_repo(
        self, mock_get_path: MagicMock, sample_config_content: str
    ) -> None:
        """Test retrieval from different nested repository."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        with patch(
            "builtins.open", mock_open(read_data=sample_config_content.encode())
        ):
            # Execute
            result = get_config_value("coordinator.repos.test_repo", "test_job")

            # Verify
            assert result == "Test/test-job"

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_nested_section_missing_intermediate(
        self, mock_get_path: MagicMock, sample_config_content: str
    ) -> None:
        """Test that None is returned when intermediate section doesn't exist."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        with patch(
            "builtins.open", mock_open(read_data=sample_config_content.encode())
        ):
            # Execute - 'nonexistent' is not a key in coordinator
            result = get_config_value("coordinator.nonexistent.mcp_coder", "repo_url")

            # Verify
            assert result is None

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_nested_section_missing_leaf(
        self, mock_get_path: MagicMock, sample_config_content: str
    ) -> None:
        """Test that None is returned when leaf section doesn't exist."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        with patch(
            "builtins.open", mock_open(read_data=sample_config_content.encode())
        ):
            # Execute - 'nonexistent_repo' doesn't exist in coordinator.repos
            result = get_config_value("coordinator.repos.nonexistent_repo", "repo_url")

            # Verify
            assert result is None

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_get_config_value_nested_section_missing_key(
        self, mock_get_path: MagicMock, sample_config_content: str
    ) -> None:
        """Test that None is returned when key doesn't exist in nested section."""
        # Setup
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path

        with patch(
            "builtins.open", mock_open(read_data=sample_config_content.encode())
        ):
            # Execute - section exists but key doesn't
            result = get_config_value("coordinator.repos.mcp_coder", "nonexistent_key")

            # Verify
            assert result is None


class TestCreateDefaultConfig:
    """Tests for create_default_config function."""

    def test_create_default_config_creates_directory_and_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that config directory and file are created."""
        # Setup
        config_dir = tmp_path / ".mcp_coder"
        config_file = config_dir / "config.toml"

        # Mock get_config_file_path to return test location
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = create_default_config()

        # Verify
        assert result is True
        assert config_dir.exists()
        assert config_file.exists()
        assert config_file.is_file()

    def test_create_default_config_returns_true_on_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful creation returns True."""
        # Setup
        config_file = tmp_path / ".mcp_coder" / "config.toml"

        # Mock get_config_file_path to return test location
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = create_default_config()

        # Verify
        assert result is True

    def test_create_default_config_returns_false_if_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that existing config returns False (no overwrite)."""
        # Setup
        config_dir = tmp_path / ".mcp_coder"
        config_file = config_dir / "config.toml"
        config_dir.mkdir(parents=True)
        config_file.write_text("[existing]\nvalue = 'test'", encoding="utf-8")

        # Mock get_config_file_path to return test location
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = create_default_config()

        # Verify
        assert result is False
        # Verify existing content was not overwritten
        content = config_file.read_text(encoding="utf-8")
        assert "[existing]" in content
        assert "value = 'test'" in content

    def test_create_default_config_content_has_all_sections(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that created config has all required sections."""
        # Setup
        config_file = tmp_path / ".mcp_coder" / "config.toml"

        # Mock get_config_file_path to return test location
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        create_default_config()

        # Verify - Load and parse TOML content
        with open(config_file, "rb") as f:
            config = tomllib.load(f)

        # Assert all required sections present
        assert "jenkins" in config
        assert "coordinator" in config
        assert "repos" in config["coordinator"]
        assert "mcp_coder" in config["coordinator"]["repos"]
        assert "mcp_server_filesystem" in config["coordinator"]["repos"]

    def test_create_default_config_content_has_example_repos(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that config includes example repository configurations."""
        # Setup
        config_file = tmp_path / ".mcp_coder" / "config.toml"

        # Mock get_config_file_path to return test location
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        create_default_config()

        # Verify - Load and parse TOML content
        with open(config_file, "rb") as f:
            config = tomllib.load(f)

        # Check mcp_coder repo config
        mcp_coder_repo = config["coordinator"]["repos"]["mcp_coder"]
        assert "repo_url" in mcp_coder_repo
        assert "executor_job_path" in mcp_coder_repo
        assert "github_credentials_id" in mcp_coder_repo

        # Check mcp_server_filesystem repo config
        filesystem_repo = config["coordinator"]["repos"]["mcp_server_filesystem"]
        assert "repo_url" in filesystem_repo
        assert "executor_job_path" in filesystem_repo
        assert "github_credentials_id" in filesystem_repo

    def test_create_default_config_handles_permission_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test graceful handling of permission errors."""
        # Setup
        config_file = tmp_path / ".mcp_coder" / "config.toml"

        # Mock get_config_file_path to return test location
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Mock Path.write_text to raise PermissionError
        original_write_text = Path.write_text

        def mock_write_text(self: Path, *args: object, **kwargs: object) -> int:
            if self == config_file:
                raise PermissionError("Permission denied")
            return original_write_text(self, *args, **kwargs)  # type: ignore

        monkeypatch.setattr(Path, "write_text", mock_write_text)

        # Execute & Verify - Should raise OSError
        with pytest.raises(OSError):
            create_default_config()
