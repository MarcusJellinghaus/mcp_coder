"""Git-backed tests for the low-level git helpers in ``workflows/rebase.py``.

Covers ``_run_git``, ``_is_rebase_in_progress``, ``_abort_rebase``,
``_reset_hard``, ``_rebase_success_shape`` and the conflict helpers
(``_conflicted_files``, ``_binary_conflict``, ``_resolve_pr_info_conflict``,
``_show_stage``, ``_stage_all_and_continue``). Tests touching a real git
repository are marked ``git_integration`` and build on a temp-repo fixture
with an initial commit; the pure text helper ``_has_conflict_markers`` gets
plain unit tests.
"""

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.workflows.rebase import (
    _abort_rebase,
    _binary_conflict,
    _conflicted_files,
    _has_conflict_markers,
    _is_rebase_in_progress,
    _rebase_success_shape,
    _reset_hard,
    _resolve_pr_info_conflict,
    _run_git,
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
    _run_git(project_dir, "branch", "feature")
    _write_and_commit(repo, project_dir, filename, base_version, "Base edit")
    _run_git(project_dir, "checkout", "feature")
    if feature_version is None:
        repo.index.remove([filename], working_tree=True)
        repo.index.commit(f"Delete {filename}")
    else:
        _write_and_commit(repo, project_dir, filename, feature_version, "Feature edit")
    result = _run_git(project_dir, "rebase", base_branch)
    assert result.returncode != 0, "rebase should stop at the conflict"
    return base_branch


@pytest.mark.git_integration
class TestConflictedFiles:
    """Tests for the unmerged-path listing."""

    def test_empty_on_clean_repo(self, git_repo_with_files: tuple[Any, Path]) -> None:
        """A repo without conflicts lists no conflicted files."""
        _, project_dir = git_repo_with_files

        assert _conflicted_files(project_dir) == []

    def test_lists_conflicted_file(self, git_repo_with_files: tuple[Any, Path]) -> None:
        """A stopped rebase exposes the conflicted path."""
        repo, project_dir = git_repo_with_files

        _start_conflicted_rebase(repo, project_dir, "conflict.txt")

        assert _conflicted_files(project_dir) == ["conflict.txt"]


@pytest.mark.git_integration
class TestShowStage:
    """Tests for reading the three index stages of a conflicted file."""

    def test_all_three_stages_present(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """Stage 1/2/3 return ancestor, base (ours) and feature (theirs)."""
        repo, project_dir = git_repo_with_files

        _start_conflicted_rebase(repo, project_dir, "conflict.txt")

        assert _show_stage(project_dir, 1, "conflict.txt") == _ANCESTOR.decode()
        assert _show_stage(project_dir, 2, "conflict.txt") == _BASE_VERSION.decode()
        assert _show_stage(project_dir, 3, "conflict.txt") == _FEATURE_VERSION.decode()

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
class TestResolvePrInfoConflict:
    """Tests for the deterministic pr_info/ auto-resolution."""

    def test_theirs_resolution(self, git_repo_with_files: tuple[Any, Path]) -> None:
        """A both-modified pr_info/ file resolves to the feature version."""
        repo, project_dir = git_repo_with_files
        _start_conflicted_rebase(repo, project_dir, "pr_info/notes.md")

        assert _resolve_pr_info_conflict(project_dir, "pr_info/notes.md") is True

        # read_text() normalizes newlines — git autocrlf may check the feature
        # version out with CRLF on Windows.
        content = (project_dir / "pr_info" / "notes.md").read_text(encoding="utf-8")
        assert content == _FEATURE_VERSION.decode()
        assert _conflicted_files(project_dir) == []

    def test_delete_modify_falls_back_to_rm(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """When the feature branch deleted the file, it stays deleted."""
        repo, project_dir = git_repo_with_files
        _start_conflicted_rebase(
            repo, project_dir, "pr_info/notes.md", feature_version=None
        )

        assert _resolve_pr_info_conflict(project_dir, "pr_info/notes.md") is True

        assert not (project_dir / "pr_info" / "notes.md").exists()
        assert _conflicted_files(project_dir) == []


@pytest.mark.git_integration
class TestBinaryConflict:
    """Tests for binary-conflict detection (both mandatory — a false positive
    would abort every LLM conflict resolution)."""

    def test_none_for_text_conflict(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """A plain text conflict must NOT read as binary."""
        repo, project_dir = git_repo_with_files

        _start_conflicted_rebase(repo, project_dir, "conflict.txt")

        assert _binary_conflict(project_dir) is None

    def test_detects_binary_conflict(
        self, git_repo_with_files: tuple[Any, Path]
    ) -> None:
        """Conflicting NUL-byte blobs are reported as a binary conflict."""
        repo, project_dir = git_repo_with_files

        _start_conflicted_rebase(
            repo,
            project_dir,
            "blob.bin",
            ancestor=b"\x00\x01ancestor\x00",
            base_version=b"\x00\x02base\x00",
            feature_version=b"\x00\x03feature\x00",
        )

        assert _binary_conflict(project_dir) == "blob.bin"


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

        assert result.returncode == 0
        assert _is_rebase_in_progress(project_dir) is False
        assert _conflicted_files(project_dir) == []


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
