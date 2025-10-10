"""Tests for create_plan workflow argument parsing functionality."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from workflows.create_plan import parse_arguments, resolve_project_dir


class TestParseArguments:
    """Test parse_arguments function."""

    def test_parse_arguments_with_issue_number(self) -> None:
        """Test parsing with only required issue number argument."""
        test_args = ["create_plan.py", "123"]

        with patch.object(sys, "argv", test_args):
            args = parse_arguments()

        assert args.issue_number == 123
        assert args.project_dir is None
        assert args.log_level == "INFO"
        assert args.llm_method == "claude_code_cli"

    def test_parse_arguments_with_all_options(self) -> None:
        """Test parsing with all optional arguments specified."""
        test_args = [
            "create_plan.py",
            "456",
            "--project-dir",
            "/path/to/project",
            "--log-level",
            "DEBUG",
            "--llm-method",
            "claude_code_api",
        ]

        with patch.object(sys, "argv", test_args):
            args = parse_arguments()

        assert args.issue_number == 456
        assert args.project_dir == "/path/to/project"
        assert args.log_level == "DEBUG"
        assert args.llm_method == "claude_code_api"

    def test_parse_arguments_with_project_dir_only(self) -> None:
        """Test parsing with issue number and project directory."""
        test_args = [
            "create_plan.py",
            "789",
            "--project-dir",
            "C:\\Users\\test\\project",
        ]

        with patch.object(sys, "argv", test_args):
            args = parse_arguments()

        assert args.issue_number == 789
        assert args.project_dir == "C:\\Users\\test\\project"
        assert args.log_level == "INFO"
        assert args.llm_method == "claude_code_cli"

    def test_parse_arguments_with_log_level_only(self) -> None:
        """Test parsing with issue number and log level."""
        test_args = [
            "create_plan.py",
            "101",
            "--log-level",
            "WARNING",
        ]

        with patch.object(sys, "argv", test_args):
            args = parse_arguments()

        assert args.issue_number == 101
        assert args.project_dir is None
        assert args.log_level == "WARNING"
        assert args.llm_method == "claude_code_cli"

    def test_parse_arguments_with_llm_method_only(self) -> None:
        """Test parsing with issue number and LLM method."""
        test_args = [
            "create_plan.py",
            "202",
            "--llm-method",
            "claude_code_api",
        ]

        with patch.object(sys, "argv", test_args):
            args = parse_arguments()

        assert args.issue_number == 202
        assert args.project_dir is None
        assert args.log_level == "INFO"
        assert args.llm_method == "claude_code_api"

    def test_parse_arguments_missing_issue_number(self) -> None:
        """Test parsing without required issue number exits with error."""
        test_args = ["create_plan.py"]

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()
            assert (
                exc_info.value.code == 2
            )  # argparse exit code for missing required arg

    def test_parse_arguments_invalid_issue_number(self) -> None:
        """Test parsing with non-integer issue number exits with error."""
        test_args = ["create_plan.py", "not_a_number"]

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()
            assert exc_info.value.code == 2  # argparse exit code for invalid type

    def test_parse_arguments_invalid_log_level(self) -> None:
        """Test parsing with invalid log level exits with error."""
        test_args = [
            "create_plan.py",
            "123",
            "--log-level",
            "INVALID",
        ]

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()
            assert exc_info.value.code == 2  # argparse exit code for invalid choice

    def test_parse_arguments_invalid_llm_method(self) -> None:
        """Test parsing with invalid LLM method exits with error."""
        test_args = [
            "create_plan.py",
            "123",
            "--llm-method",
            "invalid_method",
        ]

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()
            assert exc_info.value.code == 2  # argparse exit code for invalid choice

    def test_parse_arguments_all_log_levels(self) -> None:
        """Test parsing with all valid log levels."""
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in log_levels:
            test_args = [
                "create_plan.py",
                "123",
                "--log-level",
                level,
            ]

            with patch.object(sys, "argv", test_args):
                args = parse_arguments()
                assert args.log_level == level

    def test_parse_arguments_all_llm_methods(self) -> None:
        """Test parsing with all valid LLM methods."""
        llm_methods = ["claude_code_cli", "claude_code_api"]

        for method in llm_methods:
            test_args = [
                "create_plan.py",
                "123",
                "--llm-method",
                method,
            ]

            with patch.object(sys, "argv", test_args):
                args = parse_arguments()
                assert args.llm_method == method


class TestResolveProjectDir:
    """Test resolve_project_dir function."""

    def test_resolve_project_dir_current_directory(self, tmp_path: Path) -> None:
        """Test resolve_project_dir with None uses current working directory."""
        # Create .git directory in temp path
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = resolve_project_dir(None)
            assert result == tmp_path

    def test_resolve_project_dir_explicit_path(self, tmp_path: Path) -> None:
        """Test resolve_project_dir with explicit valid project directory."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = resolve_project_dir(str(tmp_path))
        assert result == tmp_path

    def test_resolve_project_dir_explicit_path_resolved(self, tmp_path: Path) -> None:
        """Test resolve_project_dir resolves to absolute path."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Create a subdirectory to test relative path resolution
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        subdir_git = subdir / ".git"
        subdir_git.mkdir()

        result = resolve_project_dir(str(subdir))
        assert result == subdir
        assert result.is_absolute()

    def test_resolve_project_dir_invalid_path(self) -> None:
        """Test resolve_project_dir with invalid path exits with code 1."""
        with pytest.raises(SystemExit) as exc_info:
            resolve_project_dir("/invalid/nonexistent/path/that/does/not/exist")
        assert exc_info.value.code == 1

    def test_resolve_project_dir_not_directory(self, tmp_path: Path) -> None:
        """Test resolve_project_dir with non-directory path exits with code 1."""
        # Create a file instead of directory
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")

        with pytest.raises(SystemExit) as exc_info:
            resolve_project_dir(str(test_file))
        assert exc_info.value.code == 1

    def test_resolve_project_dir_not_git_repository(self, tmp_path: Path) -> None:
        """Test resolve_project_dir without .git directory exits with code 1."""
        # Create directory but no .git subdirectory
        with pytest.raises(SystemExit) as exc_info:
            resolve_project_dir(str(tmp_path))
        assert exc_info.value.code == 1

    def test_resolve_project_dir_permission_error(self, tmp_path: Path) -> None:
        """Test resolve_project_dir with permission error exits with code 1."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Mock permission error during directory listing
        with patch.object(
            Path, "iterdir", side_effect=PermissionError("Access denied")
        ):
            with pytest.raises(SystemExit) as exc_info:
                resolve_project_dir(str(tmp_path))
            assert exc_info.value.code == 1

    def test_resolve_project_dir_resolve_error(self) -> None:
        """Test resolve_project_dir with path resolve error exits with code 1."""
        # Mock OSError during path resolution
        with patch.object(Path, "resolve", side_effect=OSError("Path error")):
            with pytest.raises(SystemExit) as exc_info:
                resolve_project_dir("/some/path")
            assert exc_info.value.code == 1

    def test_resolve_project_dir_value_error(self) -> None:
        """Test resolve_project_dir with ValueError during path resolution exits with code 1."""
        # Mock ValueError during path resolution
        with patch.object(Path, "resolve", side_effect=ValueError("Invalid path")):
            with pytest.raises(SystemExit) as exc_info:
                resolve_project_dir("/some/path")
            assert exc_info.value.code == 1

    def test_resolve_project_dir_relative_path(self, tmp_path: Path) -> None:
        """Test resolve_project_dir converts relative path to absolute."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Test with absolute path
        result = resolve_project_dir(str(tmp_path))
        assert result.is_absolute()
        assert result == tmp_path

    def test_resolve_project_dir_with_trailing_slash(self, tmp_path: Path) -> None:
        """Test resolve_project_dir handles paths with trailing slashes."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Add trailing slash (works on both Windows and Unix)
        path_with_slash = str(tmp_path) + "/"
        result = resolve_project_dir(path_with_slash)
        assert result == tmp_path

    def test_resolve_project_dir_git_directory_validation(self, tmp_path: Path) -> None:
        """Test resolve_project_dir specifically validates .git directory exists."""
        # First verify it fails without .git
        with pytest.raises(SystemExit) as exc_info:
            resolve_project_dir(str(tmp_path))
        assert exc_info.value.code == 1

        # Now add .git and verify it succeeds
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        result = resolve_project_dir(str(tmp_path))
        assert result == tmp_path
