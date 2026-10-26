"""Git-backed tests for the low-level git helpers in ``workflows/rebase.py``.

Covers ``_abort_rebase``, ``_restore_note`` (over the shared ``_reset_hard``
from ``workflow_steps/rebase.py``), ``_rebase_success_shape``, ``_show_stage``
and ``_stage_all_and_continue``, plus the upstream ``stage_all_changes`` /
``commit_all_changes`` behaviour the rebase loop relies on. Tests touching a
real git repository are marked ``git_integration`` and build on a temp-repo
fixture with an initial commit; the pure text helper ``_has_conflict_markers``
gets plain unit tests.
"""

import logging
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.mcp_workspace_git import (
    checkout_branch,
    commit_all_changes,
    create_branch,
    get_conflict_blob_info,
    is_rebase_in_progress,
    rebase_continue,
    rebase_start,
    stage_all_changes,
)
from mcp_coder.workflows.rebase import (
    _abort_rebase,
    _has_conflict_markers,
    _rebase_success_shape,
    _restore_note,
    _show_stage,
    _stage_all_and_continue,
)

# ``git_repo_with_files`` is provided by the local ``conftest.py`` via pytest
# fixture discovery (kept out of ``tests.utils`` for module independence).


def _commit_new_file(repo: Any, project_dir: Path, name: str, content: str) -> str:
    """Create, stage and commit a file; return the new HEAD sha."""
    (project_dir / name).write_text(content)
    repo.index.add([name])
    repo.index.commit(f"Add {name}")
    return str(repo.head.commit.hexsha)


