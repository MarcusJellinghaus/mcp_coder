"""Tests for configuration reader using TDD approach."""

import os
import tempfile
from pathlib import Path

import pytest

from mcp_coder.formatters.config_reader import (
    check_line_length_conflicts,
    read_formatter_config,
)


@pytest.mark.formatter_integration
class TestConfigReader:
    """Test configuration reading functionality."""

    def test_read_existing_configuration(self) -> None:
        """Test reading existing Black and isort configuration from pyproject.toml."""
        # Create a temporary pyproject.toml with formatter configuration
        config_content = """
[tool.black]
line-length = 100
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 88
float_to_top = true
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            temp_file = f.name

        try:
            config = read_formatter_config(temp_file)

            # Verify Black configuration
            assert "black" in config
            assert config["black"]["line-length"] == 100
            assert config["black"]["target-version"] == ["py311"]

            # Verify isort configuration
            assert "isort" in config
            assert config["isort"]["profile"] == "black"
            assert config["isort"]["line_length"] == 88
            assert config["isort"]["float_to_top"] is True

        finally:
            os.unlink(temp_file)

    def test_read_missing_configuration(self) -> None:
        """Test reading configuration when sections are missing."""
        # Create a temporary pyproject.toml without formatter sections
        config_content = """
[project]
name = "test-project"
version = "0.1.0"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            temp_file = f.name

        try:
            config = read_formatter_config(temp_file)

            # Should return empty config or defaults when sections not found
            assert isinstance(config, dict)
            # Either empty or with default configurations
            if "black" in config:
                assert isinstance(config["black"], dict)
            if "isort" in config:
                assert isinstance(config["isort"], dict)

        finally:
            os.unlink(temp_file)

    def test_line_length_conflict_detection(self) -> None:
        """Test detection of line-length conflicts between Black and isort."""
        # Configuration with conflicting line lengths
        config_with_conflict = {
            "black": {"line-length": 100},
            "isort": {"line_length": 88},
        }

        warning = check_line_length_conflicts(config_with_conflict)
        assert warning is not None
        assert "line-length" in warning or "line_length" in warning
        assert "black" in warning.lower()
        assert "isort" in warning.lower()
        assert "100" in warning
        assert "88" in warning

    def test_no_line_length_conflict(self) -> None:
        """Test no warning when line lengths match."""
        # Configuration with matching line lengths
        config_no_conflict = {
            "black": {"line-length": 88},
            "isort": {"line_length": 88},
        }

        warning = check_line_length_conflicts(config_no_conflict)
        assert warning is None

    def test_missing_line_length_config(self) -> None:
        """Test behavior when line-length config is missing."""
        # Configuration without line-length settings
        config_missing = {
            "black": {"target-version": ["py311"]},
            "isort": {"profile": "black"},
        }

        warning = check_line_length_conflicts(config_missing)
        # Should not warn if line-length settings are not present
        assert warning is None
