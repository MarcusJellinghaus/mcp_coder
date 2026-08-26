"""Tests for user_config module."""

import tomllib
from pathlib import Path

import pytest

from mcp_coder.utils.user_config import (
    _format_toml_error,
    get_cache_refresh_minutes,
    get_config_file_path,
    get_config_values,
    load_config,
)


class TestFormatTomlError:
    """Tests for _format_toml_error helper function."""

    def test_format_includes_all_error_components(self, tmp_path: Path) -> None:
        """Error message includes file path, line number, content, and pointer."""
        # Setup - create file with error on line 3 to test line number extraction
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'line1 = "ok"\nline2 = "ok"\nmy_special_key = "unclosed\n',
            encoding="utf-8",
        )

        # Parse to get real TOMLDecodeError
        try:
            with open(config_file, "rb") as f:
                tomllib.load(f)
            pytest.fail("Expected TOMLDecodeError")
        except tomllib.TOMLDecodeError as error:
            # Execute
            result = _format_toml_error(config_file, error)

            # Verify all components are present
            assert str(config_file) in result  # file path
            assert 'File "' in result  # file path format
            assert "line 3" in result  # line number
            assert "my_special_key" in result  # line content
            assert "^" in result  # caret pointer

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

    def test_format_hints_at_smart_quotes(self, tmp_path: Path) -> None:
        """Curly quotes on the error line produce the smart-quote hint."""
        # Setup - value delimited by U+201C / U+201D instead of straight quotes
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "[llm.langchain]\nbase_url = \u201chttps://relay/v1\u201d\n",
            encoding="utf-8",
        )

        try:
            with open(config_file, "rb") as f:
                tomllib.load(f)
            pytest.fail("Expected TOMLDecodeError")
        except tomllib.TOMLDecodeError as error:
            # Execute
            result = _format_toml_error(config_file, error)

            # Verify - smart-quote hint present, backslash hint absent
            assert "Curly/smart quotes" in result
            assert "Use straight quotes" in result
            assert "Backslashes in paths" not in result

    def test_format_hints_at_single_smart_quotes(self, tmp_path: Path) -> None:
        """Curly single quotes (U+2018/U+2019) also trigger the hint."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "[llm.langchain]\nmodel = \u2018gpt-4o\u2019\n", encoding="utf-8"
        )

        try:
            with open(config_file, "rb") as f:
                tomllib.load(f)
            pytest.fail("Expected TOMLDecodeError")
        except tomllib.TOMLDecodeError as error:
            # Execute
            result = _format_toml_error(config_file, error)

            # Verify
            assert "Curly/smart quotes" in result

    def test_format_backslash_hint_without_smart_quote_hint(
        self, tmp_path: Path
    ) -> None:
        """An unescaped Windows path keeps the backslash hint only."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text('path = "C:\\Users\\name"\n', encoding="utf-8")

        try:
            with open(config_file, "rb") as f:
                tomllib.load(f)
            pytest.fail("Expected TOMLDecodeError")
        except tomllib.TOMLDecodeError as error:
            # Execute
            result = _format_toml_error(config_file, error)

            # Verify - only the backslash hint
            assert "Backslashes in paths" in result
            assert "Curly/smart quotes" not in result

    def test_format_plain_syntax_error_has_no_hints(self, tmp_path: Path) -> None:
        """A plain syntax error renders neither hint."""
        # Setup - missing '=' between key and value
        config_file = tmp_path / "config.toml"
        config_file.write_text('key "value"\n', encoding="utf-8")

        try:
            with open(config_file, "rb") as f:
                tomllib.load(f)
            pytest.fail("Expected TOMLDecodeError")
        except tomllib.TOMLDecodeError as error:
            # Execute
            result = _format_toml_error(config_file, error)

            # Verify
            assert "Curly/smart quotes" not in result
            assert "Backslashes in paths" not in result

    def test_format_smart_quotes_unreadable_file_has_no_hint(
        self, tmp_path: Path
    ) -> None:
        """Unreadable file skips the smart-quote hint without crashing."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "base_url = \u201chttps://relay/v1\u201d\n", encoding="utf-8"
        )

        try:
            with open(config_file, "rb") as f:
                tomllib.load(f)
            pytest.fail("Expected TOMLDecodeError")
        except tomllib.TOMLDecodeError as error:
            # Delete file so the error line can't be read
            config_file.unlink()

            # Execute - should not raise
            result = _format_toml_error(config_file, error)

            # Verify - no hint, but the error is still reported
            assert "TOML parse error" in result
            assert "Curly/smart quotes" not in result


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

    def test_load_config_raises_with_detailed_error_on_invalid_toml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises ValueError with file path and line content on TOML parse error."""
        # Setup
        config_file = tmp_path / "config.toml"
        config_file.write_text('my_unique_key = "unclosed\n', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            load_config()

        error_message = str(exc_info.value)
        assert "TOML parse error" in error_message  # formatted error
        assert str(config_file) in error_message  # file path included
        assert "my_unique_key" in error_message  # line content included

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


def test_get_config_file_path_uses_shim() -> None:
    """get_config_file_path delegates to the user_app_data shim."""
    from mcp_coder.utils.user_app_data import get_user_app_data_dir

    assert get_config_file_path() == get_user_app_data_dir("mcp_coder") / "config.toml"


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
        # Ensure env vars don't override config file values in this test
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("JENKINS_SERVER_URL", raising=False)
        monkeypatch.delenv("JENKINS_URL", raising=False)
        monkeypatch.delenv("JENKINS_USERNAME", raising=False)
        monkeypatch.delenv("JENKINS_USER", raising=False)

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
        # Ensure GITHUB_TOKEN env var doesn't override config file value
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

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

    def test_get_config_values_preserves_native_types(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Native TOML types (int, bool) are preserved, not converted to string."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "[settings]\ntimeout = 30\ndebug = true", encoding="utf-8"
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        result = get_config_values(
            [
                ("settings", "timeout", None),
                ("settings", "debug", None),
            ]
        )

        assert result[("settings", "timeout")] == 30
        assert result[("settings", "debug")] is True


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

    @pytest.mark.parametrize(
        "config_value,description",
        [
            ("-10", "negative value"),
            ("0", "zero value"),
        ],
    )
    def test_get_cache_refresh_minutes_invalid_returns_default(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        config_value: str,
        description: str,
    ) -> None:
        """Returns 1440 for invalid values (negative, zero)."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            f"[coordinator]\ncache_refresh_minutes = {config_value}\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        result = get_cache_refresh_minutes()

        assert result == 1440, f"Expected default 1440 for {description}"

    def test_get_cache_refresh_minutes_string_raises_valueerror(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """String in int field raises ValueError at schema validation."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[coordinator]\ncache_refresh_minutes = "not_a_number"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        with pytest.raises(ValueError, match="expected int.*got str"):
            get_cache_refresh_minutes()
