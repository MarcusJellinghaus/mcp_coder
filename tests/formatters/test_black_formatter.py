"""Tests for Black formatter implementation using directory-based approach.

Based on Step 1 requirements: Test directory-based Black execution with
output parsing to determine changed files, eliminating file-by-file processing.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

from mcp_coder.formatters import FormatterResult


# Test fixtures and utilities
@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        yield project_path


@pytest.fixture
def unformatted_python_code() -> str:
    """Sample Python code that needs Black formatting."""
    return """def hello(name,age):
    if name=="Alice":
        print(f"Hello {name}, you are {age} years old")
    else:
        print("Hello stranger")
"""


@pytest.fixture
def formatted_python_code() -> str:
    """Sample Python code that is already properly formatted."""
    return """def hello(name: str, age: int) -> None:
    if name == "Alice":
        print(f"Hello {name}, you are {age} years old")
    else:
        print("Hello stranger")
"""


@pytest.fixture
def syntax_error_code() -> str:
    """Python code with syntax errors."""
    return """def broken_function(
    print("This has syntax errors"
    invalid syntax here
"""


@pytest.fixture
def pyproject_toml_with_black_config() -> str:
    """pyproject.toml content with Black configuration."""
    return """[tool.black]
line-length = 100
target-version = ["py311"]
"""


class TestBlackFormatterCore:
    """Core directory-based formatting scenarios - 3 tests."""

    def test_format_directory_with_unformatted_code(
        self, temp_project_dir: Path, unformatted_python_code: str, monkeypatch
    ) -> None:
        """Test directory-based Black execution with output parsing."""
        from mcp_coder.formatters.black_formatter import format_with_black

        # Create a Python file that needs formatting
        src_dir = temp_project_dir / "src"
        src_dir.mkdir()
        test_file = src_dir / "test_module.py"
        test_file.write_text(unformatted_python_code)

        # Mock execute_command to simulate Black directory-based execution
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.return_code = 0  # Black returns 0 when files are reformatted
        mock_result.stdout = ""
        mock_result.stderr = (
            f"reformatted {test_file}\nAll done! ✨ 🍰 ✨\n1 file reformatted."
        )

        def mock_execute_command(cmd):
            return mock_result

        monkeypatch.setattr(
            "mcp_coder.formatters.black_formatter.execute_command", mock_execute_command
        )

        # Format the code using directory-based approach
        result = format_with_black(temp_project_dir)

        # Should succeed and report the file as changed
        assert result.success is True
        assert result.formatter_name == "black"
        assert str(test_file) in result.files_changed
        assert result.error_message is None

        # The mock was called successfully if we got here without exceptions
        # In a real scenario, we would verify the command was called correctly

    def test_format_directory_no_changes_needed(
        self, temp_project_dir: Path, formatted_python_code: str, monkeypatch
    ) -> None:
        """Test directory-based Black on already formatted code (exit 0 → no changes)."""
        from mcp_coder.formatters.black_formatter import format_with_black

        # Create a Python file that is already formatted
        src_dir = temp_project_dir / "src"
        src_dir.mkdir()
        test_file = src_dir / "test_module.py"
        test_file.write_text(formatted_python_code)

        # Mock execute_command to simulate Black finding no changes needed
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.return_code = 0  # Black returns 0 when no reformatting needed
        mock_result.stdout = ""
        mock_result.stderr = "All done! ✨ 🍰 ✨\n0 files reformatted."

        def mock_execute_command(cmd):
            return mock_result

        monkeypatch.setattr(
            "mcp_coder.formatters.black_formatter.execute_command", mock_execute_command
        )

        # Format the code using directory-based approach
        result = format_with_black(temp_project_dir)

        # Should succeed but report no changes
        assert result.success is True
        assert result.formatter_name == "black"
        assert len(result.files_changed) == 0
        assert result.error_message is None

    def test_format_directory_with_syntax_errors(
        self, temp_project_dir: Path, syntax_error_code: str, monkeypatch
    ) -> None:
        """Test directory-based Black with syntax errors (exit 123 → error)."""
        from mcp_coder.formatters.black_formatter import format_with_black

        # Create a Python file with syntax errors
        src_dir = temp_project_dir / "src"
        src_dir.mkdir()
        test_file = src_dir / "broken_module.py"
        test_file.write_text(syntax_error_code)

        # Mock execute_command to simulate Black syntax error
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.return_code = 123  # Black returns 123 for syntax errors
        mock_result.stdout = ""
        mock_result.stderr = (
            "error: cannot use --safe with this file; failed to parse source file"
        )

        def mock_execute_command(cmd):
            return mock_result

        monkeypatch.setattr(
            "mcp_coder.formatters.black_formatter.execute_command", mock_execute_command
        )

        # Attempt to format the code
        result = format_with_black(temp_project_dir)

        # Should fail due to syntax errors
        assert result.success is False
        assert result.formatter_name == "black"
        assert len(result.files_changed) == 0
        assert result.error_message is not None
        assert "error" in result.error_message.lower()


class TestBlackFormatterConfiguration:
    """Configuration integration - 2 tests."""

    def test_default_config_missing_pyproject(
        self, temp_project_dir: Path, unformatted_python_code: str, monkeypatch
    ) -> None:
        """Test directory-based formatting with missing pyproject.toml (use Black defaults)."""
        from mcp_coder.formatters.black_formatter import format_with_black

        # Create source directory and file
        src_dir = temp_project_dir / "src"
        src_dir.mkdir()
        test_file = src_dir / "test_module.py"
        test_file.write_text(unformatted_python_code)

        # Mock execute_command to simulate Black with default config
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.return_code = 0
        mock_result.stdout = ""
        mock_result.stderr = (
            f"reformatted {test_file}\nAll done! ✨ 🍰 ✨\n1 file reformatted."
        )

        def mock_execute_command(cmd):
            return mock_result

        monkeypatch.setattr(
            "mcp_coder.formatters.black_formatter.execute_command", mock_execute_command
        )

        # Format using directory-based approach with defaults
        result = format_with_black(temp_project_dir)
        assert result.success is True
        assert str(test_file) in result.files_changed

    def test_custom_config_from_pyproject(
        self,
        temp_project_dir: Path,
        unformatted_python_code: str,
        pyproject_toml_with_black_config: str,
        monkeypatch,
    ) -> None:
        """Test directory-based formatting with custom pyproject.toml configuration."""
        from mcp_coder.formatters.black_formatter import format_with_black

        # Create pyproject.toml with custom Black config
        pyproject_file = temp_project_dir / "pyproject.toml"
        pyproject_file.write_text(pyproject_toml_with_black_config)

        # Create source directory and file
        src_dir = temp_project_dir / "src"
        src_dir.mkdir()
        test_file = src_dir / "test_module.py"
        test_file.write_text(unformatted_python_code)

        # Mock execute_command to simulate Black with custom config
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.return_code = 0
        mock_result.stdout = ""
        mock_result.stderr = (
            f"reformatted {test_file}\nAll done! ✨ 🍰 ✨\n1 file reformatted."
        )

        def mock_execute_command(cmd):
            return mock_result

        monkeypatch.setattr(
            "mcp_coder.formatters.black_formatter.execute_command", mock_execute_command
        )

        # Format using directory-based approach with custom config
        result = format_with_black(temp_project_dir)
        assert result.success is True
        assert str(test_file) in result.files_changed


class TestBlackFormatterRealWorld:
    """Real-world analysis scenario - 1 test."""

    def test_analysis_code_sample(self, temp_project_dir: Path, monkeypatch) -> None:
        """Use actual unformatted code from Step 0 findings to verify patterns."""
        from mcp_coder.formatters.black_formatter import format_with_black

        # Real unformatted code sample similar to what might be analyzed
        analysis_code = """#!/usr/bin/env python3
import subprocess,sys,json
from pathlib import Path

def run_black_check(files):
    cmd=['black','--check']+files
    result=subprocess.run(cmd,capture_output=True,text=True)
    if result.returncode==0:
        return {"status":"no_changes","files":[]}
    elif result.returncode==1:
        return {"status":"changes_needed","files":files}
    else:
        return {"status":"error","message":result.stderr}

def main():
    if len(sys.argv)<2:
        print("Usage: script.py <files>")
        sys.exit(1)
    files=sys.argv[1:]
    result=run_black_check(files)
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
"""

        # Create the analysis code file in src directory
        src_dir = temp_project_dir / "src"
        src_dir.mkdir()
        test_file = src_dir / "analysis_script.py"
        test_file.write_text(analysis_code)

        # Mock execute_command to simulate Black reformatting
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.return_code = 0
        mock_result.stdout = ""
        mock_result.stderr = (
            f"reformatted {test_file}\nAll done! ✨ 🍰 ✨\n1 file reformatted."
        )

        def mock_execute_command(cmd):
            return mock_result

        monkeypatch.setattr(
            "mcp_coder.formatters.black_formatter.execute_command", mock_execute_command
        )

        # Format using our Black formatter
        result = format_with_black(temp_project_dir)

        # Should successfully format the code
        assert result.success is True
        assert result.formatter_name == "black"
        assert str(test_file) in result.files_changed
        assert result.error_message is None


class TestBlackFormatterUtilities:
    """Test directory-based utility functions."""

    def test_parse_black_output_with_reformatted_files(self) -> None:
        """Test _parse_black_output function with various Black stderr formats."""
        from mcp_coder.formatters.black_formatter import _parse_black_output

        # Test single file reformatted
        stderr_single = (
            "reformatted /path/to/file.py\nAll done! ✨ 🍰 ✨\n1 file reformatted."
        )
        changed_files = _parse_black_output(stderr_single)
        assert changed_files == ["/path/to/file.py"]

        # Test multiple files reformatted
        stderr_multiple = "reformatted /path/to/file1.py\nreformatted /path/to/file2.py\nAll done! ✨ 🍰 ✨\n2 files reformatted."
        changed_files = _parse_black_output(stderr_multiple)
        assert changed_files == ["/path/to/file1.py", "/path/to/file2.py"]

        # Test no changes
        stderr_no_changes = "All done! ✨ 🍰 ✨\n0 files reformatted."
        changed_files = _parse_black_output(stderr_no_changes)
        assert changed_files == []

        # Test files with spaces in paths
        stderr_spaces = "reformatted /path/with spaces/file.py\nAll done! ✨ 🍰 ✨\n1 file reformatted."
        changed_files = _parse_black_output(stderr_spaces)
        assert changed_files == ["/path/with spaces/file.py"]

    def test_format_black_directory_function(
        self, temp_project_dir: Path, unformatted_python_code: str, monkeypatch
    ) -> None:
        """Test _format_black_directory function directly."""
        from mcp_coder.formatters.black_formatter import _format_black_directory

        # Create source directory and file
        src_dir = temp_project_dir / "src"
        src_dir.mkdir()
        test_file = src_dir / "test_module.py"
        test_file.write_text(unformatted_python_code)

        # Mock execute_command
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.return_code = 0
        mock_result.stdout = ""
        mock_result.stderr = (
            f"reformatted {test_file}\nAll done! ✨ 🍰 ✨\n1 file reformatted."
        )

        def mock_execute_command(cmd):
            return mock_result

        monkeypatch.setattr(
            "mcp_coder.formatters.black_formatter.execute_command", mock_execute_command
        )

        # Test directory formatting
        config = {"line-length": 88, "target-version": ["py311"]}
        changed_files = _format_black_directory(src_dir, config)

        assert str(test_file) in changed_files
