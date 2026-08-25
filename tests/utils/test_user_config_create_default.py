"""Tests for the create_default_config config-template writer.

Split out of ``test_user_config.py``, following the existing
``test_user_config_schema`` / ``test_user_config_repo_matching`` convention.
"""

import tomllib
from pathlib import Path

import pytest

from mcp_coder.utils.user_config import create_default_config


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
        assert "mcp_workspace" in config["coordinator"]["repos"]

        # Check new issue interaction keys exist in repo sections
        for repo_name in ("mcp_coder", "mcp_workspace"):
            repo = config["coordinator"]["repos"][repo_name]
            assert "update_issue_labels" in repo
            assert "post_issue_comments" in repo

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
        assert "update_issue_labels" in mcp_coder_repo
        assert "post_issue_comments" in mcp_coder_repo

        # Check mcp_workspace repo config
        filesystem_repo = config["coordinator"]["repos"]["mcp_workspace"]
        assert "repo_url" in filesystem_repo
        assert "executor_job_path" in filesystem_repo
        assert "github_credentials_id" in filesystem_repo
        assert "update_issue_labels" in filesystem_repo
        assert "post_issue_comments" in filesystem_repo

    def test_create_default_config_has_llm_section(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that config template contains commented-out [llm] section."""
        # Setup
        config_file = tmp_path / ".mcp_coder" / "config.toml"
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        create_default_config()

        # Verify
        content = config_file.read_text(encoding="utf-8")
        assert "# [llm]" in content
        assert "# default_provider" in content

    def test_create_default_config_has_mcp_section(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that config template contains commented-out [mcp] section."""
        # Setup
        config_file = tmp_path / ".mcp_coder" / "config.toml"
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        # Execute
        create_default_config()

        # Verify
        content = config_file.read_text(encoding="utf-8")
        assert "# [mcp]" in content
        assert "# default_config_path" in content
        # Ensure [mcp] does NOT appear as an uncommented section
        lines = content.splitlines()
        uncommented_mcp = [l for l in lines if l.strip() == "[mcp]"]
        assert len(uncommented_mcp) == 0

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
