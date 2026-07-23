"""Automated ``mcp-coder rebase`` workflow — deterministic shell (Issue #1066).

Python owns the deterministic shell around a single LLM session: pre-flight
guards, the outcome→exit-code decision, the force-push, and a ``finally`` safety
net. This module currently holds only the two pure decision functions; git
helpers, guards, and the orchestrator are added in later steps.

The exit-code contract cross-checks two signals and never trusts either alone:
the LLM's self-reported outcome marker and the actual git repository state (git
is authoritative, worst-case-wins).
"""

import re
import subprocess
from pathlib import Path

from mcp_coder.mcp_workspace_git import (
    get_latest_commit_sha,
    is_working_directory_clean,
)

_OUTCOME_RE = re.compile(r"^\s*REBASE_OUTCOME:\s*(.+?)\s*$", re.MULTILINE)
_REASON_RE = re.compile(r"^\s*REBASE_REASON:\s*(.+?)\s*$", re.MULTILINE)

_VALID_OUTCOMES = {"success", "aborted"}


def _parse_outcome_marker(response_text: str) -> tuple[str | None, str | None]:
    """Extract ``(outcome, reason)`` from the LLM response.

    ``outcome`` is ``"success"`` | ``"aborted"`` | ``None`` (unparseable or an
    unrecognized value). ``reason`` is the ``REBASE_REASON`` text, or ``None``
    when absent or ``"n/a"``. Last match wins for both markers.
    """
    outcome: str | None = None
    outcome_matches = _OUTCOME_RE.findall(response_text)
    if outcome_matches:
        candidate = outcome_matches[-1].strip().lower()
        if candidate in _VALID_OUTCOMES:
            outcome = candidate

    reason: str | None = None
    reason_matches = _REASON_RE.findall(response_text)
    if reason_matches:
        candidate_reason = reason_matches[-1].strip()
        if candidate_reason and candidate_reason.lower() != "n/a":
            reason = candidate_reason

    return outcome, reason


def _evaluate_pre_push(
    *,
    mid_rebase: bool,
    marker_outcome: str | None,
    rebase_success_shape: bool,
) -> str:
    """Return ``"push"`` or ``"abort"`` (worst-case-wins, git is authoritative)."""
    if mid_rebase:
        return "abort"  # unfinished / crashed session
    if marker_outcome == "aborted":
        return "abort"  # trust the self-report
    if not rebase_success_shape:
        return "abort"  # git can't corroborate success
    return "push"  # marker success/unparseable AND git confirms


def _run_git(project_dir: Path, *args: str) -> "subprocess.CompletedProcess[str]":
    """Run ``git <args>`` in ``project_dir`` (list form, no shell, ``check=False``).

    Returns the completed process so callers can inspect ``.returncode``,
    ``.stdout`` and ``.stderr``. Never raises on a non-zero git exit; the caller
    decides what a failure means.
    """
    # Fixed argv, no shell, trusted ``git`` CLI — bandit B603/B607 are inherent to
    # any subprocess call and accepted repo-wide (see workflows/vscodeclaude,
    # utils/mcp_verification), so no suppression is added here for consistency.
    return subprocess.run(
        ["git", *args],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        check=False,
    )


def _is_rebase_in_progress(project_dir: Path) -> bool:
    """Return True if a rebase is mid-flight.

    Detected purely from the filesystem: git creates ``.git/rebase-merge`` (merge
    backend) or ``.git/rebase-apply`` (apply backend) while a rebase is unfinished.
    """
    git_dir = project_dir / ".git"
    return (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists()


def _abort_rebase(project_dir: Path) -> None:
    """Best-effort ``git rebase --abort`` (never raises).

    Used by the ``finally`` safety net; if no rebase is in progress git simply
    exits non-zero, which ``_run_git`` swallows.
    """
    _run_git(project_dir, "rebase", "--abort")


def _reset_hard(project_dir: Path, sha: str) -> None:
    """Restore pre-rebase state with ``git reset --hard <sha>``."""
    _run_git(project_dir, "reset", "--hard", sha)


def _rebase_success_shape(project_dir: Path, pre_sha: str) -> bool:
    """Return True iff HEAD moved off ``pre_sha``, tree is clean, and not mid-rebase.

    This is the git-side corroboration of a claimed rebase success: no rebase may
    be in progress, the working tree must be clean, and HEAD must differ from the
    pre-rebase commit.
    """
    if _is_rebase_in_progress(project_dir):
        return False
    if not is_working_directory_clean(project_dir):
        return False
    return get_latest_commit_sha(project_dir) != pre_sha
