"""Tests for mcp_coder.checks.file_sizes module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.checks.file_sizes import (
    CheckResult,
    FileMetrics,
    check_file_sizes,
    count_lines,
    get_file_metrics,
    load_allowlist,
    render_output,
)


class TestCountLines:
    """Tests for count_lines() function."""

    def test_count_lines_normal_file(self, tmp_path: Path) -> None:
        """Test counting lines in a normal text file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")

        result = count_lines(test_file)

        assert result == 3

    def test_count_lines_empty_file(self, tmp_path: Path) -> None:
        """Test counting lines in empty file returns 0."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("", encoding="utf-8")

        result = count_lines(test_file)

        assert result == 0

    def test_count_lines_binary_file(self, tmp_path: Path) -> None:
        """Test binary file returns -1."""
        test_file = tmp_path / "binary.bin"
        # Write binary content that cannot be decoded as UTF-8
        test_file.write_bytes(b"\x80\x81\x82\x83\x84\x85")

        result = count_lines(test_file)

        assert result == -1

    def test_count_lines_file_without_trailing_newline(self, tmp_path: Path) -> None:
        """Test counting lines in file without trailing newline."""
        test_file = tmp_path / "no_newline.txt"
        test_file.write_text("line 1\nline 2", encoding="utf-8")

        result = count_lines(test_file)

        assert result == 2

    def test_count_lines_single_line(self, tmp_path: Path) -> None:
        """Test counting lines in single line file."""
        test_file = tmp_path / "single.txt"
        test_file.write_text("single line\n", encoding="utf-8")

        result = count_lines(test_file)

        assert result == 1

    def test_count_lines_unicode_content(self, tmp_path: Path) -> None:
        """Test counting lines with unicode content."""
        test_file = tmp_path / "unicode.txt"
        test_file.write_text(
            "Hello\nWorld\n\u4e2d\u6587\n\u65e5\u672c\u8a9e\n", encoding="utf-8"
        )

        result = count_lines(test_file)

        assert result == 4


class TestLoadAllowlist:
    """Tests for load_allowlist() function."""

    def test_load_allowlist_with_comments(self, tmp_path: Path) -> None:
        """Test that # comments are ignored."""
        allowlist_file = tmp_path / "allowlist.txt"
        allowlist_file.write_text(
            "# This is a comment\n"
            "src/module/file1.py\n"
            "# Another comment\n"
            "src/module/file2.py\n",
            encoding="utf-8",
        )

        result = load_allowlist(allowlist_file)

        assert "src/module/file1.py" in result or "src\\module\\file1.py" in result
        assert "src/module/file2.py" in result or "src\\module\\file2.py" in result
        assert len(result) == 2
        # Comments should not be in the result
        for entry in result:
            assert not entry.startswith("#")

    def test_load_allowlist_blank_lines(self, tmp_path: Path) -> None:
        """Test that blank lines are ignored."""
        allowlist_file = tmp_path / "allowlist.txt"
        allowlist_file.write_text(
            "src/file1.py\n" "\n" "   \n" "src/file2.py\n" "\n",
            encoding="utf-8",
        )

        result = load_allowlist(allowlist_file)

        assert len(result) == 2
        # Empty strings should not be in the result
        assert "" not in result
        assert "   " not in result

    def test_load_allowlist_path_normalization(self, tmp_path: Path) -> None:
        """Test path separator normalization to OS-native format."""
        import os

        allowlist_file = tmp_path / "allowlist.txt"
        # Write paths with forward slashes (cross-platform format)
        allowlist_file.write_text(
            "src/module/file1.py\n" "tests/unit/test_file.py\n",
            encoding="utf-8",
        )

        result = load_allowlist(allowlist_file)

        # Paths should be normalized to OS-native format
        if os.sep == "\\":
            # Windows
            assert "src\\module\\file1.py" in result
            assert "tests\\unit\\test_file.py" in result
        else:
            # Unix
            assert "src/module/file1.py" in result
            assert "tests/unit/test_file.py" in result

    def test_load_allowlist_missing_file(self, tmp_path: Path) -> None:
        """Test missing file returns empty set."""
        allowlist_file = tmp_path / "nonexistent.txt"

        result = load_allowlist(allowlist_file)

        assert result == set()

    def test_load_allowlist_strips_whitespace(self, tmp_path: Path) -> None:
        """Test that leading and trailing whitespace is stripped."""
        allowlist_file = tmp_path / "allowlist.txt"
        allowlist_file.write_text(
            "  src/file1.py  \n" "\tsrc/file2.py\t\n",
            encoding="utf-8",
        )

        result = load_allowlist(allowlist_file)

        # Check that paths are present without leading/trailing whitespace
        assert len(result) == 2
        for entry in result:
            assert entry == entry.strip()


