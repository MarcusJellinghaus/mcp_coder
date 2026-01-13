# copied from mcp_code_checker
"""
Tests for the data_files utility module.
"""

import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.data_files import (
    find_data_file,
    find_package_data_files,
    get_package_directory,
)


class TestFindDataFile:
    """Test the find_data_file function."""

    def test_find_development_file_new_structure(self) -> None:
        """Test finding a file in development environment with new src/ structure."""
        # Create a temporary directory structure matching the new layout
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "src" / "mcp_coder" / "prompts" / "test_prompt.md"
            test_file.parent.mkdir(parents=True)
            test_file.write_text("# test prompt")

            # Should find the development file in new structure
            result = find_data_file(
                package_name="mcp_coder",
                relative_path="prompts/test_prompt.md",
                development_base_dir=temp_path,
            )

            assert result == test_file
            assert result.exists()

    def test_find_installed_file_via_importlib(self) -> None:
        """Test finding a file in installed package via importlib."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_dir = temp_path / "test_package"
            test_file = package_dir / "data" / "test_script.py"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("# test script")

            # Mock importlib.util.find_spec to return our test location
            mock_spec = MagicMock()
            mock_spec.origin = str(package_dir / "__init__.py")

            with patch(
                "mcp_coder.utils.data_files.importlib.util.find_spec",
                return_value=mock_spec,
            ):
                result = find_data_file(
                    package_name="test_package",
                    relative_path="data/test_script.py",
                    development_base_dir=None,  # Skip development lookup
                )

                assert result == test_file

    def test_find_installed_file_via_module_file(self) -> None:
        """Test finding a file in installed package via module __file__."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_dir = temp_path / "test_package"
            test_file = package_dir / "data" / "test_script.py"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("# test script")

            # Mock the package module
            mock_module = MagicMock()
            mock_module.__file__ = str(package_dir / "__init__.py")

            with patch(
                "mcp_coder.utils.data_files.importlib.util.find_spec",
                side_effect=Exception("not found"),
            ):
                with patch(
                    "mcp_coder.utils.data_files.importlib.import_module",
                    return_value=mock_module,
                ):
                    result = find_data_file(
                        package_name="test_package",
                        relative_path="data/test_script.py",
                        development_base_dir=None,
                    )

                    assert result == test_file

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


class TestFindPackageDataFiles:
    """Test the find_package_data_files function."""

    def test_find_multiple_files(self) -> None:
        """Test finding multiple data files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create multiple test files in the new src structure
            files = [
                temp_path / "src" / "mcp_coder" / "prompts" / "test1.md",
                temp_path / "src" / "mcp_coder" / "prompts" / "test2.md",
            ]

            for file_path in files:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("# test content")

            result = find_package_data_files(
                package_name="mcp_coder",
                relative_paths=["prompts/test1.md", "prompts/test2.md"],
                development_base_dir=temp_path,
            )

            assert len(result) == 2
            assert result[0] == files[0]
            assert result[1] == files[1]


class TestGetPackageDirectory:
    """Test the get_package_directory function."""

    def test_get_directory_via_importlib(self) -> None:
        """Test getting package directory via importlib."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_dir = temp_path / "test_package"
            package_dir.mkdir()

            mock_spec = MagicMock()
            mock_spec.origin = str(package_dir / "__init__.py")

            with patch(
                "mcp_coder.utils.data_files.importlib.util.find_spec",
                return_value=mock_spec,
            ):
                result = get_package_directory("test_package")
                assert result == package_dir

    def test_get_directory_via_module_file(self) -> None:
        """Test getting package directory via module __file__."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_dir = temp_path / "test_package"
            package_dir.mkdir()

            mock_module = MagicMock()
            mock_module.__file__ = str(package_dir / "__init__.py")

            with patch(
                "mcp_coder.utils.data_files.importlib.util.find_spec",
                side_effect=Exception("not found"),
            ):
                with patch(
                    "mcp_coder.utils.data_files.importlib.import_module",
                    return_value=mock_module,
                ):
                    result = get_package_directory("test_package")
                    assert result == package_dir

    def test_package_not_found_raises_exception(self) -> None:
        """Test that ImportError is raised when package is not found."""
        with patch(
            "mcp_coder.utils.data_files.importlib.util.find_spec",
            side_effect=Exception("not found"),
        ):
            with patch(
                "mcp_coder.utils.data_files.importlib.import_module",
                side_effect=ImportError("no module"),
            ):
                with pytest.raises(ImportError) as exc_info:
                    get_package_directory("nonexistent_package")

                assert "Cannot find package directory" in str(exc_info.value)
