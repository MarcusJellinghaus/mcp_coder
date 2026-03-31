"""Tests for soft-delete file I/O helpers."""

from pathlib import Path

from mcp_coder.workflows.vscodeclaude.helpers import (
    TO_BE_DELETED_FILENAME,
    add_to_be_deleted,
    load_to_be_deleted,
    remove_from_to_be_deleted,
)


class TestLoadToBeDeleted:
    """Tests for load_to_be_deleted."""

    def test_load_empty_when_file_missing(self, tmp_path: Path) -> None:
        """Returns empty set when .to_be_deleted file does not exist."""
        result = load_to_be_deleted(str(tmp_path))
        assert result == set()

    def test_load_returns_folder_names(self, tmp_path: Path) -> None:
        """Reads file with 2 entries and returns set of 2."""
        registry = tmp_path / TO_BE_DELETED_FILENAME
        registry.write_text("mcp-coder_123\nmcp-coder_456\n")
        result = load_to_be_deleted(str(tmp_path))
        assert result == {"mcp-coder_123", "mcp-coder_456"}

    def test_load_ignores_blank_lines(self, tmp_path: Path) -> None:
        """File with blank lines returns only non-blank entries."""
        registry = tmp_path / TO_BE_DELETED_FILENAME
        registry.write_text("mcp-coder_123\n\n\nmcp-coder_456\n\n")
        result = load_to_be_deleted(str(tmp_path))
        assert result == {"mcp-coder_123", "mcp-coder_456"}


class TestAddToBeDeleted:
    """Tests for add_to_be_deleted."""

    def test_add_creates_file_if_missing(self, tmp_path: Path) -> None:
        """File is created with the entry when it doesn't exist."""
        add_to_be_deleted(str(tmp_path), "mcp-coder_123")
        registry = tmp_path / TO_BE_DELETED_FILENAME
        assert registry.exists()
        assert registry.read_text() == "mcp-coder_123\n"

    def test_add_appends_to_existing(self, tmp_path: Path) -> None:
        """Second entry is appended to existing file."""
        add_to_be_deleted(str(tmp_path), "mcp-coder_123")
        add_to_be_deleted(str(tmp_path), "mcp-coder_456")
        registry = tmp_path / TO_BE_DELETED_FILENAME
        content = registry.read_text()
        assert "mcp-coder_123\n" in content
        assert "mcp-coder_456\n" in content

    def test_add_idempotent(self, tmp_path: Path) -> None:
        """Adding the same name twice results in file having it once."""
        add_to_be_deleted(str(tmp_path), "mcp-coder_123")
        add_to_be_deleted(str(tmp_path), "mcp-coder_123")
        registry = tmp_path / TO_BE_DELETED_FILENAME
        lines = [line for line in registry.read_text().splitlines() if line.strip()]
        assert lines.count("mcp-coder_123") == 1


class TestRemoveFromToBeDeleted:
    """Tests for remove_from_to_be_deleted."""

    def test_remove_entry(self, tmp_path: Path) -> None:
        """Removes one of two entries, other remains."""
        registry = tmp_path / TO_BE_DELETED_FILENAME
        registry.write_text("mcp-coder_123\nmcp-coder_456\n")
        remove_from_to_be_deleted(str(tmp_path), "mcp-coder_123")
        content = registry.read_text()
        assert "mcp-coder_123" not in content
        assert "mcp-coder_456" in content

    def test_remove_last_entry_deletes_file(self, tmp_path: Path) -> None:
        """File is deleted when last entry is removed."""
        registry = tmp_path / TO_BE_DELETED_FILENAME
        registry.write_text("mcp-coder_123\n")
        remove_from_to_be_deleted(str(tmp_path), "mcp-coder_123")
        assert not registry.exists()

    def test_remove_nonexistent_entry_no_error(self, tmp_path: Path) -> None:
        """No-op when entry is not in file."""
        registry = tmp_path / TO_BE_DELETED_FILENAME
        registry.write_text("mcp-coder_123\n")
        remove_from_to_be_deleted(str(tmp_path), "mcp-coder_999")
        assert registry.read_text() == "mcp-coder_123\n"

    def test_remove_when_file_missing_no_error(self, tmp_path: Path) -> None:
        """No-op when .to_be_deleted file doesn't exist."""
        remove_from_to_be_deleted(str(tmp_path), "mcp-coder_123")
        registry = tmp_path / TO_BE_DELETED_FILENAME
        assert not registry.exists()
