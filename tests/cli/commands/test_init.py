"""Tests for init command functionality."""

import argparse
import logging
import tomllib
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.init import execute_init


class TestInitCommand:
    """Tests for execute_init command handler."""

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_init_creates_config_success(
        self,
        mock_create: object,
        mock_path: object,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test successful config creation prints instructions."""
        mock_create.return_value = True  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/path/config.toml"  # type: ignore[attr-defined]
        args = argparse.Namespace(command="init")

        with caplog.at_level(logging.DEBUG):
            result = execute_init(args)

        assert result == 0
        assert "Created default config at:" in caplog.text
        assert "Please update it" in caplog.text
        assert "Next steps:" in caplog.text
        assert "mcp-coder verify" in caplog.text
        assert "mcp-coder gh-tool define-labels" in caplog.text

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_init_config_already_exists(
        self,
        mock_create: object,
        mock_path: object,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test existing config prints already-exists message."""
        mock_create.return_value = False  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/path/config.toml"  # type: ignore[attr-defined]
        args = argparse.Namespace(command="init")

        with caplog.at_level(logging.DEBUG):
            result = execute_init(args)

        assert result == 0
        assert "Config already exists:" in caplog.text

    @patch("mcp_coder.cli.commands.init.get_config_file_path")
    @patch("mcp_coder.cli.commands.init.create_default_config")
    def test_init_write_failure(
        self,
        mock_create: object,
        mock_path: object,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test write failure returns exit code 1 with error message."""
        mock_create.side_effect = OSError("Permission denied")  # type: ignore[attr-defined]
        mock_path.return_value = "/fake/path/config.toml"  # type: ignore[attr-defined]
        args = argparse.Namespace(command="init")

        with caplog.at_level(logging.DEBUG):
            result = execute_init(args)

        assert result == 1
        assert "Failed to write config to" in caplog.text
        assert "Permission denied" in caplog.text

    def test_init_template_content_valid_toml_with_sections(
        self,
        tmp_path: object,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that created config is valid TOML with expected sections."""
        from pathlib import Path

        from mcp_coder.utils.user_config import (
            create_default_config,
            get_config_file_path,
        )

        config_path = Path(str(tmp_path)) / ".mcp_coder" / "config.toml"
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path",
            lambda: config_path,
        )

        created = create_default_config()

        assert created is True
        assert config_path.exists()

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        assert "github" in data
        assert "jenkins" in data
        assert "coordinator" in data
