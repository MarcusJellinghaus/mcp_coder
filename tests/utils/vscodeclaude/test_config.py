"""Test configuration loading for VSCode Claude."""

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.workflows.vscodeclaude.config import (
    load_repo_vscodeclaude_config,
    load_vscodeclaude_config,
    sanitize_folder_name,
)
from mcp_coder.workflows.vscodeclaude.types import DEFAULT_MAX_SESSIONS


class TestConfiguration:
    """Test configuration loading."""

    def test_load_vscodeclaude_config_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Loads config with valid workspace_base."""
        # Mock get_config_values directly
        mock_config = {
            ("coordinator.vscodeclaude", "workspace_base"): str(tmp_path),
            ("coordinator.vscodeclaude", "max_sessions"): "5",
        }

        def mock_get_config_values(
            keys: list[tuple[str, str, str | None]],
        ) -> dict[tuple[str, str], str | None]:
            return {(k[0], k[1]): mock_config.get((k[0], k[1])) for k in keys}

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.config.get_config_values",
            mock_get_config_values,
        )

        config = load_vscodeclaude_config()
        assert config["workspace_base"] == str(tmp_path)
        assert config["max_sessions"] == 5

    def test_load_vscodeclaude_config_missing_workspace_base(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises ValueError when workspace_base missing."""
        mock_config: dict[tuple[str, str], str | None] = {
            ("coordinator.vscodeclaude", "workspace_base"): None,
            ("coordinator.vscodeclaude", "max_sessions"): None,
        }

        def mock_get_config_values(
            keys: list[tuple[str, str, str | None]],
        ) -> dict[tuple[str, str], str | None]:
            return {(k[0], k[1]): mock_config.get((k[0], k[1])) for k in keys}

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.config.get_config_values",
            mock_get_config_values,
        )

        with pytest.raises(ValueError, match="workspace_base"):
            load_vscodeclaude_config()

    def test_load_vscodeclaude_config_default_max_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Uses default when max_sessions not set."""
        mock_config: dict[tuple[str, str], str | None] = {
            ("coordinator.vscodeclaude", "workspace_base"): str(tmp_path),
            ("coordinator.vscodeclaude", "max_sessions"): None,
        }

        def mock_get_config_values(
            keys: list[tuple[str, str, str | None]],
        ) -> dict[tuple[str, str], str | None]:
            return {(k[0], k[1]): mock_config.get((k[0], k[1])) for k in keys}

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.config.get_config_values",
            mock_get_config_values,
        )

        config = load_vscodeclaude_config()
        assert config["max_sessions"] == DEFAULT_MAX_SESSIONS

    def test_load_vscodeclaude_config_workspace_not_exists(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises ValueError when workspace_base path doesn't exist."""
        mock_config: dict[tuple[str, str], str | None] = {
            ("coordinator.vscodeclaude", "workspace_base"): "/nonexistent/path",
            ("coordinator.vscodeclaude", "max_sessions"): None,
        }

        def mock_get_config_values(
            keys: list[tuple[str, str, str | None]],
        ) -> dict[tuple[str, str], str | None]:
            return {(k[0], k[1]): mock_config.get((k[0], k[1])) for k in keys}

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.config.get_config_values",
            mock_get_config_values,
        )

        with pytest.raises(ValueError, match="does not exist"):
            load_vscodeclaude_config()

    def test_load_repo_vscodeclaude_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Loads repo-specific setup commands."""
        mock_config: dict[tuple[str, str], str | None] = {
            (
                "coordinator.repos.mcp_coder",
                "setup_commands_windows",
            ): '["uv venv", "uv sync"]',
            ("coordinator.repos.mcp_coder", "setup_commands_linux"): '["make setup"]',
        }

        def mock_get_config_values(
            keys: list[tuple[str, str, str | None]],
        ) -> dict[tuple[str, str], str | None]:
            return {(k[0], k[1]): mock_config.get((k[0], k[1])) for k in keys}

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.config.get_config_values",
            mock_get_config_values,
        )

        config = load_repo_vscodeclaude_config("mcp_coder")
        assert config["setup_commands_windows"] == ["uv venv", "uv sync"]
        assert config["setup_commands_linux"] == ["make setup"]

    def test_sanitize_folder_name(self) -> None:
        """Removes invalid characters from folder names."""
        assert sanitize_folder_name("mcp-coder") == "mcp-coder"
        assert sanitize_folder_name("my repo!@#$") == "my-repo"
        assert sanitize_folder_name("test_project") == "test_project"
        assert sanitize_folder_name("a/b\\c:d") == "a-b-c-d"
