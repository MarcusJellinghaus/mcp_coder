"""Git-backed tests for the three deterministic guards in ``workflows/rebase.py``.

Covers ``_preflight``, ``_resolve_base_branch`` and
``_check_pr_info_absent_on_base``. ``_preflight`` and the pr_info guard touch a
real git repository (with a local ``origin`` remote), so they are marked
``git_integration``. ``_resolve_base_branch`` delegates detection to
``detect_base_branch``, which is patched here so the resolve tests stay
deterministic and offline.
"""

from pathlib import Path
from typing import Any

import pytest
from git import Repo

from mcp_coder.workflows import rebase as rebase_module
from mcp_coder.workflows.rebase import (
    _check_pr_info_absent_on_base,
    _preflight,
    _resolve_base_branch,
)

# Reuse the local git-config helper for consistent commit identities.
from tests.workflows.rebase.conftest import setup_git_config


@pytest.fixture
def feature_repo_with_origin(tmp_path: Path) -> tuple[Repo, Path]:
    """A clean feature branch backed by a local bare ``origin`` remote.

    Layout: ``main`` holds an initial commit and is pushed to a bare origin
    (so ``origin/main`` exists); HEAD is left on a fresh ``feature`` branch.
    """
    project_dir = tmp_path / "work"
    project_dir.mkdir()

    repo = Repo.init(project_dir)
    setup_git_config(repo)

    (project_dir / "README.md").write_text("# Test Project\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    # Force a deterministic default branch name regardless of git's config.
    repo.git.branch("-M", "main")

    bare = tmp_path / "origin.git"
    Repo.init(bare, bare=True)
    origin = repo.create_remote("origin", str(bare))
    origin.push(refspec="main:main")
    origin.fetch()

    repo.git.checkout("-b", "feature")

    return repo, project_dir


class TestResolveBaseBranch:
    """Tests for ``_resolve_base_branch`` (detection is patched)."""

    def test_explicit_arg_returned_verbatim(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An explicit ``base_branch_arg`` wins and skips detection entirely."""

        def _fail(*_args: Any, **_kwargs: Any) -> str:
            raise AssertionError("detect_base_branch must not be called")

        monkeypatch.setattr(rebase_module, "detect_base_branch", _fail)

        base, error = _resolve_base_branch(tmp_path, "develop")

        assert base == "develop"
        assert error is None

    def test_detected_main_accepted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A detected standard base ``main`` is accepted without an error."""
        monkeypatch.setattr(rebase_module, "detect_base_branch", lambda _p: "main")

        base, error = _resolve_base_branch(tmp_path, None)

        assert base == "main"
        assert error is None

    def test_non_standard_detected_errors(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A non-standard detected base is refused with a ``--base-branch`` hint."""
        monkeypatch.setattr(rebase_module, "detect_base_branch", lambda _p: "develop")

        base, error = _resolve_base_branch(tmp_path, None)

        assert base is None
        assert error is not None
        assert "--base-branch" in error

    def test_no_detection_errors(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failed detection (``None``) yields a ``--base-branch`` request."""
        monkeypatch.setattr(rebase_module, "detect_base_branch", lambda _p: None)

        base, error = _resolve_base_branch(tmp_path, None)

        assert base is None
        assert error is not None
        assert "--base-branch" in error


@pytest.mark.git_integration
class TestPreflight:
    """Tests for the ``_preflight`` composite guard."""

    def test_clean_feature_branch_with_origin_ok(
        self, feature_repo_with_origin: tuple[Repo, Path]
    ) -> None:
        """A clean feature branch with an ``origin`` remote passes pre-flight."""
        _, project_dir = feature_repo_with_origin

        assert _preflight(project_dir) is None

    def test_dirty_tree_rejected(
        self, feature_repo_with_origin: tuple[Repo, Path]
    ) -> None:
        """An uncommitted change fails pre-flight with a message."""
        _, project_dir = feature_repo_with_origin

        (project_dir / "dirty.txt").write_text("uncommitted\n")

        message = _preflight(project_dir)
        assert message is not None
        assert "clean" in message.lower()

    def test_on_main_rejected(
        self, feature_repo_with_origin: tuple[Repo, Path]
    ) -> None:
        """Sitting on ``main`` refuses the rebase."""
        repo, project_dir = feature_repo_with_origin

        repo.git.checkout("main")

        message = _preflight(project_dir)
        assert message is not None
        assert "main" in message.lower()

    def test_missing_origin_rejected(
        self, feature_repo_with_origin: tuple[Repo, Path]
    ) -> None:
        """Removing the ``origin`` remote fails pre-flight with a message."""
        repo, project_dir = feature_repo_with_origin

        repo.delete_remote(repo.remotes.origin)

        message = _preflight(project_dir)
        assert message is not None
        assert "origin" in message.lower()


@pytest.mark.git_integration
class TestCheckPrInfoAbsentOnBase:
    """Tests for the ``_check_pr_info_absent_on_base`` guard."""

    def test_absent_returns_none(
        self, feature_repo_with_origin: tuple[Repo, Path]
    ) -> None:
        """A base branch without ``pr_info/`` passes the guard."""
        _, project_dir = feature_repo_with_origin

        assert _check_pr_info_absent_on_base(project_dir, "main") is None

    def test_present_returns_error(
        self, feature_repo_with_origin: tuple[Repo, Path]
    ) -> None:
        """A base branch carrying a committed ``pr_info/`` file is refused."""
        repo, project_dir = feature_repo_with_origin

        # Build a base branch that contains a committed pr_info/ file.
        repo.git.checkout("main")
        pr_info_dir = project_dir / "pr_info"
        pr_info_dir.mkdir()
        (pr_info_dir / "notes.md").write_text("notes\n")
        repo.index.add(["pr_info/notes.md"])
        repo.index.commit("Add pr_info")
        repo.git.branch("-M", "withprinfo")
        repo.remotes.origin.push(refspec="withprinfo:withprinfo")
        repo.remotes.origin.fetch()

        message = _check_pr_info_absent_on_base(project_dir, "withprinfo")
        assert message is not None
        assert "pr_info" in message
