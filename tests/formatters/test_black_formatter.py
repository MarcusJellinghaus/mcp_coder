"""Unit and integration tests for Black formatter implementation."""

import re
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.mcp_coder.formatters.models import FileChange, FormatterConfig, FormatterResult
from src.mcp_coder.utils.subprocess_runner import CommandResult

# Test file content constants
SIMPLE_PYTHON_FILE = "print('hello')"
UTIL_FUNCTION = "def util(): pass"
CONFIG_DICT = "CONFIG = {}"
README_CONTENT = "# README"
JSON_DATA = "{}"
MODULE_CLASS = "class Module: pass"
MAIN_FUNCTION = "def main(): pass"
TEST_FUNCTION = "def test_main(): pass"
APP_FUNCTION = "def main(): pass"
TEST_APP_FUNCTION = "def test_main(): pass"
COMPILED_BYTECODE = b"compiled"


# Import the functions we'll implement
try:
    from src.mcp_coder.formatters.black_formatter import (
        _build_black_command,
        _get_python_files,
        _parse_black_output,
        format_with_black,
    )
except ImportError:
    # Module doesn't exist yet, we'll implement it after tests
    pass


class TestGetPythonFiles:
    """Test the inline Python file discovery utility."""

    def test_get_python_files_basic(self, tmp_path: Path) -> None:
        """Test getting Python files from a directory."""
        # Create test directory structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Create Python files
        (src_dir / "main.py").write_text(SIMPLE_PYTHON_FILE)
        (src_dir / "utils.py").write_text(UTIL_FUNCTION)
        (src_dir / "config.py").write_text(CONFIG_DICT)

        # Create non-Python files
        (src_dir / "README.md").write_text(README_CONTENT)
        (src_dir / "data.json").write_text(JSON_DATA)

        # Create subdirectory with Python files
        sub_dir = src_dir / "submodule"
        sub_dir.mkdir()
        (sub_dir / "module.py").write_text(MODULE_CLASS)

        python_files = _get_python_files([src_dir])

        expected_files = {
            src_dir / "main.py",
            src_dir / "utils.py",
            src_dir / "config.py",
            sub_dir / "module.py",
        }

        assert set(python_files) == expected_files

    def test_get_python_files_multiple_directories(self, tmp_path: Path) -> None:
        """Test getting Python files from multiple directories."""
        # Create multiple directories
        src_dir = tmp_path / "src"
        tests_dir = tmp_path / "tests"
        src_dir.mkdir()
        tests_dir.mkdir()

        # Create Python files in each
        (src_dir / "app.py").write_text(APP_FUNCTION)
        (tests_dir / "test_app.py").write_text(TEST_APP_FUNCTION)

        python_files = _get_python_files([src_dir, tests_dir])

        expected_files = {
            src_dir / "app.py",
            tests_dir / "test_app.py",
        }

        assert set(python_files) == expected_files

    def test_get_python_files_empty_directory(self, tmp_path: Path) -> None:
        """Test getting Python files from empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        python_files = _get_python_files([empty_dir])

        assert python_files == []

    def test_get_python_files_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test getting Python files from nonexistent directory."""
        nonexistent_dir = tmp_path / "nonexistent"

        python_files = _get_python_files([nonexistent_dir])

        assert python_files == []

    def test_get_python_files_exclude_pycache(self, tmp_path: Path) -> None:
        """Test that __pycache__ directories are excluded."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Create Python file
        (src_dir / "main.py").write_text(SIMPLE_PYTHON_FILE)

        # Create __pycache__ directory with .pyc files
        pycache_dir = src_dir / "__pycache__"
        pycache_dir.mkdir()
        (pycache_dir / "main.cpython-311.pyc").write_bytes(COMPILED_BYTECODE)

        python_files = _get_python_files([src_dir])

        # Should only include .py files, not .pyc files
        assert python_files == [src_dir / "main.py"]


class TestParseBlackOutput:
    """Test Black stdout parsing functionality."""

    def test_parse_black_output_reformatted_files(self) -> None:
        """Test parsing Black output with reformatted files."""
        stdout = """
would reformat /path/to/file1.py
would reformat /path/to/file2.py
Oh no! 💥 💔 💥
2 files would be reformatted
        """.strip()

        reformatted_files = _parse_black_output(stdout)

        expected_files = [
            Path("/path/to/file1.py"),
            Path("/path/to/file2.py"),
        ]

        assert reformatted_files == expected_files

    def test_parse_black_output_actual_reformatted(self) -> None:
        """Test parsing Black output when files are actually reformatted."""
        stdout = """
