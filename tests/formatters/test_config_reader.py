"""Unit tests for configuration reader."""

import tempfile
import warnings
from pathlib import Path
from typing import Any, Dict

import pytest

from src.mcp_coder.formatters.config_reader import (
    get_black_config,
    get_isort_config,
    parse_pyproject_toml,
    read_formatter_config,
)
from src.mcp_coder.formatters.models import FormatterConfig


class TestParsePyprojectToml:
    """Test pyproject.toml parsing functionality."""

    def test_parse_valid_toml_file(self, tmp_path: Path) -> None:
        """Test parsing a valid pyproject.toml file."""
        toml_content = """
        [tool.black]
        line-length = 100
        target-version = ["py311"]
        
        [tool.isort]
        profile = "black"
        line_length = 100
        """
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(toml_content)

        result = parse_pyproject_toml(toml_file)

        assert result["tool"]["black"]["line-length"] == 100
        assert result["tool"]["black"]["target-version"] == ["py311"]
        assert result["tool"]["isort"]["profile"] == "black"
        assert result["tool"]["isort"]["line_length"] == 100

    def test_parse_missing_file(self, tmp_path: Path) -> None:
        """Test parsing a non-existent pyproject.toml file."""
        missing_file = tmp_path / "nonexistent.toml"

        result = parse_pyproject_toml(missing_file)

        assert result == {}

    def test_parse_malformed_toml(self, tmp_path: Path) -> None:
        """Test parsing a malformed TOML file."""
        malformed_content = """
        [tool.black
        line-length = 100
        """
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(malformed_content)

        result = parse_pyproject_toml(toml_file)

        assert result == {}

    def test_parse_empty_toml(self, tmp_path: Path) -> None:
        """Test parsing an empty TOML file."""
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text("")

        result = parse_pyproject_toml(toml_file)

        assert result == {}


class TestReadFormatterConfig:
    """Test reading formatter-specific configuration."""

    def test_read_black_config_with_settings(self, tmp_path: Path) -> None:
        """Test reading Black configuration when settings exist."""
        toml_content = """
        [tool.black]
        line-length = 120
        target-version = ["py310", "py311"]
        skip-string-normalization = true
        """
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(toml_content)

        # Create src and tests directories
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()

        config = read_formatter_config(tmp_path, "black")

        assert config.tool_name == "black"
        assert config.settings["line-length"] == 120
        assert config.settings["target-version"] == ["py310", "py311"]
        assert config.settings["skip-string-normalization"] is True
        assert config.project_root == tmp_path
        assert set(config.target_directories) == {tmp_path / "src", tmp_path / "tests"}

    def test_read_isort_config_with_settings(self, tmp_path: Path) -> None:
        """Test reading isort configuration when settings exist."""
        toml_content = """
        [tool.isort]
        profile = "django"
        line_length = 100
        multi_line_output = 3
        include_trailing_comma = true
        """
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(toml_content)

        # Create src directory only
        (tmp_path / "src").mkdir()

        config = read_formatter_config(tmp_path, "isort")

        assert config.tool_name == "isort"
        assert config.settings["profile"] == "django"
        assert config.settings["line_length"] == 100
        assert config.settings["multi_line_output"] == 3
        assert config.settings["include_trailing_comma"] is True
        assert config.project_root == tmp_path
        assert config.target_directories == [tmp_path / "src"]

    def test_read_config_missing_section(self, tmp_path: Path) -> None:
        """Test reading config when the tool section is missing."""
        toml_content = """
        [tool.other]
        some-setting = "value"
        """
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(toml_content)

        # Create src directory
        (tmp_path / "src").mkdir()

        config = read_formatter_config(tmp_path, "black")

        assert config.tool_name == "black"
        assert config.settings == {}
        assert config.project_root == tmp_path
        assert config.target_directories == [tmp_path / "src"]

    def test_read_config_no_pyproject_toml(self, tmp_path: Path) -> None:
        """Test reading config when pyproject.toml doesn't exist."""
        # Create tests directory only
        (tmp_path / "tests").mkdir()

        config = read_formatter_config(tmp_path, "isort")

        assert config.tool_name == "isort"
        assert config.settings == {}
        assert config.project_root == tmp_path
        assert config.target_directories == [tmp_path / "tests"]

    def test_read_config_no_target_directories(self, tmp_path: Path) -> None:
        """Test reading config when neither src nor tests directories exist."""
        config = read_formatter_config(tmp_path, "black")

        assert config.tool_name == "black"
        assert config.settings == {}
        assert config.project_root == tmp_path
        assert config.target_directories == []

    def test_read_config_custom_target_directories(self, tmp_path: Path) -> None:
        """Test reading config with custom target directories."""
        toml_content = """
        [tool.black]
        line-length = 88
        target_directories = ["app", "utils", "tests"]
        """
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(toml_content)

        # Create only some of the directories
        (tmp_path / "app").mkdir()
        (tmp_path / "utils").mkdir()

        config = read_formatter_config(tmp_path, "black")

        assert config.tool_name == "black"
        assert config.settings["line-length"] == 88
        assert config.settings["target_directories"] == ["app", "utils", "tests"]
        # Should only include existing directories in target_directories
        assert set(config.target_directories) == {tmp_path / "app", tmp_path / "utils"}