class TestGetFileMetrics:
    """Tests for get_file_metrics() function."""

    def test_get_file_metrics_multiple_files(self, tmp_path: Path) -> None:
        """Test getting metrics for multiple files."""
        # Create test files with known line counts
        file1 = tmp_path / "file1.py"
        file1.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")

        file2 = tmp_path / "file2.py"
        file2.write_text("line 1\nline 2\n", encoding="utf-8")

        file3 = tmp_path / "file3.py"
        file3.write_text("single line\n", encoding="utf-8")

        files = [Path("file1.py"), Path("file2.py"), Path("file3.py")]

        result = get_file_metrics(files, tmp_path)

        assert len(result) == 3
        # Convert to dict for easier assertion
        metrics_by_name = {m.path.name: m.line_count for m in result}
        assert metrics_by_name["file1.py"] == 3
        assert metrics_by_name["file2.py"] == 2
        assert metrics_by_name["file3.py"] == 1

    def test_get_file_metrics_skips_binary(self, tmp_path: Path) -> None:
        """Test that binary files are excluded from results."""
        # Create a text file
        text_file = tmp_path / "text.py"
        text_file.write_text("line 1\nline 2\n", encoding="utf-8")

        # Create a binary file
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b"\x80\x81\x82\x83\x84\x85")

        files = [Path("text.py"), Path("binary.bin")]

        result = get_file_metrics(files, tmp_path)

        # Only text file should be in results
        assert len(result) == 1
        assert result[0].path.name == "text.py"
        assert result[0].line_count == 2

    def test_get_file_metrics_empty_list(self, tmp_path: Path) -> None:
        """Test getting metrics for empty file list."""
        result = get_file_metrics([], tmp_path)

        assert result == []

    def test_get_file_metrics_returns_file_metrics_objects(
        self, tmp_path: Path
    ) -> None:
        """Test that results are FileMetrics objects with correct types."""
        test_file = tmp_path / "test.py"
        test_file.write_text("line 1\n", encoding="utf-8")

        files = [Path("test.py")]

        result = get_file_metrics(files, tmp_path)

        assert len(result) == 1
        assert isinstance(result[0], FileMetrics)
        assert isinstance(result[0].path, Path)
        assert isinstance(result[0].line_count, int)


class TestCheckFileSizes:
    """Tests for check_file_sizes() function."""

    def test_check_file_sizes_all_pass(self, tmp_path: Path) -> None:
        """Test when all files are under limit."""
        # Create test files under the limit (10 lines)
        file1 = tmp_path / "file1.py"
        file1.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")

        file2 = tmp_path / "file2.py"
        file2.write_text("line 1\nline 2\n", encoding="utf-8")

        # Mock list_files to return our test files
        with patch("mcp_coder.checks.file_sizes.list_files") as mock_list_files:
            mock_list_files.return_value = ["file1.py", "file2.py"]

            result = check_file_sizes(
                project_dir=tmp_path,
                max_lines=10,
                allowlist=set(),
            )

        assert result.passed is True
        assert result.violations == []
        assert result.total_files_checked == 2
        assert result.allowlisted_count == 0
        assert result.stale_entries == []

    def test_check_file_sizes_with_violations(self, tmp_path: Path) -> None:
        """Test detecting files over limit."""
        # Create a file over the limit (3 lines limit)
        large_file = tmp_path / "large.py"
        large_file.write_text(
            "line 1\nline 2\nline 3\nline 4\nline 5\n", encoding="utf-8"
        )

        small_file = tmp_path / "small.py"
        small_file.write_text("line 1\n", encoding="utf-8")

        with patch("mcp_coder.checks.file_sizes.list_files") as mock_list_files:
            mock_list_files.return_value = ["large.py", "small.py"]

            result = check_file_sizes(
                project_dir=tmp_path,
                max_lines=3,
                allowlist=set(),
            )

        assert result.passed is False
        assert len(result.violations) == 1
        assert result.violations[0].path == Path("large.py")
        assert result.violations[0].line_count == 5
        assert result.total_files_checked == 2
        assert result.allowlisted_count == 0

    def test_check_file_sizes_with_allowlist(self, tmp_path: Path) -> None:
        """Test that allowlisted files don't cause failure."""
        # Create files over the limit
        large_file = tmp_path / "large.py"
        large_file.write_text(
            "line 1\nline 2\nline 3\nline 4\nline 5\n", encoding="utf-8"
        )

        # Normalize path for OS
        allowlisted_path = "large.py".replace("/", os.sep)

        with patch("mcp_coder.checks.file_sizes.list_files") as mock_list_files:
            mock_list_files.return_value = ["large.py"]

            result = check_file_sizes(
                project_dir=tmp_path,
                max_lines=3,
                allowlist={allowlisted_path},
            )

        assert result.passed is True
        assert result.violations == []
        assert result.total_files_checked == 1
        assert result.allowlisted_count == 1

    def test_check_file_sizes_stale_allowlist_missing_file(
        self, tmp_path: Path
    ) -> None:
        """Test detecting allowlist entry for non-existent file."""
        # Create a small file
        small_file = tmp_path / "small.py"
        small_file.write_text("line 1\n", encoding="utf-8")

        # Allowlist contains a file that doesn't exist
        stale_path = "nonexistent.py".replace("/", os.sep)

        with patch("mcp_coder.checks.file_sizes.list_files") as mock_list_files:
            mock_list_files.return_value = ["small.py"]

            result = check_file_sizes(
                project_dir=tmp_path,
                max_lines=10,
                allowlist={stale_path},
            )

        assert result.passed is True
        assert stale_path in result.stale_entries

    def test_check_file_sizes_stale_allowlist_under_limit(self, tmp_path: Path) -> None:
        """Test detecting allowlist entry for file now under limit."""
        # Create a file that's under the limit but in the allowlist
        under_limit_file = tmp_path / "was_large.py"
        under_limit_file.write_text("line 1\nline 2\n", encoding="utf-8")

        # This file is allowlisted but no longer over the limit
        allowlisted_path = "was_large.py".replace("/", os.sep)

        with patch("mcp_coder.checks.file_sizes.list_files") as mock_list_files:
            mock_list_files.return_value = ["was_large.py"]

            result = check_file_sizes(
                project_dir=tmp_path,
                max_lines=10,
                allowlist={allowlisted_path},
            )

        assert result.passed is True
        # The file is under limit, so allowlist entry is stale
        assert allowlisted_path in result.stale_entries

    def test_check_file_sizes_violations_sorted_descending(
        self, tmp_path: Path
    ) -> None:
        """Test violations are sorted by line count descending."""
        # Create files of varying sizes, all over the limit (5 lines)
        file_10_lines = tmp_path / "file_10.py"
        file_10_lines.write_text(
            "\n".join([f"line {i}" for i in range(10)]) + "\n", encoding="utf-8"
        )

        file_20_lines = tmp_path / "file_20.py"
        file_20_lines.write_text(
            "\n".join([f"line {i}" for i in range(20)]) + "\n", encoding="utf-8"
        )

        file_15_lines = tmp_path / "file_15.py"
        file_15_lines.write_text(
            "\n".join([f"line {i}" for i in range(15)]) + "\n", encoding="utf-8"
        )

        with patch("mcp_coder.checks.file_sizes.list_files") as mock_list_files:
            mock_list_files.return_value = ["file_10.py", "file_20.py", "file_15.py"]

            result = check_file_sizes(
                project_dir=tmp_path,
                max_lines=5,
                allowlist=set(),
            )

        assert result.passed is False
        assert len(result.violations) == 3
        # Should be sorted descending by line count
        assert result.violations[0].line_count == 20
        assert result.violations[1].line_count == 15
        assert result.violations[2].line_count == 10