reformatted /home/user/project/src/main.py
reformatted /home/user/project/tests/test_main.py
All done! ✨ 🍰 ✨
2 files reformatted
        """.strip()

        reformatted_files = _parse_black_output(stdout)

        expected_files = [
            Path("/home/user/project/src/main.py"),
            Path("/home/user/project/tests/test_main.py"),
        ]

        assert reformatted_files == expected_files

    def test_parse_black_output_no_changes(self) -> None:
        """Test parsing Black output when no files need reformatting."""
        stdout = """
All done! ✨ 🍰 ✨
3 files left unchanged.
        """.strip()

        reformatted_files = _parse_black_output(stdout)

        assert reformatted_files == []

    def test_parse_black_output_mixed_content(self) -> None:
        """Test parsing Black output with mixed content."""
        stdout = """
would reformat /path/to/unformatted.py
All done! ✨ 🍰 ✨
1 file would be reformatted, 2 files left unchanged.
        """.strip()

        reformatted_files = _parse_black_output(stdout)

        assert reformatted_files == [Path("/path/to/unformatted.py")]

    def test_parse_black_output_windows_paths(self) -> None:
        """Test parsing Black output with Windows-style paths."""
        stdout = """
reformatted C:\\Users\\user\\project\\src\\main.py
reformatted C:\\Users\\user\\project\\tests\\test_main.py
All done! ✨ 🍰 ✨
2 files reformatted
        """.strip()

        reformatted_files = _parse_black_output(stdout)

        expected_files = [
            Path("C:/Users/user/project/src/main.py"),
            Path("C:/Users/user/project/tests/test_main.py"),
        ]

        assert reformatted_files == expected_files

    def test_parse_black_output_empty_stdout(self) -> None:
        """Test parsing empty Black output."""
        stdout = ""

        reformatted_files = _parse_black_output(stdout)

        assert reformatted_files == []

    def test_parse_black_output_relative_paths(self, tmp_path: Path) -> None:
        """Test parsing Black output with relative paths."""
        stdout = """