class TestGetBlackConfig:
    """Test Black-specific configuration function."""

    def test_get_black_config_defaults(self, tmp_path: Path) -> None:
        """Test getting Black config with defaults."""
        # Create src and tests directories
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()

        config = get_black_config(tmp_path)

        assert config.tool_name == "black"
        assert config.settings["line-length"] == 88
        assert config.settings["target-version"] == ["py311"]
        assert config.project_root == tmp_path
        assert set(config.target_directories) == {tmp_path / "src", tmp_path / "tests"}

    def test_get_black_config_with_custom_settings(self, tmp_path: Path) -> None:
        """Test getting Black config with custom settings from pyproject.toml."""
        toml_content = """
        [tool.black]
        line-length = 100
        target-version = ["py310"]
        skip-string-normalization = true
        """
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(toml_content)

        (tmp_path / "src").mkdir()

        config = get_black_config(tmp_path)

        assert config.tool_name == "black"
        assert config.settings["line-length"] == 100
        assert config.settings["target-version"] == ["py310"]
        assert config.settings["skip-string-normalization"] is True
        # Defaults should be merged
        assert config.target_directories == [tmp_path / "src"]

    def test_get_black_config_merge_with_defaults(self, tmp_path: Path) -> None:
        """Test that Black config merges with defaults properly."""
        toml_content = """
        [tool.black]
        skip-string-normalization = true
        """
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(toml_content)

        (tmp_path / "src").mkdir()

        config = get_black_config(tmp_path)

        assert config.tool_name == "black"
        # Custom setting
        assert config.settings["skip-string-normalization"] is True
        # Default settings should still be present
        assert config.settings["line-length"] == 88
        assert config.settings["target-version"] == ["py311"]


class TestGetIsortConfig:
    """Test isort-specific configuration function."""

    def test_get_isort_config_defaults(self, tmp_path: Path) -> None:
        """Test getting isort config with defaults."""
        # Create src and tests directories
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()

        config = get_isort_config(tmp_path)

        assert config.tool_name == "isort"
        assert config.settings["profile"] == "black"
        assert config.settings["line_length"] == 88
        assert config.settings["float_to_top"] is True
        assert config.project_root == tmp_path
        assert set(config.target_directories) == {tmp_path / "src", tmp_path / "tests"}

    def test_get_isort_config_with_custom_settings(self, tmp_path: Path) -> None:
        """Test getting isort config with custom settings from pyproject.toml."""
        toml_content = """
        [tool.isort]
        profile = "django"
        line_length = 120
        multi_line_output = 5
        """
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(toml_content)

        (tmp_path / "tests").mkdir()

        config = get_isort_config(tmp_path)

        assert config.tool_name == "isort"
        assert config.settings["profile"] == "django"
        assert config.settings["line_length"] == 120
        assert config.settings["multi_line_output"] == 5
        # Defaults should be merged
        assert config.settings["float_to_top"] is True
        assert config.target_directories == [tmp_path / "tests"]

    def test_get_isort_config_merge_with_defaults(self, tmp_path: Path) -> None:
        """Test that isort config merges with defaults properly."""
        toml_content = """
        [tool.isort]
        multi_line_output = 3
        """
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(toml_content)

        (tmp_path / "src").mkdir()

        config = get_isort_config(tmp_path)

        assert config.tool_name == "isort"
        # Custom setting
        assert config.settings["multi_line_output"] == 3
        # Default settings should still be present
        assert config.settings["profile"] == "black"
        assert config.settings["line_length"] == 88
        assert config.settings["float_to_top"] is True


class TestLineLengthConflictWarning:
    """Test line-length conflict detection and warnings."""

    def test_line_length_conflict_warning(self, tmp_path: Path) -> None:
        """Test that line-length conflicts generate warnings."""
        toml_content = """
        [tool.black]
        line-length = 88
        
        [tool.isort]
        line_length = 100
        """
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(toml_content)

        (tmp_path / "src").mkdir()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Both configs should trigger warning
            get_black_config(tmp_path)
            get_isort_config(tmp_path)

            # Should have at least one warning about line length conflict
            warning_messages = [str(warning.message) for warning in w]
            conflict_warnings = [
                msg
                for msg in warning_messages
                if "line-length" in msg.lower() and "conflict" in msg.lower()
            ]
            assert len(conflict_warnings) > 0

    def test_no_warning_same_line_length(self, tmp_path: Path) -> None:
        """Test that same line lengths don't generate warnings."""
        toml_content = """
        [tool.black]
        line-length = 88
        
        [tool.isort]
        line_length = 88
        """
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(toml_content)

        (tmp_path / "src").mkdir()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            get_black_config(tmp_path)
            get_isort_config(tmp_path)

            # Should not have any line length conflict warnings
            warning_messages = [str(warning.message) for warning in w]
            conflict_warnings = [
                msg
                for msg in warning_messages
                if "line-length" in msg.lower() and "conflict" in msg.lower()
            ]
            assert len(conflict_warnings) == 0

    def test_no_warning_missing_line_length(self, tmp_path: Path) -> None:
        """Test that missing line length in one tool doesn't generate warnings."""
        toml_content = """
        [tool.black]
        target-version = ["py311"]
        
        [tool.isort]
        profile = "black"
        """
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text(toml_content)

        (tmp_path / "src").mkdir()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            get_black_config(tmp_path)
            get_isort_config(tmp_path)

            # Should not have any line length conflict warnings
            warning_messages = [str(warning.message) for warning in w]
            conflict_warnings = [
                msg
                for msg in warning_messages
                if "line-length" in msg.lower() and "conflict" in msg.lower()
            ]
            assert len(conflict_warnings) == 0
