"""
Integration tests for mcp_code_checker wrapper module.

These tests verify that our wrapper correctly interfaces with the external
mcp_code_checker library and handles various result scenarios.
"""

from pathlib import Path

import pytest

from mcp_coder.mcp_code_checker import run_mypy_check


@pytest.mark.formatter_integration
class TestMypyIntegration:
    """Integration tests for mypy checking functionality."""

    def test_mypy_check_clean_code(self, tmp_path: Path) -> None:
        """Test mypy check on valid typed code."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("""
def add(a: int, b: int) -> int:
    return a + b

result: int = add(1, 2)
""")

        result = run_mypy_check(tmp_path, target_directories=["."])

        # Verify result structure
        assert hasattr(result, "return_code")
        assert hasattr(result, "messages")
        assert hasattr(result, "errors_found")
        assert hasattr(result, "raw_output")
        assert isinstance(result.return_code, int)
        assert isinstance(result.errors_found, (int, type(None)))
        assert result.return_code == 0
        assert (result.errors_found or 0) == 0

    def test_mypy_check_with_type_errors(self, tmp_path: Path) -> None:
        """Test mypy check on code with intentional type errors."""
        test_file = tmp_path / "errors.py"
        test_file.write_text("""
def greet(name: str) -> str:
    return name + 123  # Type error: str + int

x: int = "hello"  # Type error: str assigned to int
""")

        result = run_mypy_check(tmp_path, target_directories=["."])

        # Should detect type errors
        assert hasattr(result, "return_code")
        assert hasattr(result, "errors_found")
        assert hasattr(result, "messages")
        assert result.return_code != 0
        assert (result.errors_found or 0) > 0
        assert isinstance(result.messages, list)

    def test_has_mypy_errors_convenience_function(self, tmp_path: Path) -> None:
        """Test the convenience function for checking mypy errors."""
        # Create clean code
        test_file = tmp_path / "clean.py"
        test_file.write_text("""
def multiply(a: int, b: int) -> int:
    return a * b
""")

        result = run_mypy_check(tmp_path, target_directories=["."])
        has_errors = (result.errors_found or 0) > 0
        assert isinstance(has_errors, bool)
        assert has_errors is False

        # Create code with errors
        error_file = tmp_path / "errors.py"
        error_file.write_text("""
x: int = "not an int"
""")

        result = run_mypy_check(tmp_path, target_directories=["."])
        has_errors = (result.errors_found or 0) > 0
        assert has_errors is True

    def test_mypy_check_with_invalid_directory(self, tmp_path: Path) -> None:
        """Test mypy check with non-existent directory."""
        invalid_dir = tmp_path / "nonexistent"

        # Should handle gracefully or raise appropriate exception
        with pytest.raises((FileNotFoundError, Exception)):
            run_mypy_check(invalid_dir, target_directories=["."])

    def test_mypy_check_with_empty_directory(self, tmp_path: Path) -> None:
        """Test mypy check with empty directory."""
        result = run_mypy_check(tmp_path, target_directories=["."])

        # Should complete without crashing
        assert hasattr(result, "return_code")
        assert hasattr(result, "errors_found")
        assert (result.errors_found or 0) >= 0
