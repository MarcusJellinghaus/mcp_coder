"""Cleanup functions for vscodeclaude feature.

This is an ``apply()`` consumer of the assessment pipeline: it reads the prebuilt
:class:`SessionAssessment` map (the eligibility + git-status safety matrix already
decided in ``assess_session``) and never re-derives stale/closed logic or re-checks
git status to gate a destructive delete.
"""

import logging
from pathlib import Path

from ...utils.folder_deletion import (
    DeletionFailureReason,
    safe_delete_folder,
)
from .helpers import (
    add_to_be_deleted,
    load_to_be_deleted,
    remove_from_to_be_deleted,
)
from .sessions import (
    load_sessions,
    remove_session,
    warn_orphan_folders,
)
from .types import SessionAction, SessionAssessment, VSCodeClaudeSession
from .workspace import get_workspace_file_path

logger = logging.getLogger(__name__)


def get_stale_sessions(
    assessments: dict[str, SessionAssessment],
) -> list[tuple[VSCodeClaudeSession, SessionAssessment]]:
    """Return non-active sessions whose decision implies cleanup handling.

    Reads the prebuilt assessments instead of re-deriving eligibility: the
    closed/stale/blocked/unassigned/ineligible classification and the next action
    were decided once in ``assess_session`` (R1). Active sessions are skipped here
    (``a.verdict.active`` covers both ``KEEP_ACTIVE`` and zombie
    ``INVESTIGATE_ZOMBIE`` — both stay tracked), and ``RESTART`` sessions are left
    for the restart path. What remains is the cleanup action space:
    ``DELETE`` / ``REMOVE_MISSING`` / ``SKIP``.

    Args:
        assessments: Folder-path -> :class:`SessionAssessment` map built once per
            run by ``build_assessments``.

    Returns:
        List of ``(session, assessment)`` pairs that cleanup must act on.
    """
    store = load_sessions()
    stale_sessions: list[tuple[VSCodeClaudeSession, SessionAssessment]] = []

    for session in store["sessions"]:
        assessment = assessments.get(session["folder"])
        if assessment is None:
            continue
        # Skip active (KEEP_ACTIVE + zombie INVESTIGATE_ZOMBIE both stay tracked).
        if assessment.verdict.active:
            continue
        # RESTART is the restart path's job, not cleanup's.
        if assessment.decision.action == SessionAction.RESTART:
            continue
        stale_sessions.append((session, assessment))

    return stale_sessions


def delete_session_folder(
    session: VSCodeClaudeSession,
    workspace_base: str,
) -> bool:
    """Delete session folder, then workspace file, then session record.

    Ordering fix + lock veto: the folder is deleted FIRST, and the
    ``.code-workspace`` launcher only AFTER folder deletion succeeds. On a failed
    delete (locked folder) the entry is queued in ``.to_be_deleted`` for retry and
    the session is left tracked — ``remove_session`` is never called on a failed
    delete and the workspace file is never unlinked (lock-failure veto).

    Args:
        session: Session to delete.
        workspace_base: Path to workspace directory.

    Returns:
        True if the folder was removed (or already gone) and the session record
        removed; False on a failed delete (entry queued for retry).
    """
    folder_path = Path(session["folder"])
    folder_name = folder_path.name

    if folder_path.exists():
        deletion = safe_delete_folder(folder_path)
        if not deletion.success:
            if deletion.reason == DeletionFailureReason.LOCKED_EMPTY_DIR:
                logger.error(
                    "Failed to delete session folder - directory is empty "
                    "but locked by Windows (close Explorer or any app with "
                    "a window open to this folder, then retry): %s",
                    deletion.detail or folder_path,
                )
            else:
                reason_label = deletion.reason.value if deletion.reason else "unknown"
                logger.error(
                    "Failed to delete session folder (%s): %s",
                    reason_label,
                    deletion.detail or folder_path,
                )
            # Lock veto: queue for retry, keep the session tracked, do NOT unlink
            # the workspace file.
            add_to_be_deleted(workspace_base, folder_name)
            return False
        logger.info("Deleted folder: %s", folder_path)

        # Only AFTER the folder is gone, remove the launcher file.
        workspace_file = get_workspace_file_path(workspace_base, folder_name)
        try:
            workspace_file.unlink(missing_ok=True)
        except OSError:
            logger.warning("Failed to delete workspace file: %s", workspace_file)

    # Remove session from store.
    remove_session(session["folder"])
    return True


