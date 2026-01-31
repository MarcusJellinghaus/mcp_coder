"""Cleanup functions for vscodeclaude feature."""

import logging
import shutil
from pathlib import Path

from .orchestrator import _get_configured_repos
from .sessions import check_vscode_running, load_sessions, remove_session
from .status import check_folder_dirty, is_session_stale
from .types import VSCodeClaudeSession

logger = logging.getLogger(__name__)


def get_stale_sessions() -> list[tuple[VSCodeClaudeSession, bool]]:
    """Get stale sessions with dirty status.

    Only checks sessions for repos that are still configured.

    Returns:
        List of (session, is_dirty) tuples for stale sessions
    """
    store = load_sessions()
    stale_sessions: list[tuple[VSCodeClaudeSession, bool]] = []

    # Load configured repos (skip sessions for repos no longer in config)
    configured_repos = _get_configured_repos()

    for session in store["sessions"]:
        # Skip sessions with running VSCode
        if check_vscode_running(session.get("vscode_pid")):
            continue

        # Skip sessions for unconfigured repos
        repo_full_name = session["repo"]
        if repo_full_name not in configured_repos:
            logger.debug(
                "Skipping stale check for issue #%d: repo %s not in config",
                session["issue_number"],
                repo_full_name,
            )
            continue

        # Check if session is stale
        if is_session_stale(session):
            folder_path = Path(session["folder"])
            is_dirty = (
                check_folder_dirty(folder_path) if folder_path.exists() else False
            )
            stale_sessions.append((session, is_dirty))

    return stale_sessions


def delete_session_folder(session: VSCodeClaudeSession) -> bool:
    """Delete session folder and remove from session store.

    Args:
        session: Session to delete

    Returns:
        True if successfully deleted

    Uses shutil.rmtree for folder deletion.
    """
    folder_path = Path(session["folder"])

    try:
        # Delete the folder if it exists
        if folder_path.exists():
            shutil.rmtree(folder_path)
            logger.info("Deleted folder: %s", folder_path)

        # Also delete the workspace file if it exists
        workspace_base = folder_path.parent
        workspace_file = workspace_base / f"{folder_path.name}.code-workspace"
        if workspace_file.exists():
            workspace_file.unlink()
            logger.info("Deleted workspace file: %s", workspace_file)

        # Remove session from store
        remove_session(session["folder"])

        return True
    except Exception as e:
        logger.error("Failed to delete session folder %s: %s", folder_path, e)
        return False


def cleanup_stale_sessions(dry_run: bool = True) -> dict[str, list[str]]:
    """Clean up stale session folders.

    Args:
        dry_run: If True, only report what would be deleted

    Returns:
        Dict with "deleted" and "skipped" folder lists

    Behavior:
    - Stale + clean: delete folder and session
    - Stale + dirty: skip with warning
    """
    result: dict[str, list[str]] = {"deleted": [], "skipped": []}

    stale_sessions = get_stale_sessions()

    for session, is_dirty in stale_sessions:
        folder = session["folder"]

        if is_dirty:
            # Skip dirty folders with warning
            logger.warning(
                "Skipping dirty folder (has uncommitted changes): %s", folder
            )
            print(f"⚠️  Skipping (dirty): {folder}")
            result["skipped"].append(folder)
        else:
            # Clean folder - delete or report
            if dry_run:
                print(f"Would delete: {folder}")
                # Don't add to deleted list in dry run - it wasn't actually deleted
            else:
                if delete_session_folder(session):
                    print(f"Deleted: {folder}")
                    result["deleted"].append(folder)
                else:
                    print(f"Failed to delete: {folder}")
                    result["skipped"].append(folder)

    if not stale_sessions:
        print("No stale sessions to clean up.")

    return result
