"""Tests for user_config module."""

import platform
import tomllib
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.utils.user_config import (
    _format_toml_error,
    create_default_config,
    get_cache_refresh_minutes,
    get_config_file_path,
    get_config_values,
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


class TestGetConfigValues:
    """Tests for get_config_values batch function."""

    def test_get_config_values_returns_multiple_values(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test batch retrieval of multiple config values."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[github]
token = "ghp_test"

[jenkins]
server_url = "http://jenkins"
username = "admin"
""",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = get_config_values(
            [
                ("github", "token", None),
                ("jenkins", "server_url", None),
                ("jenkins", "username", None),
            ]
        )

        # Verify
        assert result[("github", "token")] == "ghp_test"
        assert result[("jenkins", "server_url")] == "http://jenkins"
        assert result[("jenkins", "username")] == "admin"

    def test_get_config_values_env_var_priority(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Environment variables take priority over config file."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text('[github]\ntoken = "file_token"', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )
        monkeypatch.setenv("GITHUB_TOKEN", "env_token")

        # Execute
        result = get_config_values([("github", "token", None)])

        # Verify
        assert result[("github", "token")] == "env_token"

    def test_get_config_values_missing_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing keys return None without raising."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text('[github]\ntoken = "test"', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = get_config_values(
            [
                ("github", "token", None),
                ("nonexistent", "key", None),
            ]
        )

        # Verify
        assert result[("github", "token")] == "test"
        assert result[("nonexistent", "key")] is None

    def test_get_config_values_nested_sections(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test dot notation for nested sections."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[coordinator.repos.mcp_coder]
repo_url = "https://github.com/test/repo"
executor_os = "linux"
""",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = get_config_values(
            [
                ("coordinator.repos.mcp_coder", "repo_url", None),
                ("coordinator.repos.mcp_coder", "executor_os", None),
            ]
        )

        # Verify
        assert (
            result[("coordinator.repos.mcp_coder", "repo_url")]
            == "https://github.com/test/repo"
        )
        assert result[("coordinator.repos.mcp_coder", "executor_os")] == "linux"

    def test_get_config_values_single_disk_read(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify config is loaded only once for multiple keys."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text('[a]\nx = "1"\n[b]\ny = "2"', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        load_count = 0
        original_load = load_config

        def counting_load() -> dict[str, object]:
            nonlocal load_count
            load_count += 1
            return original_load()

        monkeypatch.setattr("mcp_coder.utils.user_config.load_config", counting_load)

        # Execute
        get_config_values([("a", "x", None), ("b", "y", None)])

        # Verify
        assert load_count == 1  # Only one disk read

    def test_get_config_values_explicit_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test explicit env_var parameter overrides auto-detection."""
        # Setup
        monkeypatch.setenv("CUSTOM_VAR", "custom_value")

        # Execute
        result = get_config_values([("any", "key", "CUSTOM_VAR")])

        # Verify
        assert result[("any", "key")] == "custom_value"

    def test_get_config_values_empty_keys_returns_empty_dict(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty keys list returns empty dict without loading config."""
        # Setup
        load_called = False

        def mock_load() -> dict[str, object]:
            nonlocal load_called
            load_called = True
            return {}

        monkeypatch.setattr("mcp_coder.utils.user_config.load_config", mock_load)

        # Execute
        result = get_config_values([])

        # Verify
        assert result == {}
        assert not load_called  # Config was never loaded

    def test_get_config_values_all_env_vars_skips_disk(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If all keys have env vars set, config file is not read."""
        # Setup
        monkeypatch.setenv("GITHUB_TOKEN", "env_gh_token")
        monkeypatch.setenv("JENKINS_URL", "env_jenkins_url")

        load_called = False

        def mock_load() -> dict[str, object]:
            nonlocal load_called
            load_called = True
            return {}

        monkeypatch.setattr("mcp_coder.utils.user_config.load_config", mock_load)

        # Execute
        result = get_config_values(
            [
                ("github", "token", None),
                ("jenkins", "server_url", None),
            ]
        )

        # Verify
        assert result[("github", "token")] == "env_gh_token"
        assert result[("jenkins", "server_url")] == "env_jenkins_url"
        assert not load_called  # Config was never loaded (lazy loading)

    def test_get_config_values_converts_non_string_to_string(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-string values (int, bool) are converted to string."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "[settings]\ntimeout = 30\ndebug = true", encoding="utf-8"
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = get_config_values(
            [
                ("settings", "timeout", None),
                ("settings", "debug", None),
            ]
        )

        # Verify
        assert result[("settings", "timeout")] == "30"
        assert result[("settings", "debug")] == "True"


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


class TestGetCacheRefreshMinutes:
    """Tests for get_cache_refresh_minutes function."""

    def test_get_cache_refresh_minutes_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 1440 when config not set."""
        # Setup - empty config file
        config_file = tmp_path / "config.toml"
        config_file.write_text("", encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = get_cache_refresh_minutes()

        # Verify
        assert result == 1440

    def test_get_cache_refresh_minutes_from_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns configured value when set."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "[coordinator]\ncache_refresh_minutes = 60\n", encoding="utf-8"
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = get_cache_refresh_minutes()

        # Verify
        assert result == 60

    def test_get_cache_refresh_minutes_invalid_value(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 1440 for non-integer values."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[coordinator]\ncache_refresh_minutes = "not_a_number"\n', encoding="utf-8"
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = get_cache_refresh_minutes()

        # Verify
        assert result == 1440

    def test_get_cache_refresh_minutes_negative_value(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 1440 for negative values."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "[coordinator]\ncache_refresh_minutes = -10\n", encoding="utf-8"
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = get_cache_refresh_minutes()

        # Verify
        assert result == 1440

    def test_get_cache_refresh_minutes_zero_value(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 1440 for zero value."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "[coordinator]\ncache_refresh_minutes = 0\n", encoding="utf-8"
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        result = get_cache_refresh_minutes()

        # Verify
        assert result == 1440
