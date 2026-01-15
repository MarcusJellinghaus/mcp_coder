# copied from mcp_code_checker
"""
Tests for the data_files utility module.
"""

import logging
import sys
import tempfile
from pathlib import Path

import pytest

from mcp_coder.utils.data_files import (
    find_data_file,
    find_package_data_files,
    get_package_directory,
)


class TestFindDataFile:
    """Test the find_data_file function."""

    def test_find_file_in_installed_package(self) -> None:
        """Test finding a file in installed package using importlib.resources.

        Uses real mcp_coder package - no mocking or sys.path manipulation needed.
        """
        result = find_data_file(
            package_name="mcp_coder",
            relative_path="prompts/prompts.md",
        )

        assert result.exists()
        assert result.name == "prompts.md"
        assert "mcp_coder" in str(result)

    def test_file_not_found_raises_exception(self) -> None:
        """Test that FileNotFoundError is raised when file is not found."""
        with pytest.raises(FileNotFoundError) as exc_info:
            find_data_file(
                package_name="nonexistent_package",
                relative_path="data/missing_script.py",
            )

        assert "not found" in str(exc_info.value).lower()
        assert "data/missing_script.py" in str(exc_info.value)

    def test_pyproject_toml_consistency(self) -> None:
        """Test that the package configuration in pyproject.toml matches actual usage."""
        import tomllib

        # Read pyproject.toml
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)

        # Get package data configuration
        package_data = (
            pyproject_data.get("tool", {}).get("setuptools", {}).get("package-data", {})
        )

        # Check that mcp_coder is configured with prompts/*.md
        mcp_coder_config = package_data.get("mcp_coder", [])
        assert (
            "prompts/*.md" in mcp_coder_config
        ), f"prompts/*.md not found in pyproject.toml package-data. Found: {mcp_coder_config}"

        # Verify the actual files exist in the expected location
        project_root = Path(__file__).parent.parent.parent
        prompts_dir = project_root / "src" / "mcp_coder" / "prompts"
        assert prompts_dir.exists(), f"prompts directory not found at {prompts_dir}"

        # Check for at least one .md file in prompts directory
        md_files = list(prompts_dir.glob("*.md"))
        assert len(md_files) > 0, f"No .md files found in {prompts_dir}"

        # Test that find_data_file can actually find one of the prompt files
        first_md_file = md_files[0]
        result = find_data_file(
            package_name="mcp_coder",
            relative_path=f"prompts/{first_md_file.name}",
        )
        assert result.exists()
        assert result.name == first_md_file.name

    def test_data_file_found_logs_at_debug_level(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that successful data file discovery logs appropriately.

        Uses real mcp_coder package - no temp directories needed.
        """
        caplog.set_level(logging.DEBUG)

        result = find_data_file(
            package_name="mcp_coder",
            relative_path="prompts/prompts.md",
        )

        assert result.exists()

        # Verify logging occurred - check for key log messages at DEBUG level
        # The function logs "SEARCH STARTED" and "SUCCESS: Found data file" at DEBUG level
        debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert len(debug_records) > 0, "Expected DEBUG level log messages"

        # Verify the search started message was logged
        assert any(
            "SEARCH STARTED" in record.message for record in debug_records
        ), "Expected 'SEARCH STARTED' log message"

        # Verify the success message was logged (contains the file path)
        assert any(
            "SUCCESS" in record.message and "prompts.md" in record.message
            for record in debug_records
        ), "Expected 'SUCCESS' log message with file path"


class TestFindPackageDataFiles:
    """Test the find_package_data_files function."""

    def test_find_multiple_files(self) -> None:
        """Test finding multiple data files using real mcp_coder package."""
        result = find_package_data_files(
            package_name="mcp_coder",
            relative_paths=["prompts/prompts.md", "prompts/prompt_instructions.md"],
        )

        assert len(result) == 2
        assert all(path.exists() for path in result)


class TestGetPackageDirectory:
    """Test the get_package_directory function."""

    def test_get_directory_via_importlib(self) -> None:
        """Test getting package directory via importlib.

        Creates a real temporary package that Python can import, avoiding
        mock issues with pytest-xdist parallel execution.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Use a unique package name to avoid conflicts
            package_name = "_test_pkg_dir_importlib"
            package_dir = temp_path / package_name
            package_dir.mkdir(parents=True, exist_ok=True)

            # Create __init__.py to make it a real package
            init_file = package_dir / "__init__.py"
            init_file.write_text("# test package")

            # Add temp directory to sys.path so Python can import the package
            sys.path.insert(0, str(temp_path))
            try:
                result = get_package_directory(package_name)
                assert result == package_dir
            finally:
                # Clean up sys.path
                sys.path.remove(str(temp_path))
                # Clean up any cached module
                if package_name in sys.modules:
                    del sys.modules[package_name]

    def test_get_directory_via_module_file(self) -> None:
        """Test getting package directory via module __file__.

        Creates a real temporary package that Python can import, avoiding
        mock issues with pytest-xdist parallel execution.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Use a unique package name to avoid conflicts
            package_name = "_test_pkg_dir_module_file"
            package_dir = temp_path / package_name
            package_dir.mkdir(parents=True, exist_ok=True)

            # Create __init__.py to make it a real package
            init_file = package_dir / "__init__.py"
            init_file.write_text("# test package")

            # Add temp directory to sys.path so Python can import the package
            sys.path.insert(0, str(temp_path))
            try:
                result = get_package_directory(package_name)
                assert result == package_dir
            finally:
                # Clean up sys.path
                sys.path.remove(str(temp_path))
                # Clean up any cached module
                if package_name in sys.modules:
                    del sys.modules[package_name]

    def test_package_not_found_raises_exception(self) -> None:
        """Test that ImportError is raised when package is not found."""
        # Use a package name that definitely doesn't exist
        with pytest.raises(ImportError) as exc_info:
            get_package_directory("_nonexistent_package_12345")

        assert "Cannot find package directory" in str(exc_info.value)
