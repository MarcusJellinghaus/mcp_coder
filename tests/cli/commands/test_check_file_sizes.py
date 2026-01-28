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


class TestCheckFileSizesEndToEnd:
    """End-to-end integration tests without mocking core logic.

    These tests create actual files and run the full command flow.
    """

    def test_passes_when_all_files_under_limit(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that command passes when all files are under the line limit."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Create a small Python file (under 600 lines)
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        small_file = src_dir / "small.py"
        small_file.write_text("# Small file\n" * 50)  # 50 lines

        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=600,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )

        result = execute_check_file_sizes(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "PASSED" in captured.out or "passed" in captured.out.lower()

    def test_fails_when_file_exceeds_limit(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that command fails when a file exceeds the line limit."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Create a large Python file (over 100 lines with max_lines=100)
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        large_file = src_dir / "large.py"
        large_file.write_text("# Line\n" * 150)  # 150 lines

        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=100,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )

        result = execute_check_file_sizes(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "large.py" in captured.out

    def test_allowlist_skips_specified_files(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that allowlisted files are skipped from violation reporting."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Create a large file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        large_file = src_dir / "large.py"
        large_file.write_text("# Line\n" * 150)  # 150 lines

        # Create allowlist file
        allowlist_file = tmp_path / ".large-files-allowlist"
        allowlist_file.write_text("src/large.py\n")

        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=100,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )

        result = execute_check_file_sizes(args)

        assert result == 0  # Should pass because the large file is allowlisted
        captured = capsys.readouterr()
        # Output should mention allowlisted file
        assert "allowlist" in captured.out.lower() or "PASSED" in captured.out

    def test_generate_allowlist_outputs_violation_paths(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that --generate-allowlist outputs paths of violating files."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Create multiple large files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "big1.py").write_text("# Line\n" * 150)
        (src_dir / "big2.py").write_text("# Line\n" * 200)
        (src_dir / "small.py").write_text("# Line\n" * 50)  # Under limit

        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=100,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=True,
        )

        result = execute_check_file_sizes(args)

        assert result == 1  # Violations exist
        captured = capsys.readouterr()
        # Should output paths in allowlist format
        assert "big1.py" in captured.out
        assert "big2.py" in captured.out
        # Small file should NOT be in output (it's under limit)
        assert "small.py" not in captured.out

    def test_custom_max_lines_threshold(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that custom --max-lines threshold is respected."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Create a file with 75 lines
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        medium_file = src_dir / "medium.py"
        medium_file.write_text("# Line\n" * 75)

        # With max_lines=100, should pass
        args_pass = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=100,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )
        result_pass = execute_check_file_sizes(args_pass)
        assert result_pass == 0

        # With max_lines=50, should fail
        args_fail = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=50,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )
        result_fail = execute_check_file_sizes(args_fail)
        assert result_fail == 1

    def test_custom_allowlist_filename(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that custom --allowlist-file is used."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Create a large file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        large_file = src_dir / "large.py"
        large_file.write_text("# Line\n" * 150)

        # Create custom allowlist file
        custom_allowlist = tmp_path / "my-custom-allowlist.txt"
        custom_allowlist.write_text("src/large.py\n")

        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=100,
            allowlist_file="my-custom-allowlist.txt",
            generate_allowlist=False,
        )

        result = execute_check_file_sizes(args)

        assert result == 0  # Should pass with custom allowlist

    def test_empty_project_passes(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that an empty project (no Python files) passes."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Don't create any files, just an empty src directory
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=600,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )

        result = execute_check_file_sizes(args)

        assert result == 0

    def test_multiple_directories_scanned(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that files in src/ and tests/ are both scanned."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Create files in both src/ and tests/
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "module.py").write_text("# Small\n" * 10)

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        large_test = tests_dir / "test_large.py"
        large_test.write_text("# Line\n" * 150)

        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=100,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )

        result = execute_check_file_sizes(args)

        assert result == 1  # Should fail due to large test file
        captured = capsys.readouterr()
        assert "test_large.py" in captured.out

    def test_stale_allowlist_entries_reported(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that stale allowlist entries are reported in output."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Create only a small file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "small.py").write_text("# Small\n" * 10)

        # Create allowlist with non-existent file
        allowlist_file = tmp_path / ".large-files-allowlist"
        allowlist_file.write_text("src/nonexistent.py\n")

        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=100,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )

        result = execute_check_file_sizes(args)

        # Should still pass (no violations)
        assert result == 0
        captured = capsys.readouterr()
        # Output should mention stale entry
        assert "stale" in captured.out.lower() or "nonexistent" in captured.out

    def test_output_format_shows_line_counts(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that output includes line counts for violations."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Create a file with exactly 150 lines
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        large_file = src_dir / "large.py"
        large_file.write_text("# Line\n" * 150)

        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=100,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=False,
        )

        result = execute_check_file_sizes(args)

        assert result == 1
        captured = capsys.readouterr()
        # Output should show the line count (150)
        assert "150" in captured.out

    def test_generate_allowlist_with_no_violations(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test --generate-allowlist with no violations produces no output."""
        from mcp_coder.cli.commands.check_file_sizes import execute_check_file_sizes

        # Create only small files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "small.py").write_text("# Small\n" * 10)

        args = argparse.Namespace(
            project_dir=str(tmp_path),
            max_lines=100,
            allowlist_file=".large-files-allowlist",
            generate_allowlist=True,
        )

        result = execute_check_file_sizes(args)

        assert result == 0  # No violations
        captured = capsys.readouterr()
        # Output should be empty or minimal (no paths to allowlist)
        assert "small.py" not in captured.out