def _retry_to_be_deleted(
    workspace_base: str,
    assessments: dict[str, SessionAssessment],
) -> None:
    """Retry queued ``.to_be_deleted`` folders, consuming the assessment map.

    ``.to_be_deleted`` is keyed by folder NAME; ``assessments`` is keyed by folder
    PATH, so each entry is resolved under ``workspace_base`` to look up its
    assessment. A live folder (assessment ``verdict.active``) is spared and left in
    the queue — replacing the cmdline-only ``is_vscode_open_for_folder`` check and
    closing the second #38 door.
    """
    to_delete = load_to_be_deleted(workspace_base)
    for folder_name in list(to_delete):
        folder_path = Path(workspace_base) / folder_name
        assessment = assessments.get(str(folder_path))

        # Assessment exists + active -> spare the live folder; leave it queued.
        if assessment is not None and assessment.verdict.active:
            logger.debug(
                "Sparing .to_be_deleted entry — session is live on %s; "
                "leaving entry queued.",
                folder_name,
            )
            continue

        # Folder gone (inactive assessment or no assessment) -> drop the entry.
        if not folder_path.exists():
            remove_from_to_be_deleted(workspace_base, folder_name)
            logger.info("Removed stale .to_be_deleted entry: %s", folder_name)
            continue

        # Inactive assessment OR no assessment, folder still present -> retry.
        deletion = safe_delete_folder(folder_path)
        if deletion.success:
            remove_from_to_be_deleted(workspace_base, folder_name)
            logger.info("Retry-deleted soft-deleted folder: %s", folder_name)


def cleanup_stale_sessions(
    workspace_base: str,
    assessments: dict[str, SessionAssessment],
    dry_run: bool = True,
) -> dict[str, list[str]]:
    """Clean up stale session folders by consuming prebuilt assessments.

    Args:
        workspace_base: Path to workspace directory.
        assessments: Folder-path -> :class:`SessionAssessment` map built once per
            run by ``build_assessments``.
        dry_run: If True, only report what would be deleted.

    Returns:
        Dict with "deleted" and "skipped" folder lists.

    The action is driven entirely by ``a.decision.action`` (decided upstream in
    ``decide``); cleanup never re-checks git status to gate a destructive delete:
    - ``DELETE``: delete folder, then workspace file, then session record.
    - ``REMOVE_MISSING``: remove session + orphan workspace file (folder gone).
    - ``SKIP``: report ``a.decision.reason`` (dirty / unverified non-empty).

    Retry logic: on non-dry-run, retries ``.to_be_deleted`` entries first,
    consuming the assessment map (live folders are spared, never deleted).
    """
    result: dict[str, list[str]] = {"deleted": [], "skipped": []}

    # Retry .to_be_deleted entries before processing stale sessions.
    if not dry_run:
        _retry_to_be_deleted(workspace_base, assessments)

    # Run orphan detection for all repos with active sessions.
    if not dry_run:
        store = load_sessions()
        session_folders = {Path(s["folder"]).name for s in store["sessions"]}
        to_be_deleted_set = load_to_be_deleted(workspace_base)
        sessions_by_repo: dict[str, set[int]] = {}
        for session in store["sessions"]:
            repo = session["repo"]
            sessions_by_repo.setdefault(repo, set()).add(session["issue_number"])

        for repo_full_name, issues in sessions_by_repo.items():
            for issue_number in issues:
                warn_orphan_folders(
                    workspace_base,
                    repo_full_name,
                    issue_number,
                    session_folders=session_folders,
                    to_be_deleted=to_be_deleted_set,
                )

    stale_sessions = get_stale_sessions(assessments)

    for session, assessment in stale_sessions:
        folder = session["folder"]
        action = assessment.decision.action
        reason = assessment.decision.reason

        if action == SessionAction.DELETE:
            if dry_run:
                print(f"Add --cleanup to delete ({reason}): {folder}")
                # Don't add to deleted list in dry run - it wasn't actually deleted
            else:
                if delete_session_folder(session, workspace_base=workspace_base):
                    print(f"Deleted: {folder}")
                    result["deleted"].append(folder)
                else:
                    print(f"Failed to delete: {folder}")
                    result["skipped"].append(folder)

        elif action == SessionAction.REMOVE_MISSING:
            # Folder gone - also clean up orphan workspace file to break the
            # orphan-workspace -> false-active -> cleanup-skipped loop.
            workspace_file = get_workspace_file_path(workspace_base, Path(folder).name)
            if dry_run:
                print(f"Would remove session (folder missing): {folder}")
            else:
                if workspace_file.exists():
                    workspace_file.unlink()
                remove_session(folder)
                print(f"Removed session (folder missing): {folder}")
                result["deleted"].append(folder)

        else:  # SessionAction.SKIP
            logger.warning("Skipping (%s): %s", reason, folder)
            print(f"[WARN] Skipping ({reason}): {folder}")
            result["skipped"].append(folder)

    if not stale_sessions:
        print("No stale sessions to clean up.")

    return result
