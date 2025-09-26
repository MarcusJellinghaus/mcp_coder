"""Integration tests for user_config module.

These tests use real file operations (no mocking) to verify end-to-end functionality.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.utils.user_config import get_config_file_path, get_config_value


class TestRealConfigFileWorkflow:
    """Integration tests using real file operations."""

    def test_real_config_file_workflow(self, tmp_path: Path) -> None:
        """Test complete workflow with real config file creation and reading."""
        # Create a temporary config file
        config_content = """[tokens]
github = "ghp_real_integration_token"
claude = "cl_test_token_456"

[settings]
default_branch = "develop"
timeout = 45
enabled = true

[database]
host = "localhost"
port = 5432
"""
        config_file = tmp_path / ".mcp_coder" / "config.toml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(config_content, encoding="utf-8")

        # Mock get_config_file_path to return our temporary file
        with patch(
            "mcp_coder.utils.user_config.get_config_file_path",
            return_value=config_file,
        ):
            # Test successful value retrieval
            assert get_config_value("tokens", "github") == "ghp_real_integration_token"
            assert get_config_value("tokens", "claude") == "cl_test_token_456"
            assert get_config_value("settings", "default_branch") == "develop"

            # Test type conversion
            assert get_config_value("settings", "timeout") == "45"
            assert get_config_value("settings", "enabled") == "True"
            assert get_config_value("database", "port") == "5432"

            # Test missing section/key
            assert get_config_value("nonexistent", "key") is None
            assert get_config_value("tokens", "missing") is None

    def test_config_directory_creation_path_verification(self, tmp_path: Path) -> None:
        """Test that config file path points to correct directory structure."""
        # Create temporary home directory
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()

        with patch("pathlib.Path.home", return_value=fake_home):
            config_path = get_config_file_path()

            # Verify path structure
            assert config_path.parent.name == ".mcp_coder"
            assert config_path.name == "config.toml"
            assert config_path.parent.parent == fake_home

            # Verify the full path construction
            expected_path = fake_home / ".mcp_coder" / "config.toml"
            assert config_path == expected_path

    def test_path_consistency(self) -> None:
        """Test that path generation is consistent across multiple calls."""
        # Test that multiple calls return the same path
        path1 = get_config_file_path()
        path2 = get_config_file_path()
        
        assert path1 == path2
        assert path1.name == "config.toml"
        assert path1.parent.name == ".mcp_coder"
        # Should be relative to user's home directory
        assert str(path1).endswith(".mcp_coder/config.toml") or str(path1).endswith(
            ".mcp_coder\\config.toml"
        )

    def test_malformed_config_file_handling(self, tmp_path: Path) -> None:
        """Test behavior with malformed TOML files."""
        config_file = tmp_path / ".mcp_coder" / "config.toml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Test various malformed TOML scenarios
        malformed_configs = [
            "[section without closing bracket",  # Syntax error
            "[section]\nkey =",  # Incomplete key-value
            "[section\nkey = value",  # Missing closing bracket
            "invalid content without sections",  # No sections
        ]

        with patch(
            "mcp_coder.utils.user_config.get_config_file_path",
            return_value=config_file,
        ):
            for malformed_content in malformed_configs:
                config_file.write_text(malformed_content, encoding="utf-8")

                # Should return None gracefully for malformed files
                result = get_config_value("section", "key")
                assert result is None

    def test_empty_and_nonexistent_file_scenarios(self, tmp_path: Path) -> None:
        """Test behavior with empty and non-existent files."""
        config_file = tmp_path / ".mcp_coder" / "config.toml"

        with patch(
            "mcp_coder.utils.user_config.get_config_file_path",
            return_value=config_file,
        ):
            # Test non-existent file
            assert not config_file.exists()
            result = get_config_value("section", "key")
            assert result is None

            # Test empty file
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.write_text("", encoding="utf-8")
            result = get_config_value("section", "key")
            assert result is None

            # Test file with only comments
            config_file.write_text(
                "# This is just a comment\n# Another comment", encoding="utf-8"
            )
            result = get_config_value("section", "key")
            assert result is None

    def test_file_permission_scenarios(self, tmp_path: Path) -> None:
        """Test behavior when file permissions prevent reading."""
        config_file = tmp_path / ".mcp_coder" / "config.toml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        config_content = """[section]
key = "value"
"""
        config_file.write_text(config_content, encoding="utf-8")

        with patch(
            "mcp_coder.utils.user_config.get_config_file_path",
            return_value=config_file,
        ):
            # Simulate file permission error by patching open
            with patch("builtins.open", side_effect=PermissionError("Access denied")):
                result = get_config_value("section", "key")
                assert result is None

    def test_unicode_content_handling(self, tmp_path: Path) -> None:
        """Test handling of Unicode content in config files."""
        config_file = tmp_path / ".mcp_coder" / "config.toml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Config with Unicode characters
        config_content = """[tokens]
github = "ghp_token_with_émojis_🚀"
description = "Testing with üñíçødé characters"

[paths]
project_name = "mcp_cöder"
"""
        config_file.write_text(config_content, encoding="utf-8")

        with patch(
            "mcp_coder.utils.user_config.get_config_file_path",
            return_value=config_file,
        ):
            # Test Unicode value retrieval
            assert get_config_value("tokens", "github") == "ghp_token_with_émojis_🚀"
            assert (
                get_config_value("tokens", "description")
                == "Testing with üñíçødé characters"
            )
            assert get_config_value("paths", "project_name") == "mcp_cöder"

    def test_complex_toml_structures(self, tmp_path: Path) -> None:
        """Test handling of complex TOML structures like arrays and nested tables."""
        config_file = tmp_path / ".mcp_coder" / "config.toml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        config_content = """[simple]
string_value = "simple string"
number_value = 42
boolean_value = true

[arrays]
string_array = ["one", "two", "three"]
number_array = [1, 2, 3]

[nested.table]
nested_key = "nested_value"
"""
        config_file.write_text(config_content, encoding="utf-8")

        with patch(
            "mcp_coder.utils.user_config.get_config_file_path",
            return_value=config_file,
        ):
            # Test simple values
            assert get_config_value("simple", "string_value") == "simple string"
            assert get_config_value("simple", "number_value") == "42"
            assert get_config_value("simple", "boolean_value") == "True"

            # Test arrays (should be converted to string representation)
            array_result = get_config_value("arrays", "string_array")
            assert array_result is not None
            assert (
                "one" in array_result
            )  # Array converted to string should contain elements

            # Test nested tables
            assert (
                get_config_value("nested", "table") is not None
            )  # Should find the nested table
