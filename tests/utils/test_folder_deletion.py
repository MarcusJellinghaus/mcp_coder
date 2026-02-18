"""Tests for folder deletion utilities.

This module contains mock-based tests for safe folder deletion functionality,
ensuring reliable CI execution without actual file locking dependencies.
"""

import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mcp_coder.utils.folder_deletion import (
    DeletionFailureReason,
    DeletionResult,
    _cleanup_staging,
    _get_default_staging_dir,
    _move_to_staging,
    _rmtree_remove_readonly,
    _try_delete_empty_directory,
    is_directory_empty,
    safe_delete_folder,
)


class TestSafeDeleteFolder:
    """Tests for safe_delete_folder function."""

    def test_nonexistent_folder_returns_true(self, tmp_path: Path) -> None:
        """Test that deleting a non-existent folder returns True (idempotent)."""
        nonexistent = tmp_path / "does_not_exist"

        result = safe_delete_folder(nonexistent)

        assert result.success is True
        assert not nonexistent.exists()

    def test_empty_folder_deleted(self, tmp_path: Path) -> None:
        """Test that an empty folder is deleted successfully."""
        folder = tmp_path / "empty_folder"
        folder.mkdir()

        result = safe_delete_folder(folder)

        assert result.success is True
        assert not folder.exists()

    def test_folder_with_files_deleted(self, tmp_path: Path) -> None:
        """Test that a folder with files is deleted successfully."""
        folder = tmp_path / "folder_with_files"
        folder.mkdir()
        (folder / "file1.txt").write_text("content1")
        (folder / "file2.txt").write_text("content2")
        subfolder = folder / "subfolder"
        subfolder.mkdir()
        (subfolder / "nested.txt").write_text("nested content")

        result = safe_delete_folder(folder)

        assert result.success is True
        assert not folder.exists()

    def test_readonly_files_handled(self, tmp_path: Path) -> None:
        """Test that read-only files are handled correctly."""
        folder = tmp_path / "readonly_folder"
        folder.mkdir()
        readonly_file = folder / "readonly.txt"
        readonly_file.write_text("readonly content")

        # Make file read-only
        os.chmod(readonly_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        try:
            result = safe_delete_folder(folder)

            assert result.success is True
            assert not folder.exists()
        finally:
            # Cleanup in case test fails
            if readonly_file.exists():
                os.chmod(readonly_file, stat.S_IWUSR)

    def test_locked_file_moved_to_staging(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that locked files are moved to staging directory."""
        folder = tmp_path / "locked_folder"
        folder.mkdir()
        locked_file = folder / "locked.txt"
        locked_file.write_text("locked content")

        staging_dir = tmp_path / "staging"
        call_count = 0

        # Mock rmtree to fail on first call with PermissionError, succeed on second
        original_rmtree = shutil.rmtree

        def mock_rmtree(path: Any, **kwargs: Any) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                error = PermissionError("Access denied")
                error.filename = str(locked_file)
                raise error
            # On retry, the file should be gone (moved), so simulate empty folder
            if Path(path).exists():
                original_rmtree(path, **kwargs)

        monkeypatch.setattr(shutil, "rmtree", mock_rmtree)

        # Mock move to succeed and actually remove the file
        def mock_move(src: str, dst: str) -> str:
            # Actually delete the source to simulate move
            src_path = Path(src)
            if src_path.is_file():
                src_path.unlink()
            elif src_path.is_dir():
                original_rmtree(src_path)
            return dst

        monkeypatch.setattr(shutil, "move", mock_move)

        result = safe_delete_folder(folder, staging_dir=staging_dir)

        assert result.success is True

    def test_cleanup_staging_false_skips_cleanup(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that cleanup_staging=False skips staging cleanup."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        cleanup_called = False

        original_cleanup = _cleanup_staging

        def mock_cleanup(staging_dir: Path | None) -> tuple[int, int]:
            nonlocal cleanup_called
            cleanup_called = True
            return original_cleanup(staging_dir)

        monkeypatch.setattr(
            "mcp_coder.utils.folder_deletion._cleanup_staging", mock_cleanup
        )

        result = safe_delete_folder(folder, cleanup_staging=False)

        assert result.success is True
        assert cleanup_called is False

    def test_cleanup_staging_true_runs_cleanup(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that cleanup_staging=True runs staging cleanup."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        cleanup_called = False

        original_cleanup = _cleanup_staging

        def mock_cleanup(staging_dir: Path | None) -> tuple[int, int]:
            nonlocal cleanup_called
            cleanup_called = True
            return original_cleanup(staging_dir)

        monkeypatch.setattr(
            "mcp_coder.utils.folder_deletion._cleanup_staging", mock_cleanup
        )

        result = safe_delete_folder(folder, cleanup_staging=True)

        assert result.success is True
        assert cleanup_called is True

    def test_max_retries_exceeded_returns_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that exceeding MAX_RETRIES returns False."""
        folder = tmp_path / "persistent_folder"
        folder.mkdir()
        (folder / "file.txt").write_text("content")

        # Mock rmtree to always raise PermissionError
        def mock_rmtree(path: Any, **kwargs: Any) -> None:
            error = PermissionError("Access denied")
            error.filename = str(folder / "file.txt")
            raise error

        monkeypatch.setattr(shutil, "rmtree", mock_rmtree)

        # Mock move to always fail
        def mock_move(src: str, dst: str) -> str:
            raise PermissionError("Cannot move")

        monkeypatch.setattr(shutil, "move", mock_move)

        result = safe_delete_folder(folder, cleanup_staging=False)

        assert result.success is False
        assert result.reason == DeletionFailureReason.MAX_RETRIES
        assert folder.exists()

    def test_empty_locked_directory_handled(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that empty locked directories are handled correctly."""
        folder = tmp_path / "empty_locked"
        folder.mkdir()

        staging_dir = tmp_path / "staging"
        rmdir_attempts = 0

        def mock_rmdir(self: Path) -> None:
            nonlocal rmdir_attempts
            rmdir_attempts += 1
            raise PermissionError("Directory locked")

        monkeypatch.setattr(Path, "rmdir", mock_rmdir)

        # Mock move to succeed and remove the folder
        def mock_move(src: str, dst: str) -> str:
            Path(src).mkdir(parents=True, exist_ok=True)  # Ensure it exists
            # Create staging and pretend to move
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            # Actually delete source to simulate successful move
            Path(src).rmdir = lambda: None  # type: ignore[method-assign]
            shutil._rmtree_unsafe(Path(src), lambda *_: None)  # type: ignore[attr-defined]
            return dst

        # Simpler approach - just mark folder as moved
        def mock_move_simple(src: str, dst: str) -> str:
            # Mark folder as non-existent after move
            return dst

        monkeypatch.setattr(shutil, "move", mock_move_simple)

        # Mock exists to return False after move attempt
        exists_call_count = 0
        original_exists = Path.exists

        def mock_exists(self: Path) -> bool:
            nonlocal exists_call_count
            if self == folder:
                exists_call_count += 1
                # After move attempt (2nd call to exists), pretend it's gone
                if exists_call_count > 2:
                    return False
            return original_exists(self)

        monkeypatch.setattr(Path, "exists", mock_exists)

        result = safe_delete_folder(folder, staging_dir=staging_dir)

        assert result.success is True
        assert rmdir_attempts > 0  # Confirm rmdir was attempted

    def test_directory_becomes_empty_during_deletion(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test handling when directory becomes empty during deletion."""
        folder = tmp_path / "becomes_empty"
        folder.mkdir()
        (folder / "file.txt").write_text("content")

        call_count = 0
        original_rmtree = shutil.rmtree

        def mock_rmtree(path: Any, **kwargs: Any) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: raise error pointing to the folder itself
                # (simulates folder becoming empty during deletion)
                error = PermissionError("Access denied")
                error.filename = str(folder)
                raise error
            # Second call: succeed
            original_rmtree(path, **kwargs)

        monkeypatch.setattr(shutil, "rmtree", mock_rmtree)

        # Make is_directory_empty return True after first rmtree attempt
        empty_check_count = 0
        original_is_empty = is_directory_empty

        def mock_is_empty(path: Path) -> bool:
            nonlocal empty_check_count
            empty_check_count += 1
            if path == folder and empty_check_count > 1:
                return True
            return original_is_empty(path)

        monkeypatch.setattr(
            "mcp_coder.utils.folder_deletion.is_directory_empty", mock_is_empty
        )

        # Make _try_delete_empty_directory succeed
        def mock_try_delete_empty(path: Path, staging_dir: Path | None) -> bool:
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
            return True

        monkeypatch.setattr(
            "mcp_coder.utils.folder_deletion._try_delete_empty_directory",
            mock_try_delete_empty,
        )

        result = safe_delete_folder(folder, cleanup_staging=False)

        assert result.success is True

    def test_string_path_accepted(self, tmp_path: Path) -> None:
        """Test that string paths are accepted and converted."""
        folder = tmp_path / "string_path_folder"
        folder.mkdir()
        (folder / "file.txt").write_text("content")

        result = safe_delete_folder(str(folder))

        assert result.success is True
        assert not folder.exists()

    def test_custom_staging_dir(self, tmp_path: Path) -> None:
        """Test that custom staging directory is used."""
        folder = tmp_path / "folder"
        folder.mkdir()

        custom_staging = tmp_path / "custom_staging"

        result = safe_delete_folder(folder, staging_dir=custom_staging)

        assert result.success is True
        # Staging dir created only if needed (not for successful direct delete)

    def test_string_staging_dir_accepted(self, tmp_path: Path) -> None:
        """Test that string staging_dir is accepted and converted."""
        folder = tmp_path / "folder"
        folder.mkdir()

        custom_staging = tmp_path / "custom_staging"

        result = safe_delete_folder(folder, staging_dir=str(custom_staging))

        assert result.success is True


class TestMoveToStaging:
    """Tests for _move_to_staging function."""

    def test_moves_file_with_uuid_suffix(self, tmp_path: Path) -> None:
        """Test that files are moved with UUID suffix."""
        source_file = tmp_path / "test_file.txt"
        source_file.write_text("content")
        staging_dir = tmp_path / "staging"

        result = _move_to_staging(source_file, staging_dir)

        assert result is True
        assert not source_file.exists()
        assert staging_dir.exists()

        # Check that file was moved with UUID suffix
        moved_files = list(staging_dir.iterdir())
        assert len(moved_files) == 1
        assert moved_files[0].name.startswith("test_file_")
        assert moved_files[0].suffix == ".txt"
        assert len(moved_files[0].stem) == len("test_file_") + 8  # 8-char UUID

    def test_moves_directory_with_uuid_suffix(self, tmp_path: Path) -> None:
        """Test that directories are moved with UUID suffix."""
        source_dir = tmp_path / "test_dir"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("content")
        staging_dir = tmp_path / "staging"

        result = _move_to_staging(source_dir, staging_dir)

        assert result is True
        assert not source_dir.exists()
        assert staging_dir.exists()

        # Check that directory was moved with UUID suffix
        moved_items = list(staging_dir.iterdir())
        assert len(moved_items) == 1
        assert moved_items[0].name.startswith("test_dir_")
        assert moved_items[0].is_dir()

    def test_handles_move_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that move failures are handled gracefully."""
        source_file = tmp_path / "test_file.txt"
        source_file.write_text("content")
        staging_dir = tmp_path / "staging"

        def mock_move(src: str, dst: str) -> str:
            raise PermissionError("Cannot move")

        monkeypatch.setattr(shutil, "move", mock_move)

        result = _move_to_staging(source_file, staging_dir)

        assert result is False
        assert source_file.exists()  # File should still exist

    def test_uses_default_staging_when_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that default staging directory is used when None."""
        source_file = tmp_path / "test_file.txt"
        source_file.write_text("content")

        # Mock the default staging dir to use tmp_path
        default_staging = tmp_path / "default_staging"
        monkeypatch.setattr(
            "mcp_coder.utils.folder_deletion._get_default_staging_dir",
            lambda: default_staging,
        )

        result = _move_to_staging(source_file, None)

        assert result is True
        assert not source_file.exists()
        assert default_staging.exists()


class TestCleanupStaging:
    """Tests for _cleanup_staging function."""

    def test_deletes_unlocked_files(self, tmp_path: Path) -> None:
        """Test that unlocked files in staging are deleted."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        (staging_dir / "file1.txt").write_text("content1")
        (staging_dir / "file2.txt").write_text("content2")

        deleted, remaining = _cleanup_staging(staging_dir)

        assert deleted == 2
        assert remaining == 0
        assert not staging_dir.exists()  # Should be removed when empty

    def test_counts_remaining_locked_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that remaining locked files are counted."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        (staging_dir / "unlocked.txt").write_text("content1")
        locked_file = staging_dir / "locked.txt"
        locked_file.write_text("content2")

        # Mock unlink to fail for locked file
        original_unlink = Path.unlink

        def mock_unlink(self: Path, missing_ok: bool = False) -> None:
            if self.name == "locked.txt":
                raise PermissionError("File locked")
            original_unlink(self, missing_ok=missing_ok)

        monkeypatch.setattr(Path, "unlink", mock_unlink)

        deleted, remaining = _cleanup_staging(staging_dir)

        assert deleted == 1
        assert remaining == 1
        assert locked_file.exists()

    def test_removes_empty_staging_dir(self, tmp_path: Path) -> None:
        """Test that empty staging directory is removed."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        (staging_dir / "file.txt").write_text("content")

        deleted, remaining = _cleanup_staging(staging_dir)

        assert deleted == 1
        assert remaining == 0
        assert not staging_dir.exists()

    def test_nonexistent_staging_dir(self, tmp_path: Path) -> None:
        """Test handling of non-existent staging directory."""
        staging_dir = tmp_path / "nonexistent"

        deleted, remaining = _cleanup_staging(staging_dir)

        assert deleted == 0
        assert remaining == 0

    def test_deletes_directories_in_staging(self, tmp_path: Path) -> None:
        """Test that directories in staging are deleted."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        subdir = staging_dir / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("content")

        deleted, remaining = _cleanup_staging(staging_dir)

        assert deleted == 1
        assert remaining == 0
        assert not staging_dir.exists()

    def test_uses_default_staging_when_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that default staging directory is used when None."""
        default_staging = tmp_path / "default_staging"
        default_staging.mkdir()
        (default_staging / "file.txt").write_text("content")

        monkeypatch.setattr(
            "mcp_coder.utils.folder_deletion._get_default_staging_dir",
            lambda: default_staging,
        )

        deleted, remaining = _cleanup_staging(None)

        assert deleted == 1
        assert remaining == 0


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_default_staging_dir(self) -> None:
        """Test _get_default_staging_dir returns expected path."""
        result = _get_default_staging_dir()

        assert result.name == "safe_delete_staging"
        assert result.parent == Path(tempfile.gettempdir())

    def test_is_directory_empty_true(self, tmp_path: Path) -> None:
        """Test is_directory_empty returns True for empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = is_directory_empty(empty_dir)

        assert result is True

    def test_is_directory_empty_false(self, tmp_path: Path) -> None:
        """Test is_directory_empty returns False for non-empty directory."""
        non_empty_dir = tmp_path / "non_empty"
        non_empty_dir.mkdir()
        (non_empty_dir / "file.txt").write_text("content")

        result = is_directory_empty(non_empty_dir)

        assert result is False

    def test_is_directory_empty_permission_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test is_directory_empty returns False on permission error."""
        dir_path = tmp_path / "locked"
        dir_path.mkdir()

        def mock_iterdir(self: Path) -> Any:
            raise PermissionError("Access denied")

        monkeypatch.setattr(Path, "iterdir", mock_iterdir)

        result = is_directory_empty(dir_path)

        assert result is False

    def test_rmtree_remove_readonly(self, tmp_path: Path) -> None:
        """Test _rmtree_remove_readonly removes readonly flag and calls func."""
        readonly_file = tmp_path / "readonly.txt"
        readonly_file.write_text("content")
        os.chmod(readonly_file, stat.S_IRUSR)

        mock_func = Mock()

        _rmtree_remove_readonly(mock_func, str(readonly_file), None)

        mock_func.assert_called_once_with(str(readonly_file))
        # File should now be writable
        assert os.access(readonly_file, os.W_OK)

    def test_try_delete_empty_directory_success(self, tmp_path: Path) -> None:
        """Test _try_delete_empty_directory succeeds for unlocked directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = _try_delete_empty_directory(empty_dir, None)

        assert result is True
        assert not empty_dir.exists()

    def test_try_delete_empty_directory_locked_moves_to_staging(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _try_delete_empty_directory moves locked directory to staging."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        staging_dir = tmp_path / "staging"

        # Mock rmdir to fail
        def mock_rmdir(self: Path) -> None:
            raise PermissionError("Directory locked")

        monkeypatch.setattr(Path, "rmdir", mock_rmdir)
        monkeypatch.setattr(
            "mcp_coder.utils.folder_deletion.time.sleep", lambda _: None
        )

        result = _try_delete_empty_directory(empty_dir, staging_dir)

        assert result is True
        assert not empty_dir.exists()
        assert staging_dir.exists()

    def test_try_delete_empty_directory_all_fail(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _try_delete_empty_directory returns False when all methods fail."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        staging_dir = tmp_path / "staging"

        # Mock rmdir to fail
        def mock_rmdir(self: Path) -> None:
            raise PermissionError("Directory locked")

        monkeypatch.setattr(Path, "rmdir", mock_rmdir)
        monkeypatch.setattr(
            "mcp_coder.utils.folder_deletion.time.sleep", lambda _: None
        )

        # Mock move to fail
        def mock_move(src: str, dst: str) -> str:
            raise PermissionError("Cannot move")

        monkeypatch.setattr(shutil, "move", mock_move)

        result = _try_delete_empty_directory(empty_dir, staging_dir)

        assert result is False
        assert empty_dir.exists()

    def test_try_delete_empty_directory_retries_rmdir_before_staging(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test rmdir is retried 3 times before _move_to_staging is attempted."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        staging_dir = tmp_path / "staging"

        rmdir_call_count = 0

        def mock_rmdir(self: Path) -> None:
            nonlocal rmdir_call_count
            rmdir_call_count += 1
            raise PermissionError("Directory locked")

        monkeypatch.setattr(Path, "rmdir", mock_rmdir)
        monkeypatch.setattr(
            "mcp_coder.utils.folder_deletion.time.sleep", lambda _: None
        )

        move_to_staging_called = False

        def mock_move_to_staging(path: Path, _staging: Path | None) -> bool:
            nonlocal move_to_staging_called
            move_to_staging_called = True
            return True

        monkeypatch.setattr(
            "mcp_coder.utils.folder_deletion._move_to_staging", mock_move_to_staging
        )

        result = _try_delete_empty_directory(empty_dir, staging_dir)

        assert rmdir_call_count == 3
        assert result is True

    def test_try_delete_empty_directory_succeeds_on_second_attempt(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test early exit when rmdir succeeds on the second attempt."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        staging_dir = tmp_path / "staging"

        rmdir_call_count = 0
        original_rmdir = Path.rmdir

        def mock_rmdir(self: Path) -> None:
            nonlocal rmdir_call_count
            rmdir_call_count += 1
            if rmdir_call_count == 1:
                raise PermissionError("Directory locked")
            original_rmdir(self)

        monkeypatch.setattr(Path, "rmdir", mock_rmdir)
        monkeypatch.setattr(
            "mcp_coder.utils.folder_deletion.time.sleep", lambda _: None
        )

        move_to_staging_called = False

        def mock_move_to_staging(path: Path, _staging: Path | None) -> bool:
            nonlocal move_to_staging_called
            move_to_staging_called = True
            return True

        monkeypatch.setattr(
            "mcp_coder.utils.folder_deletion._move_to_staging", mock_move_to_staging
        )

        result = _try_delete_empty_directory(empty_dir, staging_dir)

        assert result is True
        assert move_to_staging_called is False

    def test_try_delete_empty_directory_sleep_called_between_retries(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test time.sleep(1) is called between retry attempts."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        staging_dir = tmp_path / "staging"

        def mock_rmdir(self: Path) -> None:
            raise PermissionError("Directory locked")

        monkeypatch.setattr(Path, "rmdir", mock_rmdir)

        sleep_calls: list[int | float] = []

        def mock_sleep(seconds: int | float) -> None:
            sleep_calls.append(seconds)

        monkeypatch.setattr("mcp_coder.utils.folder_deletion.time.sleep", mock_sleep)

        monkeypatch.setattr(
            "mcp_coder.utils.folder_deletion._move_to_staging",
            lambda path, _staging: True,
        )

        _try_delete_empty_directory(empty_dir, staging_dir)

        assert len(sleep_calls) == 2
        assert all(s == 1 for s in sleep_calls)