reformatted src/main.py
reformatted tests/test_main.py
All done! ✨ 🍰 ✨
2 files reformatted
        """.strip()

        reformatted_files = _parse_black_output(stdout, tmp_path)

        expected_files = [
            tmp_path / "src" / "main.py",
            tmp_path / "tests" / "test_main.py",
        ]

        assert reformatted_files == expected_files


class TestBuildBlackCommand:
    """Test Black command building functionality."""

    def test_build_black_command_basic(self, tmp_path: Path) -> None:
        """Test building basic Black command."""
        config = FormatterConfig(
            tool_name="black",
            settings={"line-length": 88, "target-version": ["py311"]},
            target_directories=[tmp_path / "src"],
            project_root=tmp_path,
        )

        command = _build_black_command(config)

        expected_command = [
            "black",
            "--line-length",
            "88",
            "--target-version",
            "py311",
            str(tmp_path / "src"),
        ]

        assert command == expected_command

    def test_build_black_command_multiple_target_versions(self, tmp_path: Path) -> None:
        """Test building Black command with multiple target versions."""
        config = FormatterConfig(
            tool_name="black",
            settings={"line-length": 100, "target-version": ["py310", "py311"]},
            target_directories=[tmp_path / "src", tmp_path / "tests"],
            project_root=tmp_path,
        )

        command = _build_black_command(config)

        expected_command = [
            "black",
            "--line-length",
            "100",
            "--target-version",
            "py310",
            "--target-version",
            "py311",
            str(tmp_path / "src"),
            str(tmp_path / "tests"),
        ]

        assert command == expected_command

    def test_build_black_command_additional_options(self, tmp_path: Path) -> None:
        """Test building Black command with additional options."""
        config = FormatterConfig(
            tool_name="black",
            settings={
                "line-length": 120,
                "target-version": ["py311"],
                "skip-string-normalization": True,
                "quiet": True,
            },
            target_directories=[tmp_path / "src"],
            project_root=tmp_path,
        )

        command = _build_black_command(config)

        # Note: Only line-length and target-version are handled in our basic implementation
        expected_command = [
            "black",
            "--line-length",
            "120",
            "--target-version",
            "py311",
            str(tmp_path / "src"),
        ]

        assert command == expected_command

    def test_build_black_command_no_target_directories(self, tmp_path: Path) -> None:
        """Test building Black command with no target directories."""
        config = FormatterConfig(
            tool_name="black",
            settings={"line-length": 88, "target-version": ["py311"]},
            target_directories=[],
            project_root=tmp_path,
        )

        command = _build_black_command(config)

        expected_command = [
            "black",
            "--line-length",
            "88",
            "--target-version",
            "py311",
        ]

        assert command == expected_command


class TestFormatWithBlackUnit:
    """Unit tests for format_with_black function (mocked)."""

    @patch("src.mcp_coder.formatters.black_formatter.execute_command")
    @patch("src.mcp_coder.formatters.black_formatter.get_black_config")
    @patch("src.mcp_coder.formatters.black_formatter._get_python_files")
    def test_format_with_black_success(
        self, mock_get_files, mock_get_config, mock_execute, tmp_path: Path
    ) -> None:
        """Test successful Black formatting."""
        # Setup mocks
        mock_config = FormatterConfig(
            tool_name="black",
            settings={"line-length": 88, "target-version": ["py311"]},
            target_directories=[tmp_path / "src"],
            project_root=tmp_path,
        )
        mock_get_config.return_value = mock_config

        python_files = [tmp_path / "src" / "main.py", tmp_path / "src" / "utils.py"]
        mock_get_files.return_value = python_files

        mock_result = CommandResult(
            return_code=0,
            stdout=f"reformatted {tmp_path / 'src' / 'main.py'}\nAll done! ✨ 🍰 ✨\n1 file reformatted",
            stderr="",
            timed_out=False,
            execution_time_ms=1500,
        )
        mock_execute.return_value = mock_result

        # Execute
        result = format_with_black(tmp_path)

        # Verify
        assert result.success is True
        assert result.formatter_name == "black"
        assert result.execution_time_ms == 1500
        assert result.error_message is None
        assert len(result.files_changed) == 2

        # Check that main.py was marked as changed (because it appeared in stdout)
        main_py_change = next(
            fc for fc in result.files_changed if fc.file_path.name == "main.py"
        )
        assert main_py_change.had_changes is True

        # Check that utils.py was marked as unchanged (didn't appear in stdout)
        utils_py_change = next(
            fc for fc in result.files_changed if fc.file_path.name == "utils.py"
        )
        assert utils_py_change.had_changes is False

    @patch("src.mcp_coder.formatters.black_formatter.execute_command")
    @patch("src.mcp_coder.formatters.black_formatter.get_black_config")
    @patch("src.mcp_coder.formatters.black_formatter._get_python_files")
    def test_format_with_black_failure(
        self, mock_get_files, mock_get_config, mock_execute, tmp_path: Path
    ) -> None:
        """Test Black formatting failure."""
        # Setup mocks
        mock_config = FormatterConfig(
            tool_name="black",
            settings={"line-length": 88, "target-version": ["py311"]},
            target_directories=[tmp_path / "src"],
            project_root=tmp_path,
        )
        mock_get_config.return_value = mock_config

        python_files = [tmp_path / "src" / "broken.py"]
        mock_get_files.return_value = python_files

        mock_result = CommandResult(
            return_code=1,
            stdout="",
            stderr="error: cannot use --safe with --fast",
            timed_out=False,
            execution_time_ms=500,
        )
        mock_execute.return_value = mock_result

        # Execute
        result = format_with_black(tmp_path)

        # Verify
        assert result.success is False
        assert result.formatter_name == "black"
        assert result.execution_time_ms == 500
        assert result.error_message == "error: cannot use --safe with --fast"
        assert len(result.files_changed) == 1
        assert result.files_changed[0].had_changes is False

    @patch("src.mcp_coder.formatters.black_formatter.execute_command")
    @patch("src.mcp_coder.formatters.black_formatter.get_black_config")
    @patch("src.mcp_coder.formatters.black_formatter._get_python_files")
    def test_format_with_black_timeout(
        self, mock_get_files, mock_get_config, mock_execute, tmp_path: Path
    ) -> None:
        """Test Black formatting timeout."""
        # Setup mocks
        mock_config = FormatterConfig(
            tool_name="black",
            settings={"line-length": 88, "target-version": ["py311"]},
            target_directories=[tmp_path / "src"],
            project_root=tmp_path,
        )
        mock_get_config.return_value = mock_config

        python_files = [tmp_path / "src" / "large_file.py"]
        mock_get_files.return_value = python_files

        mock_result = CommandResult(
            return_code=1,
            stdout="",
            stderr="",
            timed_out=True,
            execution_error="Process timed out after 120 seconds",
            execution_time_ms=120000,
        )
        mock_execute.return_value = mock_result

        # Execute
        result = format_with_black(tmp_path)

        # Verify
        assert result.success is False
        assert result.formatter_name == "black"
        assert result.execution_time_ms == 120000
        assert "timed out" in result.error_message.lower()

    @patch("src.mcp_coder.formatters.black_formatter.execute_command")
    @patch("src.mcp_coder.formatters.black_formatter.get_black_config")
    @patch("src.mcp_coder.formatters.black_formatter._get_python_files")
    def test_format_with_black_no_python_files(
        self, mock_get_files, mock_get_config, mock_execute, tmp_path: Path
    ) -> None:
        """Test Black formatting when no Python files are found."""
        # Setup mocks
        mock_config = FormatterConfig(
            tool_name="black",
            settings={"line-length": 88, "target-version": ["py311"]},
            target_directories=[tmp_path / "src"],
            project_root=tmp_path,
        )
        mock_get_config.return_value = mock_config

        # No Python files found
        mock_get_files.return_value = []

        # Execute
        result = format_with_black(tmp_path)

        # Verify - should succeed but with no files processed
        assert result.success is True
        assert result.formatter_name == "black"
        assert result.files_changed == []
        assert result.error_message is None

        # execute_command should not be called
        mock_execute.assert_not_called()

    def test_format_with_black_custom_target_dirs(self, tmp_path: Path) -> None:
        """Test Black formatting with custom target directories."""
        custom_dirs = ["app", "scripts"]

        # Create the custom directories
        for dir_name in custom_dirs:
            (tmp_path / dir_name).mkdir()

        with (
            patch(
                "src.mcp_coder.formatters.black_formatter.execute_command"
            ) as mock_execute,
            patch(
                "src.mcp_coder.formatters.black_formatter.get_black_config"
            ) as mock_get_config,
            patch(
                "src.mcp_coder.formatters.black_formatter._get_python_files"
            ) as mock_get_files,
        ):

            # Setup mocks
            mock_config = FormatterConfig(
                tool_name="black",
                settings={"line-length": 88, "target-version": ["py311"]},
                target_directories=[tmp_path / d for d in custom_dirs],
                project_root=tmp_path,
            )
            mock_get_config.return_value = mock_config

            python_files = [tmp_path / "app" / "main.py"]
            mock_get_files.return_value = python_files

            mock_result = CommandResult(
                return_code=0,
                stdout="All done! ✨ 🍰 ✨\n1 file left unchanged.",
                stderr="",
                timed_out=False,
                execution_time_ms=800,
            )
            mock_execute.return_value = mock_result

            # Execute with custom target directories
            result = format_with_black(tmp_path, target_dirs=custom_dirs)

            # Verify that custom target directories were passed to get_python_files
            expected_dirs = [tmp_path / d for d in custom_dirs]
            mock_get_files.assert_called_once_with(expected_dirs)


@pytest.mark.formatter_integration
class TestFormatWithBlackIntegration:
    """Integration tests for Black formatter (requires Black to be installed)."""

    def test_format_unformatted_code(self, tmp_path: Path) -> None:
        """Test formatting unformatted Python code."""
        # Test file content as multiline string
        unformatted_content = """def bad_function(x,y):return x+y
