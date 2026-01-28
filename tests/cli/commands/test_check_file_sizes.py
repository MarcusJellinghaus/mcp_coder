"""Tests for check file-size CLI command."""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.checks.file_sizes import CheckResult, FileMetrics


class TestCheckFileSizesCommand:
    """Test the check file-size CLI command handler."""

    @patch("mcp_coder.cli.commands.check_file_sizes.check_file_sizes")
    @patch("mcp_coder.cli.commands.check_file_sizes.load_allowlist")
    def test_returns_zero_on_pass(
        self, mock_load: MagicMock, mock_check: MagicMock, tmp_path: Path
    ) -> None:
        """Test exit code 0 when all files pass."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Setup mocks
        mock_load.return_value = set()
        mock_check.return_value = CheckResult(
            passed=True,
            violations=[],
            total_files_checked=10,
            allowlisted_count=0,
            stale_entries=[],
        )

        # Create args namespace
        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=600,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )

        # Execute
        result = execute_check_file_sizes(args)

        # Verify
        assert result == 0
        mock_load.assert_called_once()
        mock_check.assert_called_once()

    @patch("mcp_coder.cli.commands.check_file_sizes.check_file_sizes")
    @patch("mcp_coder.cli.commands.check_file_sizes.load_allowlist")
    def test_returns_one_on_violations(
        self, mock_load: MagicMock, mock_check: MagicMock, tmp_path: Path
    ) -> None:
        """Test exit code 1 when violations found."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Setup mocks
        mock_load.return_value = set()
        mock_check.return_value = CheckResult(
            passed=False,
            violations=[FileMetrics(path=Path("src/big_file.py"), line_count=800)],
            total_files_checked=10,
            allowlisted_count=0,
            stale_entries=[],
        )

        # Create args namespace
        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=600,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )

        # Execute
        result = execute_check_file_sizes(args)

        # Verify
        assert result == 1
        mock_check.assert_called_once()

    @patch("mcp_coder.cli.commands.check_file_sizes.check_file_sizes")
    @patch("mcp_coder.cli.commands.check_file_sizes.load_allowlist")
    def test_generate_allowlist_outputs_paths(
        self,
        mock_load: MagicMock,
        mock_check: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test --generate-allowlist outputs violation paths."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Setup mocks
        mock_load.return_value = set()
        violations = [
            FileMetrics(path=Path("src/big_file.py"), line_count=800),
            FileMetrics(path=Path("src/another_big.py"), line_count=700),
        ]
        mock_check.return_value = CheckResult(
            passed=False,
            violations=violations,
            total_files_checked=10,
            allowlisted_count=0,
            stale_entries=[],
        )

        # Create args namespace
        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=600,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=True,
        )

        # Execute
        result = execute_check_file_sizes(args)

        # Verify
        assert result == 1  # Violations exist, so return 1
        captured = capsys.readouterr()
        assert "src/big_file.py" in captured.out
        assert "src/another_big.py" in captured.out

    @patch("mcp_coder.cli.commands.check_file_sizes.check_file_sizes")
    @patch("mcp_coder.cli.commands.check_file_sizes.load_allowlist")
    def test_generate_allowlist_returns_zero_when_no_violations(
        self, mock_load: MagicMock, mock_check: MagicMock, tmp_path: Path
    ) -> None:
        """Test --generate-allowlist returns 0 when no violations."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Setup mocks
        mock_load.return_value = set()
        mock_check.return_value = CheckResult(
            passed=True,
            violations=[],
            total_files_checked=10,
            allowlisted_count=0,
            stale_entries=[],
        )

        # Create args namespace
        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=600,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=True,
        )

        # Execute
        result = execute_check_file_sizes(args)

        # Verify
        assert result == 0

    @patch("mcp_coder.cli.commands.check_file_sizes.check_file_sizes")
    @patch("mcp_coder.cli.commands.check_file_sizes.load_allowlist")
    def test_uses_current_directory_when_project_dir_not_specified(
        self, mock_load: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test that current directory is used when project_dir is None."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Setup mocks
        mock_load.return_value = set()
        mock_check.return_value = CheckResult(
            passed=True,
            violations=[],
            total_files_checked=10,
            allowlisted_count=0,
            stale_entries=[],
        )

        # Create args namespace with no project_dir
        args = argparse.Namespace(
            project_dir=None,
            max_lines=600,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )

        # Execute
        result = execute_check_file_sizes(args)

        # Verify - should use cwd
        assert result == 0
        call_args = mock_check.call_args
        # First positional argument should be the resolved cwd
        assert call_args[0][0] == Path.cwd().resolve()

    @patch("mcp_coder.cli.commands.check_file_sizes.check_file_sizes")
    @patch("mcp_coder.cli.commands.check_file_sizes.load_allowlist")
    def test_passes_max_lines_to_check(
        self, mock_load: MagicMock, mock_check: MagicMock, tmp_path: Path
    ) -> None:
        """Test that max_lines argument is passed to check_file_sizes."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Setup mocks
        mock_load.return_value = set()
        mock_check.return_value = CheckResult(
            passed=True,
            violations=[],
            total_files_checked=10,
            allowlisted_count=0,
            stale_entries=[],
        )

        # Create args namespace with custom max_lines
        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=1000,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )

        # Execute
        execute_check_file_sizes(args)

        # Verify max_lines was passed
        call_args = mock_check.call_args
        assert call_args[0][1] == 1000  # Second positional argument is max_lines

    @patch("mcp_coder.cli.commands.check_file_sizes.check_file_sizes")
    @patch("mcp_coder.cli.commands.check_file_sizes.load_allowlist")
    def test_loads_allowlist_from_project_dir(
        self, mock_load: MagicMock, mock_check: MagicMock, tmp_path: Path
    ) -> None:
        """Test that allowlist is loaded from project directory."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Setup mocks
        allowlist = {"src/allowed_big.py"}
        mock_load.return_value = allowlist
        mock_check.return_value = CheckResult(
            passed=True,
            violations=[],
            total_files_checked=10,
            allowlisted_count=1,
            stale_entries=[],
        )

        # Create args namespace
        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=600,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )

        # Execute
        execute_check_file_sizes(args)

        # Verify allowlist path
        expected_path = tmp_path / ".large-files-allowlist"
        mock_load.assert_called_once_with(expected_path)

        # Verify allowlist was passed to check
        call_args = mock_check.call_args
        assert call_args[0][2] == allowlist  # Third positional argument is allowlist


class TestCheckFileSizesIntegration:
    """Integration tests for check file-size via CLI parser."""

    @patch("mcp_coder.cli.main.execute_check_file_sizes")
    @patch("sys.argv", ["mcp-coder", "check", "file-size"])
    def test_command_routing(self, mock_execute: MagicMock) -> None:
        """Test that check file-size routes to correct handler."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0

        result = main()

        assert result == 0
        mock_execute.assert_called_once()

        # Check that the function was called with proper arguments
        call_args = mock_execute.call_args[0][0]  # First positional argument (args)
        assert isinstance(call_args, argparse.Namespace)

    @patch("mcp_coder.cli.main.execute_check_file_sizes")
    @patch("sys.argv", ["mcp-coder", "check", "file-size", "--max-lines", "1000"])
    def test_max_lines_argument_parsing(self, mock_execute: MagicMock) -> None:
        """Test that --max-lines argument is parsed correctly."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0

        main()

        call_args = mock_execute.call_args[0][0]
        assert call_args.max_lines == 1000

    @patch("mcp_coder.cli.main.execute_check_file_sizes")
    @patch(
        "sys.argv",
        ["mcp-coder", "check", "file-size", "--allowlist-file", "my-allowlist.txt"],
    )
    def test_allowlist_file_argument_parsing(self, mock_execute: MagicMock) -> None:
        """Test that --allowlist-file argument is parsed correctly."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0

        main()

        call_args = mock_execute.call_args[0][0]
        assert call_args.allowlist_file == "my-allowlist.txt"

    @patch("mcp_coder.cli.main.execute_check_file_sizes")
    @patch("sys.argv", ["mcp-coder", "check", "file-size", "--generate-allowlist"])
    def test_generate_allowlist_flag_parsing(self, mock_execute: MagicMock) -> None:
        """Test that --generate-allowlist flag is parsed correctly."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0

        main()

        call_args = mock_execute.call_args[0][0]
        assert call_args.generate_allowlist is True

    @patch("mcp_coder.cli.main.execute_check_file_sizes")
    @patch(
        "sys.argv",
        ["mcp-coder", "check", "file-size", "--project-dir", "/some/path"],
    )
    def test_project_dir_argument_parsing(self, mock_execute: MagicMock) -> None:
        """Test that --project-dir argument is parsed correctly."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0

        main()

        call_args = mock_execute.call_args[0][0]
        assert call_args.project_dir == "/some/path"

    @patch("mcp_coder.cli.main.execute_check_file_sizes")
    @patch("sys.argv", ["mcp-coder", "check", "file-size"])
    def test_default_argument_values(self, mock_execute: MagicMock) -> None:
        """Test that default argument values are set correctly."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0

        main()

        call_args = mock_execute.call_args[0][0]
        assert call_args.max_lines == 600
        assert call_args.allowlist_file == ".large-files-allowlist"
        assert call_args.generate_allowlist is False
        assert call_args.project_dir is None