class TestRenderOutput:
    """Tests for render_output() function."""

    def test_render_output_success(self) -> None:
        """Test success message format."""
        result = CheckResult(
            passed=True,
            violations=[],
            total_files_checked=10,
            allowlisted_count=2,
            stale_entries=[],
        )

        output = render_output(result, max_lines=500)

        assert "passed" in output.lower() or "success" in output.lower()
        assert "10" in output  # total files checked
        assert "2" in output  # allowlisted count

    def test_render_output_success_with_stale(self) -> None:
        """Test success message includes stale allowlist info."""
        result = CheckResult(
            passed=True,
            violations=[],
            total_files_checked=5,
            allowlisted_count=1,
            stale_entries=["old/file.py", "removed/module.py"],
        )

        output = render_output(result, max_lines=500)

        assert "passed" in output.lower() or "success" in output.lower()
        # Should mention stale entries
        assert "stale" in output.lower() or "old/file.py" in output
        assert "old/file.py" in output or "2" in output  # either path or count

    def test_render_output_failure(self) -> None:
        """Test failure message format with violations listed."""
        violations = [
            FileMetrics(path=Path("src/large_file.py"), line_count=750),
            FileMetrics(path=Path("src/another_big.py"), line_count=600),
        ]
        result = CheckResult(
            passed=False,
            violations=violations,
            total_files_checked=20,
            allowlisted_count=0,
            stale_entries=[],
        )

        output = render_output(result, max_lines=500)

        # Should indicate failure
        assert "fail" in output.lower() or "violation" in output.lower()
        # Should list the violations
        assert "large_file.py" in output
        assert "another_big.py" in output
        # Should show line counts
        assert "750" in output
        assert "600" in output

    def test_render_output_failure_shows_max_lines(self) -> None:
        """Test failure message mentions the max lines threshold."""
        violations = [
            FileMetrics(path=Path("src/big.py"), line_count=600),
        ]
        result = CheckResult(
            passed=False,
            violations=violations,
            total_files_checked=10,
            allowlisted_count=0,
            stale_entries=[],
        )

        output = render_output(result, max_lines=500)

        # Should mention the max lines threshold
        assert "500" in output

    def test_render_output_success_no_allowlisted(self) -> None:
        """Test success message when no files are allowlisted."""
        result = CheckResult(
            passed=True,
            violations=[],
            total_files_checked=15,
            allowlisted_count=0,
            stale_entries=[],
        )

        output = render_output(result, max_lines=500)

        assert "passed" in output.lower() or "success" in output.lower()
        assert "15" in output  # total files checked