@pytest.mark.git_integration
class TestAbortRebase:
    """Tests for the best-effort rebase abort."""

    def test_no_raise_when_not_rebasing(
        self, git_repo_with_files: tuple[Any, Path], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Aborting with no rebase in progress is a silent no-op."""
        _, project_dir = git_repo_with_files

        with caplog.at_level(logging.ERROR, logger="mcp_coder.workflows.rebase"):
            _abort_rebase(project_dir)

        assert not caplog.records

    def test_aborts_stopped_rebase(self, git_repo_with_files: tuple[Any, Path]) -> None:
        """A rebase stopped at a conflict is aborted."""
        repo, project_dir = git_repo_with_files
        _start_conflicted_rebase(repo, project_dir, "conflict.txt")
        assert is_rebase_in_progress(project_dir) is True

        _abort_rebase(project_dir)

        assert is_rebase_in_progress(project_dir) is False


@pytest.mark.git_integration
class TestResetHard:
    """Tests for the hard-reset restore helper."""

    def test_reset_restores_captured_sha(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """After a new commit, ``_restore_note`` returns HEAD to the captured sha."""
        repo, project_dir = git_repo_with_files
        original_sha = repo.head.commit.hexsha

        new_sha = _commit_new_file(repo, project_dir, "extra.txt", "content")
        assert new_sha != original_sha

        assert _restore_note(project_dir, original_sha) == (
            "; pre-rebase state restored"
        )

        assert repo.head.commit.hexsha == original_sha

    def test_failure_returns_failed_note_and_logs_error(
        self, git_repo_with_files: tuple[Any, Path], caplog: pytest.LogCaptureFixture
    ) -> None:
        """An unknown sha leaves HEAD alone and yields the FAILED note."""
        repo, project_dir = git_repo_with_files
        head = repo.head.commit.hexsha

        with caplog.at_level(logging.ERROR, logger="mcp_coder.workflow_steps.rebase"):
            note = _restore_note(project_dir, "0" * 40)

        assert note == "; restoring pre-rebase state FAILED (see log)"
        assert repo.head.commit.hexsha == head
        assert any(r.levelno == logging.ERROR for r in caplog.records)


@pytest.mark.git_integration
class TestRebaseSuccessShape:
    """Tests for the ``_rebase_success_shape`` composite check."""

    def test_false_when_head_unchanged(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """HEAD still on ``pre_sha`` means the rebase did not advance."""
        repo, project_dir = git_repo_with_files
        pre_sha = repo.head.commit.hexsha

        assert _rebase_success_shape(project_dir, pre_sha) is False

    def test_true_after_clean_new_commit(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """HEAD moved off ``pre_sha`` with a clean tree → success shape."""
        repo, project_dir = git_repo_with_files
        pre_sha = repo.head.commit.hexsha

        _commit_new_file(repo, project_dir, "extra.txt", "content")

        assert _rebase_success_shape(project_dir, pre_sha) is True

    def test_false_with_dirty_tree(self, git_repo_with_files: tuple[Any, Path]) -> None:
        """A dirty working tree fails the success shape even after a new commit."""
        repo, project_dir = git_repo_with_files
        pre_sha = repo.head.commit.hexsha

        _commit_new_file(repo, project_dir, "extra.txt", "content")
        (project_dir / "dirty.txt").write_text("uncommitted")

        assert _rebase_success_shape(project_dir, pre_sha) is False

    def test_false_when_mid_rebase(self, git_repo_with_files: tuple[Any, Path]) -> None:
        """A rebase in progress fails the success shape even with moved HEAD."""
        repo, project_dir = git_repo_with_files
        pre_sha = repo.head.commit.hexsha

        _commit_new_file(repo, project_dir, "extra.txt", "content")
        (project_dir / ".git" / "rebase-merge").mkdir()

        assert _rebase_success_shape(project_dir, pre_sha) is False


# --- Conflict-helper test support ---

_ANCESTOR = b"shared line\n"
_BASE_VERSION = b"base edit\n"
_FEATURE_VERSION = b"feature edit\n"


def _write_and_commit(
    repo: Any, project_dir: Path, name: str, data: bytes, message: str
) -> None:
    """Write ``data`` to ``name`` (creating parent dirs), stage and commit."""
    path = project_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    repo.index.add([name])
    repo.index.commit(message)


def _start_conflicted_rebase(
    repo: Any,
    project_dir: Path,
    filename: str,
    ancestor: bytes = _ANCESTOR,
    base_version: bytes = _BASE_VERSION,
    feature_version: bytes | None = _FEATURE_VERSION,
) -> str:
    """Create a base/feature divergence on ``filename`` and start the rebase.

    Both branches edit the same file (``feature_version=None`` deletes it on
    the feature branch instead, producing a delete/modify conflict). Leaves
    the repo stopped at the conflict and returns the base branch name.
    """
    base_branch = str(repo.active_branch.name)
    _write_and_commit(repo, project_dir, filename, ancestor, f"Add {filename}")
    assert create_branch("feature", project_dir)
    assert checkout_branch(base_branch, project_dir)
    _write_and_commit(repo, project_dir, filename, base_version, "Base edit")
    assert checkout_branch("feature", project_dir)
    if feature_version is None:
        repo.index.remove([filename], working_tree=True)
        repo.index.commit(f"Delete {filename}")
    else:
        _write_and_commit(repo, project_dir, filename, feature_version, "Feature edit")
    result = rebase_start(project_dir, base_branch)
    assert result["status"] == "stopped_on_conflict", result
    return base_branch


@pytest.mark.git_integration
class TestShowStage:
    """Tests for reading an index stage of a conflicted file."""

    def test_missing_side_returns_none(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """A delete/modify conflict has no stage 3 (theirs deleted the file)."""
        repo, project_dir = git_repo_with_files

        _start_conflicted_rebase(
            repo, project_dir, "conflict.txt", feature_version=None
        )

        assert _show_stage(project_dir, 3, "conflict.txt") is None
        assert _show_stage(project_dir, 2, "conflict.txt") == _BASE_VERSION.decode()


@pytest.mark.git_integration
class TestStageAllInRebase:
    """Upstream ``stage_all_changes`` stages LLM-resolved unmerged files."""

    def test_resolved_file_staged_and_continue_completes(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """Resolved content is staged, no conflicts remain, continue completes."""
        repo, project_dir = git_repo_with_files
        _start_conflicted_rebase(repo, project_dir, "conflict.txt")
        (project_dir / "conflict.txt").write_bytes(b"resolved\n")

        assert stage_all_changes(project_dir) is True

        info = get_conflict_blob_info(project_dir)
        assert info["success"] is True
        assert info["entries"] == []
        assert rebase_continue(project_dir)["status"] == "completed"


@pytest.mark.git_integration
class TestStageAllAndContinue:
    """Tests for the stage-everything-and-continue step."""

    def test_finishes_single_conflict_rebase(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """After resolving the only conflict, continue completes the rebase."""
        repo, project_dir = git_repo_with_files
        _start_conflicted_rebase(repo, project_dir, "conflict.txt")
        (project_dir / "conflict.txt").write_bytes(b"resolved\n")

        result = _stage_all_and_continue(project_dir)

        assert result["status"] == "completed"
        assert is_rebase_in_progress(project_dir) is False


@pytest.mark.git_integration
class TestCommitAllChanges:
    """Upstream ``commit_all_changes`` as used by the regression-fix loop."""

    def test_clean_tree_is_success_without_commit(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """Nothing to commit is ``success=True`` with no commit hash."""
        repo, project_dir = git_repo_with_files
        head = repo.head.commit.hexsha

        result = commit_all_changes("fix: nothing", project_dir)

        assert result["success"] is True
        assert result["commit_hash"] is None
        assert repo.head.commit.hexsha == head


class TestHasConflictMarkers:
    """Plain unit tests for the conflict-marker scan (no git needed)."""

    def test_true_with_real_markers(self, tmp_path: Path) -> None:
        """Genuine ``<<<<<<< `` / ``>>>>>>> `` marker lines are detected."""
        (tmp_path / "conflicted.txt").write_text(
            "<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> abc123 (feature)\n",
            encoding="utf-8",
        )

        assert _has_conflict_markers(tmp_path, "conflicted.txt") is True

    def test_false_for_markdown_underline(self, tmp_path: Path) -> None:
        """A bare ``=======`` line (markdown underline) is not a marker."""
        (tmp_path / "doc.md").write_text(
            "Heading\n=======\n\nLegitimate text.\n", encoding="utf-8"
        )

        assert _has_conflict_markers(tmp_path, "doc.md") is False

    def test_false_for_missing_file(self, tmp_path: Path) -> None:
        """A missing file (legitimately deleted) is marker-free."""
        assert _has_conflict_markers(tmp_path, "gone.txt") is False
