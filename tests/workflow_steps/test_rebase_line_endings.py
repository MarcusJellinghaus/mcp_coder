"""Tests for clearing line-ending-only dirt before a rebase, against real git."""

import os
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from git import Repo

from mcp_coder.workflow_steps.rebase import (
    RebaseOutcome,
    _attempt_rebase_and_push,
    _clear_line_ending_dirt,
)

_MODULE = "mcp_coder.workflow_steps.rebase"
_CRLF_CONTENT = b"line one\r\nline two\r\n"

pytestmark = pytest.mark.git_integration


def _commit(repo: Repo, message: str, *files: str) -> None:
    """Commit ``files`` through the git CLI, filters included.

    Never ``git add .``: it would re-hash a racily-clean ``doc.md`` once
    ``.gitattributes`` exists and normalize it too early.
    """
    repo.git.add(*files)
    repo.git.commit("-m", message)


def _rewrite(path: Path, content: bytes) -> None:
    """Write ``content`` with a new mtime, so the stat cache can't hide the file."""
    path.write_bytes(content)
    stat = path.stat()
    os.utime(path, (stat.st_atime, stat.st_mtime + 2))


def _staged(repo: Repo) -> str:
    """Return the names of the staged files."""
    return str(repo.git.diff("--cached", "--name-only"))


@pytest.fixture(autouse=True)
def mock_detect_base() -> Iterator[None]:
    """Answer base detection without GitHub; everything else is real git."""
    with patch(f"{_MODULE}.detect_base_branch", return_value="main"):
        yield


@pytest.fixture
def crlf_repo(git_repo: tuple[Repo, Path], tmp_path: Path) -> tuple[Repo, Path]:
    """Feature branch with a bare origin and a permanently modified ``doc.md``.

    ``doc.md`` is committed with CRLF before ``.gitattributes`` makes it ``text``.

    Returns:
        The ``Repo`` object and the project directory path.
    """
    repo, project_dir = git_repo
    with repo.config_writer() as config:
        config.set_value("core", "autocrlf", "false")
    repo.git.checkout("-b", "main")

    (project_dir / "doc.md").write_bytes(_CRLF_CONTENT)
    _commit(repo, "Add CRLF doc", "doc.md")
    (project_dir / ".gitattributes").write_bytes(b"*.md text\n")
    (project_dir / "normal.md").write_bytes(b"already normalized\n")
    _commit(repo, "Add attributes", ".gitattributes", "normal.md")

    origin = tmp_path / "origin.git"
    Repo.init(origin, bare=True)
    repo.create_remote("origin", str(origin))
    repo.git.push("origin", "main")
    repo.git.checkout("-b", "feature")
    repo.git.push("-u", "origin", "feature")

    _rewrite(project_dir / "doc.md", _CRLF_CONTENT)
    assert repo.git.status("--porcelain") == " M doc.md"
    return repo, project_dir


