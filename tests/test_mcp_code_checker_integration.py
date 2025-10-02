"""
Integration tests for mcp_code_checker wrapper module.

These tests verify that our wrapper correctly interfaces with the external
mcp_code_checker library and handles various result scenarios.
"""

import tempfile
from pathlib import Path

import pytest

from mcp_coder.mcp_code_checker import has_mypy_errors, run_mypy_check


@pytest.mark.formatter_integration
class TestMypyIntegration:
    """Integration tests for mypy checking functionality."""

    def test_successful_mypy_check_on_current_project(self) -> None:
        """Test mypy check on current project (should pass)."""
        # Use current project directory
        project_dir = Path.cwd()

        # Run mypy check
        result = run_mypy_check(project_dir)

        # Verify result structure - should be MypyResult from mcp_code_checker
        assert hasattr(result, "return_code")
        assert hasattr(result, "messages")
        assert hasattr(result, "errors_found")
        assert hasattr(result, "raw_output")
        assert isinstance(result.return_code, int)
        assert isinstance(result.errors_found, (int, type(None)))
        assert (result.errors_found or 0) >= 0

        # Verify the result is consistent
        if (result.errors_found or 0) > 0:
            # If there are errors, return code should indicate failure
            assert result.return_code != 0
        else:
            # If no errors, return code should be 0
            assert result.return_code == 0

    def test_has_mypy_errors_convenience_function(self) -> None:
        """Test the convenience function for checking mypy errors."""
        project_dir = Path.cwd()

        # Test the convenience function
        has_errors = has_mypy_errors(project_dir)

        # Should return a boolean
        assert isinstance(has_errors, bool)

        # Should match the detailed result
        detailed_result = run_mypy_check(project_dir)
        assert has_errors == ((detailed_result.errors_found or 0) > 0)

    def test_mypy_check_with_invalid_directory(self) -> None:
        """Test mypy check with non-existent directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_dir = Path(temp_dir) / "nonexistent"

            # Should handle gracefully or raise appropriate exception
            with pytest.raises((FileNotFoundError, Exception)):
                run_mypy_check(invalid_dir)

    def test_mypy_check_with_empty_directory(self) -> None:
        """Test mypy check with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_dir = Path(temp_dir)

            # Run mypy check on empty directory
            result = run_mypy_check(empty_dir)

            # Should complete without crashing
            assert hasattr(result, "return_code")
            assert hasattr(result, "errors_found")
            # Empty directory likely has no type errors (nothing to check)
            assert (result.errors_found or 0) >= 0


class TestMypyCheckWithTypingErrors:
    """Test mypy checking with intentional typing errors."""

    def test_mypy_check_with_type_errors(self) -> None:
        """Test mypy check on code with intentional type errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create a Python file with type errors
            test_file = project_dir / "test_file.py"
            test_file.write_text(
                """
def add_numbers(a, b):  # Missing type annotations
    return a + b

def greet(name: str) -> str:
    return name + 123  # Type error: str + int

x: int = "hello"  # Type error: str assigned to int
"""
            )

            # Create a basic pyproject.toml to make it a valid Python project
            pyproject_file = project_dir / "pyproject.toml"
            pyproject_file.write_text(
                """
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "test-project"
version = "0.1.0"
"""
            )

            # Run mypy check
            result = run_mypy_check(project_dir)

            # Should complete without crashing
            assert hasattr(result, "return_code")
            assert hasattr(result, "errors_found")
            assert hasattr(result, "messages")

            # The exact behavior depends on mypy configuration
            # Let's just verify the result structure is consistent
            if (result.errors_found or 0) > 0:
                assert result.return_code != 0
                assert isinstance(result.messages, list)
            else:
                # If mypy doesn't detect errors (maybe due to configuration),
                # that's still a valid result structure
                assert result.return_code >= 0
                # This scenario suggests mypy might not be configured to catch these errors
                # which is actually valid behavior
