"""Folder deletion utilities with safe handling of locked files.

This module provides utilities for safely deleting folders on Windows,
handling locked files by moving them to a staging directory for later cleanup.

Key Features:
    - Handles locked files via staging directory strategy
    - Handles empty locked directories (Windows-specific)
    - Handles read-only files
    - Configurable staging cleanup
    - Python 3.12+ compatible
"""

import logging
import os
import shutil
import stat
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Callable, Union

logger = logging.getLogger(__name__)

# Internal constant - not exposed to callers
MAX_RETRIES = 50


def _get_default_staging_dir() -> Path:
    """Return default staging directory path (%TEMP%/safe_delete_staging).

    This uses the same staging directory as the CLI tool (tools/safe_delete_folder.py)
    so that both tools share cleanup - files from either get cleaned by either.

    Returns:
        Path to the default staging directory.
    """
    return Path(tempfile.gettempdir()) / "safe_delete_staging"


def _rmtree_remove_readonly(func: Callable[..., None], path: str, exc: object) -> None:
    """Error handler for shutil.rmtree to handle readonly files.

    This callback is used with shutil.rmtree's onerror/onexc parameter
    to automatically remove the read-only attribute and retry deletion.

    Args:
        func: The function that raised the exception (e.g., os.remove).
        path: The path that caused the exception.
        exc: The exception information (varies by Python version).
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _is_directory_empty(path: Path) -> bool:
    """Check if a directory is empty.

    Args:
        path: Path to the directory to check.

    Returns:
        True if the directory is empty, False otherwise or on error.
    """
    try:
        return not any(path.iterdir())
    except (PermissionError, OSError):
        return False


def _move_to_staging(item_path: Path, staging_dir: Path | None) -> bool:
    """Move file or directory to staging with UUID suffix.

    The item is renamed with a UUID suffix to avoid collisions in the staging
    directory. Format: {stem}_{uuid8}.{suffix}

    Args:
        item_path: Path to the file or directory to move.
        staging_dir: Staging directory path. Uses default if None.

    Returns:
        True if the move succeeded, False otherwise.
    """
    if staging_dir is None:
        staging_dir = _get_default_staging_dir()

    unique_name = f"{item_path.stem}_{uuid.uuid4().hex[:8]}{item_path.suffix}"
    staging_dest = staging_dir / unique_name

    try:
        staging_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(item_path), str(staging_dest))
        logger.debug("Moved locked item to staging: %s -> %s", item_path, staging_dest)
        return True
    except (PermissionError, OSError) as e:
        logger.debug("Failed to move item to staging: %s - %s", item_path, e)
        return False


def _cleanup_staging(staging_dir: Path | None) -> tuple[int, int]:
    """Clean up old items from staging directory.

    Attempts to delete all items in the staging directory. Items that are
    still locked by other processes will remain for future cleanup attempts.

    Args:
        staging_dir: Staging directory path. Uses default if None.

    Returns:
        Tuple of (deleted_count, remaining_count).
    """
    if staging_dir is None:
        staging_dir = _get_default_staging_dir()

    if not staging_dir.exists():
        return 0, 0

    deleted = 0
    remaining = 0

    for item in staging_dir.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            deleted += 1
            logger.debug("Cleaned up staging item: %s", item)
        except (PermissionError, OSError):
            remaining += 1
            logger.debug("Staging item still locked: %s", item)

    # Try to remove the staging dir itself if empty
    try:
        if staging_dir.exists() and not any(staging_dir.iterdir()):
            staging_dir.rmdir()
            logger.debug("Removed empty staging directory: %s", staging_dir)
    except (PermissionError, OSError):
        pass

    return deleted, remaining


def _try_delete_empty_directory(path: Path, staging_dir: Path | None) -> bool:
    """Try to delete an empty directory, moving to staging if locked.

    Empty directories on Windows can be locked at the directory level
    (not file level) and require special handling.

    Args:
        path: Path to the empty directory.
        staging_dir: Staging directory path for locked items.

    Returns:
        True if the directory was deleted or moved, False otherwise.
    """
    # First attempt: simple rmdir
    try:
        path.rmdir()
        if not path.exists():
            logger.debug("Deleted empty directory: %s", path)
            return True
    except (PermissionError, OSError):
        pass  # Expected if locked

    # Directory is locked - try moving to staging
    if _move_to_staging(path, staging_dir):
        logger.debug("Moved locked empty directory to staging: %s", path)
        return True

    logger.debug("Cannot delete or move empty locked directory: %s", path)
    return False


def _try_rmtree(path: Path) -> bool:
    """Try to delete a directory tree using shutil.rmtree.

    Handles Python version differences for the error handler callback.

    Args:
        path: Path to the directory to delete.

    Returns:
        True if deletion succeeded, False otherwise.

    Raises:
        PermissionError: If a file is locked.
        OSError: If another OS error occurs.
    """
    # Use kwargs to avoid pylint E1123 on Python <3.12 (onexc was added in 3.12)
    if sys.version_info >= (3, 12):
        kwargs = {"onexc": _rmtree_remove_readonly}
    else:
        kwargs = {"onerror": _rmtree_remove_readonly}
    shutil.rmtree(path, **kwargs)  # type: ignore[arg-type]
    return not path.exists()


def _handle_permission_error(
    error: PermissionError,
    path: Path,
    staging_dir: Path | None,
) -> tuple[bool, bool]:
    """Handle a PermissionError during folder deletion.

    Args:
        error: The PermissionError that was raised.
        path: The root folder being deleted.
        staging_dir: Staging directory for locked items.

    Returns:
        Tuple of (should_break, should_return_false).
        - should_break: If True, break out of retry loop (success).
        - should_return_false: If True, return False (failure).
    """
    # Extract the locked path from the error
    locked_path: Path | None = None
    if error.filename:
        locked_path = Path(error.filename)

    # Cannot identify locked file
    if locked_path is None or not locked_path.exists():
        if not path.exists():
            logger.debug("Folder removed during deletion: %s", path)
            return True, False  # Success - break
        logger.warning("Permission denied but cannot identify locked file: %s", error)
        return False, True  # Failure - return False

    # Locked path is the root directory itself (became empty during deletion)
    if locked_path == path:
        if _try_delete_empty_directory(path, staging_dir):
            return True, False  # Success - break
        return False, False  # Continue retry loop

    # Try moving the locked item to staging
    if _move_to_staging(locked_path, staging_dir):
        logger.debug("Moved locked item to staging: %s", locked_path)
        if not path.exists():
            return True, False  # Success - break
        return False, False  # Continue retry loop

    # Move failed - continue retry loop
    logger.debug("Failed to move locked item: %s", locked_path)
    return False, False


def safe_delete_folder(
    path: Union[Path, str],
    *,
    staging_dir: Union[Path, str, None] = None,
    cleanup_staging: bool = True,
) -> bool:
    """Safely delete a folder, handling locked files via staging directory.

    This function implements a three-step deletion strategy:
    1. Fast path: Try shutil.rmtree() directly
    2. Handle locks: Move locked items to staging, retry
    3. Housekeeping: Clean up staging directory (optional)

    Args:
        path: Path to the folder to delete.
        staging_dir: Custom staging directory for locked files.
            Defaults to %TEMP%/safe_delete_staging.
        cleanup_staging: Whether to clean up the staging directory after
            deletion. Defaults to True.

    Returns:
        True if the folder was deleted (or didn't exist), False if deletion
        failed after MAX_RETRIES attempts.

    Example:
        >>> from mcp_coder.utils.folder_deletion import safe_delete_folder
        >>> safe_delete_folder("/path/to/folder")
        True
    """
    # Convert to Path
    path = Path(path)

    # Idempotent: return True if folder doesn't exist
    if not path.exists():
        logger.debug("Folder does not exist (already deleted): %s", path)
        return True

    # Resolve staging_dir
    resolved_staging: Path | None
    if staging_dir is not None:
        resolved_staging = Path(staging_dir)
    else:
        resolved_staging = None  # Will use default in helper functions

    for attempt in range(MAX_RETRIES):
        # Check if folder is already gone (e.g., moved in previous iteration)
        if not path.exists():
            logger.debug("Folder removed after %d attempts: %s", attempt + 1, path)
            break

        # Special handling for empty directories
        # Empty dirs can be locked at the directory level (not file level)
        if _is_directory_empty(path):
            if _try_delete_empty_directory(path, resolved_staging):
                break
            # If we couldn't delete an empty dir, no point retrying with rmtree
            logger.warning(
                "Failed to delete empty locked directory after %d attempts: %s",
                attempt + 1,
                path,
            )
            if cleanup_staging:
                _cleanup_staging(resolved_staging)
            return False

        try:
            if _try_rmtree(path):
                logger.debug("Deleted folder directly: %s", path)
                break

        except PermissionError as e:
            should_break, should_fail = _handle_permission_error(
                e, path, resolved_staging
            )
            if should_fail:
                if cleanup_staging:
                    _cleanup_staging(resolved_staging)
                return False
            if should_break:
                break

        except OSError as e:
            if not path.exists():
                logger.debug("Folder removed (OSError but gone): %s", path)
                break
            logger.warning("OS error during deletion: %s - %s", path, e)
            if cleanup_staging:
                _cleanup_staging(resolved_staging)
            return False

    else:
        # Loop completed without break - exceeded MAX_RETRIES
        logger.warning(
            "Failed to delete folder after %d retries: %s", MAX_RETRIES, path
        )
        if cleanup_staging:
            _cleanup_staging(resolved_staging)
        return False

    # Success - optionally clean up staging
    if cleanup_staging:
        deleted, remaining = _cleanup_staging(resolved_staging)
        if deleted > 0 or remaining > 0:
            logger.debug(
                "Staging cleanup: deleted=%d, remaining=%d", deleted, remaining
            )

    return True
