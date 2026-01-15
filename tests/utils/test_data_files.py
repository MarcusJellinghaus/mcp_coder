# copied from mcp_code_checker
"""
Tests for the data_files utility module.
"""

import logging
import sys
import tempfile
from pathlib import Path

import pytest

from mcp_coder.utils.data_files import find_data_file


class TestFindDataFile:
    """Test the find_data_file function."""

    def test_find_installed_file_via_importlib(self) -> None:
        """Test finding a file in installed package via importlib.

        Creates a real temporary package that Python can import, avoiding
        mock issues with pytest-xdist parallel execution.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Use a unique package name to avoid conflicts
            package_name = "_test_pkg_importlib"
            package_dir = temp_path / package_name
            package_dir.mkdir(parents=True, exist_ok=True)

            # Create __init__.py to make it a real package
            init_file = package_dir / "__init__.py"
            init_file.write_text("# test package")

            # Create the data file we want to find
            test_file = package_dir / "data" / "test_script.py"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("# test script")

            # Add temp directory to sys.path so Python can import the package
            sys.path.insert(0, str(temp_path))
            try:
                result = find_data_file(
                    package_name=package_name,
                    relative_path="data/test_script.py",
                    development_base_dir=None,  # Skip development lookup
                )

                assert result == test_file
            finally:
                # Clean up sys.path
                sys.path.remove(str(temp_path))
                # Clean up any cached module
                if package_name in sys.modules:
                    del sys.modules[package_name]

    def test_find_installed_file_via_module_file(self) -> None:
        """Test finding a file in installed package via module __file__.

        Creates a real temporary package that Python can import, avoiding
        mock issues with pytest-xdist parallel execution.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Use a unique package name to avoid conflicts
            package_name = "_test_pkg_module_file"
            package_dir = temp_path / package_name
            package_dir.mkdir(parents=True, exist_ok=True)

            # Create __init__.py to make it a real package
            init_file = package_dir / "__init__.py"
            init_file.write_text("# test package")

            # Create the data file we want to find
            test_file = package_dir / "data" / "test_script.py"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("# test script")

            # Add temp directory to sys.path so Python can import the package
            sys.path.insert(0, str(temp_path))
            try:
                result = find_data_file(
                    package_name=package_name,
                    relative_path="data/test_script.py",
                    development_base_dir=None,
                )

                assert result == test_file
            finally:
                # Clean up sys.path
                sys.path.remove(str(temp_path))
                # Clean up any cached module
                if package_name in sys.modules:
                    del sys.modules[package_name]

    def test_file_not_found_raises_exception(self) -> None:
        """Test that FileNotFoundError is raised when file is not found."""
        with pytest.raises(FileNotFoundError) as exc_info:
            find_data_file(
                package_name="nonexistent_package",
                relative_path="data/missing_script.py",
                development_base_dir=Path("/nonexistent/path"),
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
            development_base_dir=project_root,
        )
        assert result == first_md_file

    def test_data_file_found_logs_at_debug_level(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that successful data file discovery logs at DEBUG level, not INFO.

        Uses development path lookup which doesn't require mocking importlib.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create file in development structure: src/package/relative_path
            test_file = temp_path / "src" / "test_package" / "data" / "test_script.py"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("# test script")

            caplog.set_level(logging.DEBUG)

            result = find_data_file(
                package_name="test_package",
                relative_path="data/test_script.py",
                development_base_dir=temp_path,
            )

            assert result == test_file

            # Check that the success message was logged at DEBUG level (development method uses INFO)
            # The development method logs "Found data file in development environment"
            success_messages = [
                record
                for record in caplog.records
                if "Found data file in development environment" in record.message
            ]

            assert (
                len(success_messages) == 1
            ), f"Expected 1 success message, found {len(success_messages)}"
            # The development path success message is at INFO level per the code
            assert success_messages[0].levelname == "INFO"