class TestAttemptRebaseWithLineEndingDirt:
    """_attempt_rebase_and_push on a tree dirty through line endings."""

    def test_line_ending_only_is_committed_and_pushed(
        self, crlf_repo: tuple[Repo, Path], tmp_path: Path
    ) -> None:
        """Test the renormalize commit is created and reaches origin."""
        repo, project_dir = crlf_repo
        head_before = repo.head.commit.hexsha

        outcome = _attempt_rebase_and_push(project_dir)

        assert outcome.reason == "ok"
        assert outcome.base_branch == "main"
        assert repo.head.commit.hexsha != head_before
        assert repo.head.commit.message.strip() == "chore: renormalize line endings"
        assert repo.head.commit.parents[0].hexsha == head_before
        assert repo.git.status("--porcelain") == ""
        origin = Repo(tmp_path / "origin.git")
        assert origin.commit("feature").hexsha == repo.head.commit.hexsha

    def test_lf_blob_with_crlf_working_copy_is_dirty_tree(
        self, crlf_repo: tuple[Repo, Path]
    ) -> None:
        """Test a file with no ``text`` attribute is not committed with CRLF."""
        repo, project_dir = crlf_repo
        _commit(repo, "Normalize doc", "doc.md")
        (project_dir / "plain.txt").write_bytes(b"line one\nline two\n")
        _commit(repo, "Add LF file", "plain.txt")
        head_before = repo.head.commit.hexsha
        _rewrite(project_dir / "plain.txt", _CRLF_CONTENT)
        assert repo.git.status("--porcelain") == " M plain.txt"

        outcome = _attempt_rebase_and_push(project_dir)

        assert outcome == RebaseOutcome("dirty_tree", files=("plain.txt",))
        assert _staged(repo) == ""
        assert repo.head.commit.hexsha == head_before
        assert (project_dir / "plain.txt").read_bytes() == _CRLF_CONTENT

    def test_real_change_is_dirty_tree(self, crlf_repo: tuple[Repo, Path]) -> None:
        """Test a content change on top of CRLF blocks and leaves nothing staged."""
        repo, project_dir = crlf_repo
        head_before = repo.head.commit.hexsha
        _rewrite(project_dir / "doc.md", b"line one\r\nchanged\r\n")

        outcome = _attempt_rebase_and_push(project_dir)

        assert outcome == RebaseOutcome("dirty_tree", files=("doc.md",))
        assert _staged(repo) == ""
        assert repo.head.commit.hexsha == head_before
        assert (project_dir / "doc.md").read_bytes() == b"line one\r\nchanged\r\n"

    def test_deleted_tracked_file_is_dirty_tree(
        self, crlf_repo: tuple[Repo, Path]
    ) -> None:
        """Test a deletion counts as a real change."""
        repo, project_dir = crlf_repo
        head_before = repo.head.commit.hexsha
        (project_dir / "doc.md").unlink()

        outcome = _attempt_rebase_and_push(project_dir)

        assert outcome == RebaseOutcome("dirty_tree", files=("doc.md",))
        assert repo.head.commit.hexsha == head_before

    def test_one_real_change_blocks_the_line_ending_file_too(
        self, crlf_repo: tuple[Repo, Path]
    ) -> None:
        """Test all-or-nothing: the CRLF-only file is not committed on its own."""
        repo, project_dir = crlf_repo
        head_before = repo.head.commit.hexsha
        _rewrite(project_dir / "normal.md", b"real change\n")

        outcome = _attempt_rebase_and_push(project_dir)

        assert outcome == RebaseOutcome("dirty_tree", files=("doc.md", "normal.md"))
        assert _staged(repo) == ""
        assert repo.head.commit.hexsha == head_before

    def test_staged_new_file_is_not_committed(
        self, crlf_repo: tuple[Repo, Path]
    ) -> None:
        """Test a staged new file blocks instead of joining the renormalize commit."""
        repo, project_dir = crlf_repo
        head_before = repo.head.commit.hexsha
        (project_dir / "new.md").write_bytes(b"new\n")
        repo.git.add("new.md")

        outcome = _attempt_rebase_and_push(project_dir)

        assert outcome.reason == "dirty_tree"
        assert "new.md" in outcome.files
        assert repo.head.commit.hexsha == head_before


class TestClearLineEndingDirt:
    """Branches of _clear_line_ending_dirt not reachable through the status check."""

    def test_stat_only_dirt_creates_no_commit(
        self, crlf_repo: tuple[Repo, Path]
    ) -> None:
        """Test an already-normalized file stages nothing and needs no commit."""
        repo, project_dir = crlf_repo
        head_before = repo.head.commit.hexsha
        _rewrite(project_dir / "normal.md", b"already normalized\n")

        assert _clear_line_ending_dirt(project_dir, ["normal.md"]) is True

        assert repo.head.commit.hexsha == head_before
        assert _staged(repo) == ""

    def test_commit_failure_unstages(self, crlf_repo: tuple[Repo, Path]) -> None:
        """Test a failed commit returns False with the paths unstaged again."""
        repo, project_dir = crlf_repo
        with patch(
            f"{_MODULE}.commit_paths",
            return_value={"success": False, "error": "commit refused"},
        ):
            assert _clear_line_ending_dirt(project_dir, ["doc.md"]) is False

        assert _staged(repo) == ""

    def test_git_exception_unstages(self, crlf_repo: tuple[Repo, Path]) -> None:
        """Test an exception from the staged check is contained and unstages."""
        repo, project_dir = crlf_repo
        with patch(f"{_MODULE}.has_staged_changes", side_effect=RuntimeError("boom")):
            assert _clear_line_ending_dirt(project_dir, ["doc.md"]) is False

        assert _staged(repo) == ""