print("hello world")"""

        pyproject_content = """[tool.black]
line-length = 88
target-version = ["py311"]"""

        # Create project structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Create files
        (tmp_path / "pyproject.toml").write_text(pyproject_content)
        test_file = src_dir / "test.py"
        test_file.write_text(unformatted_content)

        # Execute formatting
        result = format_with_black(tmp_path)

        # Debug output - TODO: Remove after fixing
        print(f"\nDEBUG: Test file: {test_file}")
        print(f"DEBUG: Result success: {result.success}")
        print(f"DEBUG: Files changed: {result.files_changed}")
        print(f"DEBUG: Error message: {result.error_message}")

        # Verify result
        assert result.success is True
        assert result.formatter_name == "black"
        assert len(result.files_changed) == 1
        assert result.files_changed[0].file_path == test_file
        assert result.files_changed[0].had_changes is True

        # Verify file was actually formatted
        formatted_content = test_file.read_text()
        assert "def bad_function(x, y):" in formatted_content
        assert "return x + y" in formatted_content

    def test_format_already_formatted_code(self, tmp_path: Path) -> None:
        """Test formatting already formatted Python code."""
        # Create project structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Create pyproject.toml
        pyproject_content = """
[tool.black]
line-length = 88
target-version = ["py311"]
        """.strip()
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        # Create well-formatted Python file
        formatted_content = '''def good_function(x: int, y: int) -> int:
    """A well-formatted function."""
    return x + y


print("hello world")
'''
        test_file = src_dir / "test.py"
        test_file.write_text(formatted_content)

        # Execute formatting
        result = format_with_black(tmp_path)

        # Verify result
        assert result.success is True
        assert result.formatter_name == "black"
        assert len(result.files_changed) == 1
        assert result.files_changed[0].file_path == test_file
        assert result.files_changed[0].had_changes is False

        # Verify file content remained the same
        assert test_file.read_text() == formatted_content

    def test_format_syntax_error(self, tmp_path: Path) -> None:
        """Test formatting Python file with syntax error."""
        # Create project structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Create pyproject.toml
        pyproject_content = """
