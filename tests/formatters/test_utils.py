"""Tests for formatter utilities."""

import tempfile
from pathlib import Path

import pytest

from mcp_coder.formatters.utils import (
    find_python_files,
    get_default_target_dirs,
    read_tool_config,
)


@pytest.mark.formatter_integration
class TestFormatterUtils:
    """Test shared formatter utilities."""

    def test_get_default_target_dirs_with_src_and_tests(self) -> None:
        """Test getting default target directories when src and tests exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create src and tests directories
            (project_root / "src").mkdir()
            (project_root / "tests").mkdir()

            result = get_default_target_dirs(project_root)

            assert "src" in result
            assert "tests" in result
            assert len(result) == 2

    def test_get_default_target_dirs_with_only_src(self) -> None:
        """Test getting default target directories when only src exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create only src directory
            (project_root / "src").mkdir()

            result = get_default_target_dirs(project_root)

            assert "src" in result
            assert "tests" not in result
            assert len(result) == 1

    def test_get_default_target_dirs_fallback_to_current(self) -> None:
        """Test fallback to current directory when no standard dirs exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # No src or tests directories
            result = get_default_target_dirs(project_root)

            assert result == ["."]

    def test_find_python_files_in_directory(self) -> None:
        """Test finding Python files in a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            # Create Python files and other files
            (test_dir / "module1.py").write_text("print('hello')")
            (test_dir / "module2.py").write_text("import os")
            (test_dir / "readme.txt").write_text("not python")
            (test_dir / "subdir").mkdir()
            (test_dir / "subdir" / "submodule.py").write_text("def func(): pass")

            result = find_python_files(test_dir)

            # Should find all Python files recursively
            python_filenames = [f.name for f in result]
            assert "module1.py" in python_filenames
            assert "module2.py" in python_filenames
            assert "submodule.py" in python_filenames
            assert len(result) == 3

    def test_find_python_files_single_file(self) -> None:
        """Test finding Python files when given a single file path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "single.py"
            test_file.write_text("print('single file')")

            result = find_python_files(test_file)

            assert len(result) == 1
            assert result[0] == test_file

    def test_find_python_files_non_python_single_file(self) -> None:
        """Test finding Python files when given a non-Python file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "readme.txt"
            test_file.write_text("not python")

            result = find_python_files(test_file)

            assert len(result) == 0


@pytest.mark.formatter_integration
class TestConfigReading:
    """Test shared configuration reading functionality."""

    def test_read_tool_config_with_existing_config(self) -> None:
        """Test reading tool configuration when config exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create pyproject.toml with tool configuration
            pyproject_content = """
[tool.black]
line-length = 100
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 120
float_to_top = false
"""
            (project_root / "pyproject.toml").write_text(pyproject_content)

            # Test Black configuration
            black_defaults = {"line-length": 88, "target-version": ["py310"]}
            black_config = read_tool_config(project_root, "black", black_defaults)

            assert black_config["line-length"] == 100  # From config file
            assert black_config["target-version"] == ["py311"]  # From config file

            # Test isort configuration
            isort_defaults = {
                "profile": "default",
                "line_length": 88,
                "float_to_top": True,
            }
            isort_config = read_tool_config(project_root, "isort", isort_defaults)

            assert isort_config["profile"] == "black"  # From config file
            assert isort_config["line_length"] == 120  # From config file
            assert isort_config["float_to_top"] is False  # From config file

    def test_read_tool_config_with_missing_config(self) -> None:
        """Test reading tool configuration when config doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # No pyproject.toml file
            defaults = {"line-length": 88, "target-version": ["py311"]}
            config = read_tool_config(project_root, "black", defaults)

            # Should return defaults
            assert config == defaults

    def test_read_tool_config_with_missing_tool_section(self) -> None:
        """Test reading tool configuration when tool section doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create pyproject.toml without the requested tool section
            pyproject_content = """
[build-system]
requires = ["setuptools"]

[tool.other-tool]
some-setting = "value"
"""
            (project_root / "pyproject.toml").write_text(pyproject_content)

            defaults = {"profile": "black", "line_length": 88}
            config = read_tool_config(project_root, "isort", defaults)

            # Should return defaults when tool section missing
            assert config == defaults

    def test_read_tool_config_with_partial_config(self) -> None:
        """Test reading tool configuration with partial config (merge with defaults)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create pyproject.toml with partial configuration
            pyproject_content = """
[tool.black]
line-length = 120
# target-version not specified
"""
            (project_root / "pyproject.toml").write_text(pyproject_content)

            defaults = {
                "line-length": 88,
                "target-version": ["py311"],
                "skip-string-normalization": False,
            }
            config = read_tool_config(project_root, "black", defaults)

            # Should merge: config file values override defaults, missing keys use defaults
            assert config["line-length"] == 120  # From config file
            assert config["target-version"] == ["py311"]  # From defaults
            assert config["skip-string-normalization"] is False  # From defaults

    def test_read_tool_config_with_invalid_toml(self) -> None:
        """Test reading tool configuration with invalid TOML file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create invalid TOML file
            (project_root / "pyproject.toml").write_text("invalid toml content [[[")

            defaults = {"line-length": 88}
            config = read_tool_config(project_root, "black", defaults)

            # Should return defaults when TOML is invalid
            assert config == defaults

    def test_find_python_files_empty_directory(self) -> None:
        """Test finding Python files in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            result = find_python_files(test_dir)

            assert len(result) == 0
