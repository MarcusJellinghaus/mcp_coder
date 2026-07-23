"""Git-backed tests for the low-level git helpers in ``workflows/rebase.py``.

Covers ``_run_git``, ``_is_rebase_in_progress``, ``_abort_rebase``,
``_reset_hard`` and ``_rebase_success_shape``. These touch a real git
repository, so every test is marked ``git_integration`` and builds on a
temp-repo fixture with an initial commit.
"""

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.workflows.rebase import (
    _abort_rebase,
    _is_rebase_in_progress,
    _rebase_success_shape,
    _reset_hard,
    _run_git,
)

# Import git fixtures from utils (re-exported for pytest discovery).
from tests.utils.conftest import git_repo_with_files


def _commit_new_file(repo: Any, project_dir: Path, name: str, content: str) -> str:
    """Create, stage and commit a file; return the new HEAD sha."""
    (project_dir / name).write_text(content)
    repo.index.add([name])
    repo.index.commit(f"Add {name}")
    return str(repo.head.commit.hexsha)


@pytest.mark.git_integration
class TestRunGit:
    """Tests for the raw ``_run_git`` subprocess runner."""

    def test_rev_parse_head_succeeds(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """``rev-parse HEAD`` returns ``returncode == 0`` and the HEAD sha."""
        repo, project_dir = git_repo_with_files

        result = _run_git(project_dir, "rev-parse", "HEAD")

        assert result.returncode == 0
        assert result.stdout.strip() == repo.head.commit.hexsha

    def test_invalid_subcommand_nonzero(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """An unknown ref yields a non-zero return code without raising."""
        _, project_dir = git_repo_with_files

        result = _run_git(project_dir, "rev-parse", "no-such-ref")

        assert result.returncode != 0


@pytest.mark.git_integration
class TestIsRebaseInProgress:
    """Tests for the filesystem-based mid-rebase detection."""

    def test_false_on_clean_repo(self, git_repo_with_files: tuple[Any, Path]) -> None:
        """A repo with no rebase state is not mid-rebase."""
        _, project_dir = git_repo_with_files

        assert _is_rebase_in_progress(project_dir) is False

    def test_true_with_rebase_merge_dir(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """A ``.git/rebase-merge`` directory signals a rebase in progress."""
        _, project_dir = git_repo_with_files

        (project_dir / ".git" / "rebase-merge").mkdir()

        assert _is_rebase_in_progress(project_dir) is True

    def test_true_with_rebase_apply_dir(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """A ``.git/rebase-apply`` directory signals a rebase in progress."""
        _, project_dir = git_repo_with_files

        (project_dir / ".git" / "rebase-apply").mkdir()

        assert _is_rebase_in_progress(project_dir) is True


@pytest.mark.git_integration
class TestAbortRebase:
    """Tests for the best-effort rebase abort."""

    def test_no_raise_when_not_rebasing(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """Aborting with no rebase in progress is a silent no-op."""
        _, project_dir = git_repo_with_files

        # Must not raise even though there is nothing to abort.
        _abort_rebase(project_dir)


@pytest.mark.git_integration
class TestResetHard:
    """Tests for the hard-reset restore helper."""

    def test_reset_restores_captured_sha(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """After a new commit, ``_reset_hard`` returns HEAD to the captured sha."""
        repo, project_dir = git_repo_with_files
        original_sha = repo.head.commit.hexsha

        new_sha = _commit_new_file(repo, project_dir, "extra.txt", "content")
        assert new_sha != original_sha

        _reset_hard(project_dir, original_sha)

        assert repo.head.commit.hexsha == original_sha


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
