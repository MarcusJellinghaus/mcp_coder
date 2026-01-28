"""Tests for mcp_coder.checks.file_sizes module."""

from pathlib import Path

import pytest

from mcp_coder.checks.file_sizes import count_lines, load_allowlist


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
