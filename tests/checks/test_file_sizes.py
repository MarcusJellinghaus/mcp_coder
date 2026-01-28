"""Tests for mcp_coder.checks.file_sizes module."""

from pathlib import Path

import pytest

from mcp_coder.checks.file_sizes import count_lines


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
