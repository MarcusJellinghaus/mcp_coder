"""Tests for CLI path resolver utilities --- `resolve_mcp_config_path` and `resolve_claude_settings_path`."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.utils import (
    resolve_claude_settings_path,
    resolve_mcp_config_path,
)
from mcp_coder.utils.user_config import _CONFIG_SCHEMA


class TestResolveMcpConfigPath:
    """Test cases for resolve_mcp_config_path function."""

    def test_resolve_mcp_config_auto_detect_project_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Auto-detect finds .mcp.json in project_dir even when CWD differs."""
        monkeypatch.delenv("MCP_CODER_MCP_CONFIG", raising=False)
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        mcp_json = project_dir / ".mcp.json"
        mcp_json.write_text("{}")
        monkeypatch.chdir(cwd)

        result = resolve_mcp_config_path(None, project_dir=str(project_dir))
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
        """Test that explicit path to non-existent file raises FileNotFoundError.

        The error message must include both the project directory and the
        current directory to aid debugging path-resolution issues.
        """
        with pytest.raises(FileNotFoundError) as excinfo:
            resolve_mcp_config_path("/nonexistent/path/config.json")
        assert "Project directory:" in str(excinfo.value)
        assert "Current directory:" in str(excinfo.value)

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

    # ---- Relative path × CWD ≠ project_dir → resolves against project_dir ----

    def test_relative_cli_resolves_against_project_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Relative --mcp-config resolves against project_dir, not CWD."""
        monkeypatch.delenv("MCP_CODER_MCP_CONFIG", raising=False)
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        mcp_json = project_dir / ".mcp.json"
        mcp_json.write_text("{}")
        monkeypatch.chdir(cwd)

        result = resolve_mcp_config_path(".mcp.json", project_dir=str(project_dir))
        assert result == str(mcp_json.resolve())

    def test_relative_env_resolves_against_project_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Relative MCP_CODER_MCP_CONFIG resolves against project_dir, not CWD."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        mcp_json = project_dir / ".mcp.json"
        mcp_json.write_text("{}")
        monkeypatch.setenv("MCP_CODER_MCP_CONFIG", ".mcp.json")
        monkeypatch.chdir(cwd)

        result = resolve_mcp_config_path(None, project_dir=str(project_dir))
        assert result == str(mcp_json.resolve())

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_relative_config_resolves_against_project_dir(
        self,
        mock_config: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Relative [mcp] default_config_path resolves against project_dir, not CWD."""
        monkeypatch.delenv("MCP_CODER_MCP_CONFIG", raising=False)
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        mcp_json = project_dir / ".mcp.json"
        mcp_json.write_text("{}")
        mock_config.return_value = {("mcp", "default_config_path"): ".mcp.json"}
        monkeypatch.chdir(cwd)

        result = resolve_mcp_config_path(None, project_dir=str(project_dir))
        assert result == str(mcp_json.resolve())

    def test_autodetect_resolves_against_project_dir_when_cwd_differs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Auto-detect uses project_dir as the base, not CWD."""
        monkeypatch.delenv("MCP_CODER_MCP_CONFIG", raising=False)
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        # .mcp.json only exists in project_dir; CWD has none
        mcp_json = project_dir / ".mcp.json"
        mcp_json.write_text("{}")
        monkeypatch.chdir(cwd)

        result = resolve_mcp_config_path(None, project_dir=str(project_dir))
        assert result == str(mcp_json.resolve())

    # ---- Relative path × project_dir=None → falls back to CWD ----

    def test_relative_cli_falls_back_to_cwd_when_no_project_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Relative --mcp-config falls back to CWD when project_dir is None."""
        monkeypatch.delenv("MCP_CODER_MCP_CONFIG", raising=False)
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text("{}")
        monkeypatch.chdir(tmp_path)

        result = resolve_mcp_config_path(".mcp.json")
        assert result == str(mcp_json.resolve())

    def test_relative_env_falls_back_to_cwd_when_no_project_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Relative MCP_CODER_MCP_CONFIG falls back to CWD when project_dir is None."""
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text("{}")
        monkeypatch.setenv("MCP_CODER_MCP_CONFIG", ".mcp.json")
        monkeypatch.chdir(tmp_path)

        result = resolve_mcp_config_path(None)
        assert result == str(mcp_json.resolve())

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_relative_config_falls_back_to_cwd_when_no_project_dir(
        self,
        mock_config: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Relative [mcp] default_config_path falls back to CWD when project_dir is None."""
        monkeypatch.delenv("MCP_CODER_MCP_CONFIG", raising=False)
        # Use a non-.mcp.json filename so autodetect can't accidentally pick it up.
        mcp_json = tmp_path / "elsewhere.json"
        mcp_json.write_text("{}")
        mock_config.return_value = {("mcp", "default_config_path"): "elsewhere.json"}
        monkeypatch.chdir(tmp_path)

        result = resolve_mcp_config_path(None)
        assert result == str(mcp_json.resolve())

    def test_autodetect_falls_back_to_cwd_when_no_project_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Auto-detect falls back to CWD when project_dir is None."""
        monkeypatch.delenv("MCP_CODER_MCP_CONFIG", raising=False)
        mcp_json = tmp_path / ".mcp.json"
        mcp_json.write_text("{}")
        monkeypatch.chdir(tmp_path)

        result = resolve_mcp_config_path(None)
        assert result == str(mcp_json.resolve())

    def test_schema_has_mcp_config_env_var(self) -> None:
        """Test that schema maps mcp/default_config_path to MCP_CODER_MCP_CONFIG."""
        assert (
            _CONFIG_SCHEMA["mcp"]["default_config_path"].env_var
            == "MCP_CODER_MCP_CONFIG"
        )


class TestResolveClaudeSettingsPath:
    """Test cases for resolve_claude_settings_path function."""

    def test_resolve_claude_settings_explicit_absolute(self, tmp_path: Path) -> None:
        """Explicit absolute path is returned as-is."""
        settings = tmp_path / "settings.json"
        settings.write_text("{}")

        result = resolve_claude_settings_path(str(settings))
        assert result == str(settings.resolve())

    def test_resolve_claude_settings_explicit_relative_against_project_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Explicit relative path resolves against project_dir, not CWD."""
        monkeypatch.delenv("MCP_CODER_CLAUDE_SETTINGS", raising=False)
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        settings = project_dir / "settings.json"
        settings.write_text("{}")
        monkeypatch.chdir(cwd)

        result = resolve_claude_settings_path(
            "settings.json", project_dir=str(project_dir)
        )
        assert result == str(settings.resolve())

    def test_resolve_claude_settings_explicit_relative_falls_back_to_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Explicit relative path falls back to CWD when project_dir is None."""
        monkeypatch.delenv("MCP_CODER_CLAUDE_SETTINGS", raising=False)
        settings = tmp_path / "settings.json"
        settings.write_text("{}")
        monkeypatch.chdir(tmp_path)

        result = resolve_claude_settings_path("settings.json")
        assert result == str(settings.resolve())

    def test_resolve_claude_settings_explicit_not_found(self) -> None:
        """Explicit path to non-existent file raises FileNotFoundError.

        The error message must include both the project directory and the
        current directory to aid debugging path-resolution issues.
        """
        with pytest.raises(FileNotFoundError) as excinfo:
            resolve_claude_settings_path("/nonexistent/path/settings.json")
        assert "Project directory:" in str(excinfo.value)
        assert "Current directory:" in str(excinfo.value)

    def test_resolve_claude_settings_env_var_absolute(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP_CODER_CLAUDE_SETTINGS env var (absolute) is used when settings_file is None."""
        settings = tmp_path / "env_settings.json"
        settings.write_text("{}")
        monkeypatch.setenv("MCP_CODER_CLAUDE_SETTINGS", str(settings))

        result = resolve_claude_settings_path(None)
        assert result == str(settings.resolve())

    def test_resolve_claude_settings_env_var_relative(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Relative MCP_CODER_CLAUDE_SETTINGS resolves against project_dir, not CWD."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        settings = project_dir / "settings.json"
        settings.write_text("{}")
        monkeypatch.setenv("MCP_CODER_CLAUDE_SETTINGS", "settings.json")
        monkeypatch.chdir(cwd)

        result = resolve_claude_settings_path(None, project_dir=str(project_dir))
        assert result == str(settings.resolve())

    def test_relative_env_falls_back_to_cwd_when_no_project_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Relative MCP_CODER_CLAUDE_SETTINGS falls back to CWD when project_dir is None."""
        settings = tmp_path / "settings.json"
        settings.write_text("{}")
        monkeypatch.setenv("MCP_CODER_CLAUDE_SETTINGS", "settings.json")
        monkeypatch.chdir(tmp_path)

        result = resolve_claude_settings_path(None)
        assert result == str(settings.resolve())

    def test_resolve_claude_settings_env_missing_file_falls_back(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Missing env var file warns and falls back to auto-detect."""
        monkeypatch.setenv("MCP_CODER_CLAUDE_SETTINGS", "/nonexistent/settings.json")
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings = claude_dir / "settings.json"
        settings.write_text("{}")
        monkeypatch.chdir(tmp_path)

        import logging

        with caplog.at_level(logging.WARNING, logger="mcp_coder.cli.utils"):
            result = resolve_claude_settings_path(None)

        assert result == str(settings.resolve())
        assert "MCP_CODER_CLAUDE_SETTINGS" in caplog.text
        assert "file not found" in caplog.text

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_claude_settings_config_file_absolute(
        self, mock_config: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """[claude] default_settings_path (absolute) from config file is used."""
        monkeypatch.delenv("MCP_CODER_CLAUDE_SETTINGS", raising=False)
        settings = tmp_path / "settings_from_config.json"
        settings.write_text("{}")
        mock_config.return_value = {("claude", "default_settings_path"): str(settings)}
        # No .claude/ directory in tmp_path
        monkeypatch.chdir(tmp_path)

        result = resolve_claude_settings_path(None)
        assert result == str(settings.resolve())

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_claude_settings_config_relative(
        self,
        mock_config: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Relative [claude] default_settings_path resolves against project_dir."""
        monkeypatch.delenv("MCP_CODER_CLAUDE_SETTINGS", raising=False)
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        settings = project_dir / "elsewhere.json"
        settings.write_text("{}")
        mock_config.return_value = {
            ("claude", "default_settings_path"): "elsewhere.json"
        }
        monkeypatch.chdir(cwd)

        result = resolve_claude_settings_path(None, project_dir=str(project_dir))
        assert result == str(settings.resolve())

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_relative_config_falls_back_to_cwd_when_no_project_dir(
        self,
        mock_config: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Relative [claude] default_settings_path falls back to CWD when project_dir is None."""
        monkeypatch.delenv("MCP_CODER_CLAUDE_SETTINGS", raising=False)
        # Use a non-default filename so autodetect can't accidentally pick it up.
        settings = tmp_path / "elsewhere.json"
        settings.write_text("{}")
        mock_config.return_value = {
            ("claude", "default_settings_path"): "elsewhere.json"
        }
        monkeypatch.chdir(tmp_path)

        result = resolve_claude_settings_path(None)
        assert result == str(settings.resolve())

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_claude_settings_config_missing_file_falls_back(
        self,
        mock_config: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Missing config file path warns and falls back to auto-detect."""
        monkeypatch.delenv("MCP_CODER_CLAUDE_SETTINGS", raising=False)
        mock_config.return_value = {
            ("claude", "default_settings_path"): "/nonexistent/settings.json"
        }
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings = claude_dir / "settings.json"
        settings.write_text("{}")
        monkeypatch.chdir(tmp_path)

        import logging

        with caplog.at_level(logging.WARNING, logger="mcp_coder.cli.utils"):
            result = resolve_claude_settings_path(None)

        assert result == str(settings.resolve())
        assert "default_settings_path" in caplog.text
        assert "file not found" in caplog.text

    def test_resolve_claude_settings_autodetect_local(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Auto-detect picks up <project_dir>/.claude/settings.local.json."""
        monkeypatch.delenv("MCP_CODER_CLAUDE_SETTINGS", raising=False)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        local_settings = claude_dir / "settings.local.json"
        local_settings.write_text("{}")
        monkeypatch.chdir(tmp_path)

        result = resolve_claude_settings_path(None, project_dir=str(tmp_path))
        assert result == str(local_settings.resolve())

    def test_resolve_claude_settings_autodetect_shared(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Auto-detect picks up <project_dir>/.claude/settings.json when no local.json."""
        monkeypatch.delenv("MCP_CODER_CLAUDE_SETTINGS", raising=False)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        shared_settings = claude_dir / "settings.json"
        shared_settings.write_text("{}")
        monkeypatch.chdir(tmp_path)

        result = resolve_claude_settings_path(None, project_dir=str(tmp_path))
        assert result == str(shared_settings.resolve())

    def test_resolve_claude_settings_autodetect_local_wins(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When both settings.local.json and settings.json exist, local wins."""
        monkeypatch.delenv("MCP_CODER_CLAUDE_SETTINGS", raising=False)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        local_settings = claude_dir / "settings.local.json"
        local_settings.write_text("{}")
        shared_settings = claude_dir / "settings.json"
        shared_settings.write_text("{}")
        monkeypatch.chdir(tmp_path)

        result = resolve_claude_settings_path(None, project_dir=str(tmp_path))
        assert result == str(local_settings.resolve())

    def test_resolve_claude_settings_autodetect_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns None when no settings file exists anywhere."""
        monkeypatch.delenv("MCP_CODER_CLAUDE_SETTINGS", raising=False)
        monkeypatch.chdir(tmp_path)

        result = resolve_claude_settings_path(None, project_dir=str(tmp_path))
        assert result is None

    def test_resolve_claude_settings_autodetect_no_project_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Auto-detect falls back to CWD/.claude/ when project_dir is None.

        Verifies both that settings.local.json is found at <CWD>/.claude/
        and that settings.json is the fallback when no local variant exists.
        """
        monkeypatch.delenv("MCP_CODER_CLAUDE_SETTINGS", raising=False)

        # Scenario 1: settings.local.json at <CWD>/.claude/ is picked up.
        local_root = tmp_path / "with_local"
        local_root.mkdir()
        local_claude = local_root / ".claude"
        local_claude.mkdir()
        local_settings = local_claude / "settings.local.json"
        local_settings.write_text("{}")
        monkeypatch.chdir(local_root)

        result = resolve_claude_settings_path(None)
        assert result == str(local_settings.resolve())

        # Scenario 2: only settings.json exists -- falls back to it.
        shared_root = tmp_path / "shared_only"
        shared_root.mkdir()
        shared_claude = shared_root / ".claude"
        shared_claude.mkdir()
        shared_settings = shared_claude / "settings.json"
        shared_settings.write_text("{}")
        monkeypatch.chdir(shared_root)

        result = resolve_claude_settings_path(None)
        assert result == str(shared_settings.resolve())

    def test_resolve_claude_settings_cli_overrides_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Explicit CLI settings_file overrides env var."""
        cli_file = tmp_path / "cli_settings.json"
        cli_file.write_text("{}")
        env_file = tmp_path / "env_settings.json"
        env_file.write_text("{}")
        monkeypatch.setenv("MCP_CODER_CLAUDE_SETTINGS", str(env_file))

        result = resolve_claude_settings_path(str(cli_file))
        assert result == str(cli_file.resolve())

    @patch("mcp_coder.cli.utils.get_config_values")
    def test_resolve_claude_settings_env_overrides_config(
        self, mock_config: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Env var takes precedence over config file."""
        env_file = tmp_path / "env_settings.json"
        env_file.write_text("{}")
        cfg_file = tmp_path / "cfg_settings.json"
        cfg_file.write_text("{}")
        monkeypatch.setenv("MCP_CODER_CLAUDE_SETTINGS", str(env_file))
        mock_config.return_value = {("claude", "default_settings_path"): str(cfg_file)}

        result = resolve_claude_settings_path(None)
        assert result == str(env_file.resolve())

    def test_schema_has_claude_settings_env_var(self) -> None:
        """Schema maps claude/default_settings_path to MCP_CODER_CLAUDE_SETTINGS."""
        assert (
            _CONFIG_SCHEMA["claude"]["default_settings_path"].env_var
            == "MCP_CODER_CLAUDE_SETTINGS"
        )