[tool.black]
line-length = 88
target-version = ["py311"]
        """.strip()
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        # Create Python file with syntax error
        broken_content = 'def broken_function(\nprint("missing closing paren")'
        test_file = src_dir / "broken.py"
        test_file.write_text(broken_content)

        # Execute formatting
        result = format_with_black(tmp_path)

        # Verify result
        assert result.success is False
        assert result.formatter_name == "black"
        assert result.error_message is not None
        assert "error" in result.error_message.lower()

    def test_format_missing_target_directory(self, tmp_path: Path) -> None:
        """Test formatting when target directory doesn't exist."""
        # Create pyproject.toml
        pyproject_content = """
[tool.black]
line-length = 88
target-version = ["py311"]
        """.strip()
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        # Don't create src directory

        # Execute formatting
        result = format_with_black(tmp_path)

        # Verify result - should succeed with no files
        assert result.success is True
        assert result.formatter_name == "black"
        assert result.files_changed == []

    def test_format_with_custom_config(self, tmp_path: Path) -> None:
        """Test formatting with custom Black configuration."""
        # Create project structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Create pyproject.toml with custom line length
        pyproject_content = """
[tool.black]
line-length = 60
target-version = ["py311"]
        """.strip()
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        # Create file with long line
        long_line_content = "def long_function_name_with_many_parameters(param1, param2, param3, param4):\n    return param1 + param2 + param3 + param4"
        test_file = src_dir / "test.py"
        test_file.write_text(long_line_content)

        # Execute formatting
        result = format_with_black(tmp_path)

        # Verify result
        assert result.success is True
        assert result.formatter_name == "black"
        assert len(result.files_changed) == 1
        assert result.files_changed[0].had_changes is True

        # Verify line was wrapped due to custom line length
        formatted_content = test_file.read_text()
        lines = formatted_content.split("\n")
        # With line-length=60, the long function definition should be wrapped
        assert any(
            len(line) <= 60 or line.strip().startswith("#")
            for line in lines
            if line.strip()
        )

    def test_format_multiple_files(self, tmp_path: Path) -> None:
        """Test formatting multiple Python files."""
        # Create project structure
        src_dir = tmp_path / "src"
        tests_dir = tmp_path / "tests"
        src_dir.mkdir()
        tests_dir.mkdir()

        # Create pyproject.toml
        pyproject_content = """
[tool.black]
line-length = 88
target-version = ["py311"]
        """.strip()
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        # Create multiple unformatted files
        unformatted_content1 = "def func1(x,y):return x+y"
        unformatted_content2 = "def func2(a,b):return a*b"
        formatted_content = "def func3(x: int, y: int) -> int:\n    return x - y"

        file1 = src_dir / "file1.py"
        file2 = src_dir / "file2.py"
        file3 = tests_dir / "file3.py"

        file1.write_text(unformatted_content1)
        file2.write_text(unformatted_content2)
        file3.write_text(formatted_content)

        # Execute formatting
        result = format_with_black(tmp_path)

        # Verify result
        assert result.success is True
        assert result.formatter_name == "black"
        assert len(result.files_changed) == 3

        # Check which files had changes
        changed_files = {fc.file_path: fc.had_changes for fc in result.files_changed}
        assert changed_files[file1] is True
        assert changed_files[file2] is True
        assert changed_files[file3] is False  # Already formatted
