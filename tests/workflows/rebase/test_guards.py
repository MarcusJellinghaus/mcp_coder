"""Git-backed tests for the three deterministic guards in ``workflows/rebase.py``.

Covers ``_preflight``, ``_resolve_base_branch`` and
``_check_pr_info_absent_on_base``. ``_preflight`` and the pr_info guard touch a
real git repository (with a local ``origin`` remote), so they are marked
``git_integration``. ``_resolve_base_branch`` delegates detection to
``detect_base_branch_with_source``, which is patched here so the resolve tests stay
deterministic and offline.
"""

from pathlib import Path
from typing import Any

import pytest
from git import Repo

from mcp_coder.mcp_workspace_git import BaseBranchSource
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
            raise AssertionError("detect_base_branch_with_source must not be called")

        monkeypatch.setattr(rebase_module, "detect_base_branch_with_source", _fail)

        base, error = _resolve_base_branch(tmp_path, "develop")

        assert base == "develop"
        assert error is None

    def test_detected_main_accepted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A detected standard base ``main`` is accepted without an error."""
        monkeypatch.setattr(
            rebase_module,
            "detect_base_branch_with_source",
            lambda _p: ("main", BaseBranchSource.DEFAULT),
        )

        base, error = _resolve_base_branch(tmp_path, None)

        assert base == "main"
        assert error is None

    def test_issue_named_base_accepted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A non-standard base named in the issue is trusted."""
        monkeypatch.setattr(
            rebase_module,
            "detect_base_branch_with_source",
            lambda _p: ("epic/x", BaseBranchSource.ISSUE),
        )

        base, error = _resolve_base_branch(tmp_path, None)

        assert base == "epic/x"
        assert error is None

    @pytest.mark.parametrize(
        "source", [BaseBranchSource.PR, BaseBranchSource.MERGE_BASE]
    )
    def test_non_standard_heuristic_base_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        source: BaseBranchSource,
    ) -> None:
        """A non-standard base not named in the issue is refused."""
        monkeypatch.setattr(
            rebase_module,
            "detect_base_branch_with_source",
            lambda _p: ("develop", source),
        )

        base, error = _resolve_base_branch(tmp_path, None)

        assert base is None
        assert error is not None
        assert "--base-branch" in error
        assert "### Base Branch" in error
        assert "issue body is trusted" in error
        assert f"detected from {source.value}," in error

    def test_no_detection_errors(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failed detection (``None``) yields a ``--base-branch`` request."""
        monkeypatch.setattr(
            rebase_module, "detect_base_branch_with_source", lambda _p: None
        )

        base, error = _resolve_base_branch(tmp_path, None)

        assert base is None
        assert error is not None
        assert "--base-branch" in error


_CLEAN_STATUS: dict[str, Any] = {
    "success": True,
    "error": None,
    "returncode": 0,
    "stderr": "",
    "clean": True,
    "staged": [],
    "modified": [],
    "untracked": [],
}


@pytest.fixture
def preflight_passing(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Patch every ``_preflight`` shim call to a passing default."""
    monkeypatch.setattr(
        rebase_module, "get_working_tree_status", lambda _pd: dict(_CLEAN_STATUS)
    )
    monkeypatch.setattr(rebase_module, "is_rebase_in_progress", lambda _pd: False)
    monkeypatch.setattr(rebase_module, "get_current_branch_name", lambda _pd: "feature")
    monkeypatch.setattr(
        rebase_module, "get_remote_url", lambda _pd: "https://example.com/r.git"
    )
    monkeypatch.setattr(
        rebase_module,
        "check_formatter_config",
        lambda _pd, warn_legacy_key=False: None,
    )
    return monkeypatch


class TestPreflightMocked:
    """``_preflight`` against the mocked shim (fail-closed semantics)."""

    def test_all_pass(self, tmp_path: Path, preflight_passing: Any) -> None:
        """Every guard passing yields ``None``."""
        assert _preflight(tmp_path) is None

    def test_status_failure_not_clean(
        self, tmp_path: Path, preflight_passing: pytest.MonkeyPatch
    ) -> None:
        """A failed ``git status`` is never read as clean."""
        preflight_passing.setattr(
            rebase_module,
            "get_working_tree_status",
            lambda _pd: {**_CLEAN_STATUS, "success": False, "clean": False},
        )

        assert _preflight(tmp_path) == "Working tree not clean"

    def test_rebase_in_progress(
        self, tmp_path: Path, preflight_passing: pytest.MonkeyPatch
    ) -> None:
        """A rebase in progress is refused."""
        preflight_passing.setattr(
            rebase_module, "is_rebase_in_progress", lambda _pd: True
        )

        assert _preflight(tmp_path) == "Repository is mid-rebase/merge"

    def test_no_origin(
        self, tmp_path: Path, preflight_passing: pytest.MonkeyPatch
    ) -> None:
        """``get_remote_url`` returning ``None`` means no ``origin``."""
        preflight_passing.setattr(rebase_module, "get_remote_url", lambda _pd: None)

        assert _preflight(tmp_path) == "Remote 'origin' not found"


class TestCheckPrInfoAbsentOnBaseMocked:
    """``_check_pr_info_absent_on_base`` against a mocked ``list_tree``."""

    @staticmethod
    def _listing(success: bool, entries: list[str]) -> dict[str, Any]:
        return {
            "success": success,
            "error": None if success else "git ls-tree failed (exit 128)",
            "returncode": 0 if success else 128,
            "stderr": "",
            "entries": entries,
        }

    def test_listing_failure_is_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failed listing is an error, never read as absent."""
        calls: list[tuple[Path, str, str]] = []

        def _list(pd: Path, ref: str, path: str) -> dict[str, Any]:
            calls.append((pd, ref, path))
            return self._listing(False, [])

        monkeypatch.setattr(rebase_module, "list_tree", _list)

        message = _check_pr_info_absent_on_base(tmp_path, "main")

        assert message is not None
        assert message.startswith("Could not list pr_info/ on origin/main")
        assert "exit 128" in message
        assert calls == [(tmp_path, "origin/main", "pr_info")]

    def test_entries_present_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Any entry under ``pr_info/`` is refused."""
        monkeypatch.setattr(
            rebase_module,
            "list_tree",
            lambda _pd, _ref, _path: self._listing(True, ["pr_info/a.md"]),
        )

        assert (
            _check_pr_info_absent_on_base(tmp_path, "main")
            == "pr_info/ present on origin/main"
        )

    def test_empty_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An empty listing passes the guard."""
        monkeypatch.setattr(
            rebase_module, "list_tree", lambda _pd, _ref, _path: self._listing(True, [])
        )

        assert _check_pr_info_absent_on_base(tmp_path, "main") is None


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

    def test_formatter_config_error_returned(
        self,
        feature_repo_with_origin: tuple[Repo, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A formatter config error is the pre-flight message."""
        _, project_dir = feature_repo_with_origin
        calls: list[tuple[Path, bool]] = []

        def _check(pd: Path, warn_legacy_key: bool = False) -> str:
            calls.append((pd, warn_legacy_key))
            return "No formatter declared: add [tool.ruff.format]"

        monkeypatch.setattr(rebase_module, "check_formatter_config", _check)

        assert (
            _preflight(project_dir) == "No formatter declared: add [tool.ruff.format]"
        )
        assert calls == [(project_dir, True)]

    def test_formatter_config_ok_returns_none(
        self,
        feature_repo_with_origin: tuple[Repo, Path],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A resolvable formatter config lets pre-flight pass."""
        _, project_dir = feature_repo_with_origin
        monkeypatch.setattr(
            rebase_module,
            "check_formatter_config",
            lambda _pd, warn_legacy_key=False: None,
        )

        assert _preflight(project_dir) is None


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

    def test_missing_base_on_origin_returns_error(
        self, feature_repo_with_origin: tuple[Repo, Path]
    ) -> None:
        """A base absent on origin is an error, not \"pr_info/ absent\"."""
        _, project_dir = feature_repo_with_origin

        message = _check_pr_info_absent_on_base(project_dir, "no-such-branch")
        assert message is not None
        assert message.startswith("Could not list pr_info/ on origin/no-such-branch")
