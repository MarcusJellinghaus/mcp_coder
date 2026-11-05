"""Tests for the check that stops a rebase-and-push overwriting foreign commits.

Real-git tests compare against the literal reason so they can run before the
guard exists; unit tests read the shared text through the module at test time.
"""

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps import rebase as rebase_module
from mcp_coder.workflow_steps.rebase import RebaseOutcome, _attempt_rebase_and_push
from tests.conftest import BareRemote

_MODULE = "mcp_coder.workflow_steps.rebase"
_PRE_SHA = "a" * 40
_REMOTE_SHA = "b" * 40
_BASE_SHA = "c" * 40
_RESET_OK = {"success": True, "stderr": "", "error": None}
_RESET_FAILED = {"success": False, "stderr": "boom", "error": "boom"}


@pytest.fixture
def base_is_main() -> Iterator[None]:
    """Make ``main`` the detected base; everything else runs on real git."""
    with patch(f"{_MODULE}.detect_base_branch", return_value="main"):
        yield


def _local_head(remote: BareRemote) -> str:
    """Return the SHA of HEAD in the ``local`` clone."""
    return remote.local.head.commit.hexsha


@pytest.mark.git_integration
@pytest.mark.usefixtures("base_is_main")
class TestMustStop:
    """The branch has commits this checkout does not have: nothing is pushed."""

    @staticmethod
    def _assert_stopped(remote: BareRemote, pre_sha: str, remote_before: str) -> None:
        """Run the attempt and assert it stopped and left everything in place."""
        outcome = _attempt_rebase_and_push(remote.local_dir)

        # One comparison, so that a failure shows the outcome and the remote together.
        assert (outcome.reason, remote.remote_sha(), _local_head(remote)) == (
            "branch_moved",
            remote_before,
            pre_sha,
        )

    def test_foreign_commit_with_unpushed_local_commit(
        self, bare_remote: BareRemote
    ) -> None:
        """Test a foreign commit stops a checkout that has its own commit."""
        pre_sha = bare_remote.commit_local("local1")
        foreign_sha = bare_remote.push_foreign("foreign1")

        self._assert_stopped(bare_remote, pre_sha, foreign_sha)

    def test_foreign_commit_with_moved_base_resets_the_rebase(
        self, bare_remote: BareRemote
    ) -> None:
        """Test the rebase, which really moves HEAD here, is undone."""
        pre_sha = bare_remote.commit_local("local1")
        foreign_sha = bare_remote.push_foreign("foreign1")
        bare_remote.move_base("base2")

        self._assert_stopped(bare_remote, pre_sha, foreign_sha)

    def test_stale_checkout_without_local_commits(
        self, bare_remote: BareRemote
    ) -> None:
        """Test a checkout that is merely behind does not push itself back."""
        pre_sha = _local_head(bare_remote)
        foreign_sha = bare_remote.push_foreign("foreign1")

        self._assert_stopped(bare_remote, pre_sha, foreign_sha)

    def test_remote_rewritten_by_someone_elses_rebase(
        self, bare_remote: BareRemote
    ) -> None:
        """Test a rewritten remote stops, even though no new file appeared."""
        pre_sha = _local_head(bare_remote)
        rewritten_sha = bare_remote.rewrite_remote()

        self._assert_stopped(bare_remote, pre_sha, rewritten_sha)

    def test_tag_named_like_the_remote_branch(self, bare_remote: BareRemote) -> None:
        """Test a tag ``origin/feature`` at local HEAD cannot pass the check."""
        pre_sha = _local_head(bare_remote)
        bare_remote.local.create_tag("origin/feature")
        foreign_sha = bare_remote.push_foreign("foreign1")

        self._assert_stopped(bare_remote, pre_sha, foreign_sha)


@pytest.mark.git_integration
@pytest.mark.usefixtures("base_is_main")
class TestMustPush:
    """The remote holds nothing this checkout lacks: the push goes ahead."""

    def test_normal_rebase_after_base_moved(self, bare_remote: BareRemote) -> None:
        """Test a rebase that rewrites local commits still pushes."""
        pre_sha = bare_remote.commit_local("local1")
        base_sha = bare_remote.move_base("base2")

        outcome = _attempt_rebase_and_push(bare_remote.local_dir)

        assert outcome.reason == "ok"
        assert _local_head(bare_remote) != pre_sha
        assert bare_remote.remote_sha() == _local_head(bare_remote)
        assert base_sha in bare_remote.remote_log()

    def test_local_commit_ahead_with_nothing_to_rebase(
        self, bare_remote: BareRemote
    ) -> None:
        """Test a commit ahead of the remote pushes (review's round-log case)."""
        pre_sha = bare_remote.commit_local("local1")

        outcome = _attempt_rebase_and_push(bare_remote.local_dir)

        assert outcome.reason == "ok"
        assert bare_remote.remote_sha() == pre_sha

    def test_never_pushed_branch(self, bare_remote: BareRemote) -> None:
        """Test the check is skipped for a branch origin does not have yet."""
        bare_remote.local.git.checkout("-b", "fresh")
        pre_sha = bare_remote.commit_local("local1")

        outcome = _attempt_rebase_and_push(bare_remote.local_dir)

        assert outcome.reason == "ok"
        assert bare_remote.remote_sha("fresh") == pre_sha


@dataclass(frozen=True)
class _Mocks:
    """The collaborators of ``_attempt_rebase_and_push`` a test may override."""

    latest_sha: MagicMock
    rebase: MagicMock
    branch_name: MagicMock
    merge_base: MagicMock
    push: MagicMock
    reset: MagicMock


def _remote_sha_for(_project_dir: Path, branch: str) -> str:
    """Answer both lookups: ``_base_sha`` asks for main, the check for feature."""
    return _BASE_SHA if branch == "main" else _REMOTE_SHA


@pytest.fixture
def mocks() -> Iterator[_Mocks]:
    """Mock every collaborator so that a default run passes the check and pushes."""
    clean: dict[str, list[str]] = {"staged": [], "modified": [], "untracked": []}
    with (
        patch(f"{_MODULE}.get_full_status", return_value=clean),
        patch(f"{_MODULE}.detect_base_branch", return_value="main"),
        patch(f"{_MODULE}.check_base_branch_on_origin", return_value=None),
        patch(f"{_MODULE}.get_remote_branch_commit_sha", _remote_sha_for),
        patch(f"{_MODULE}.get_latest_commit_sha", return_value=_PRE_SHA) as latest_sha,
        patch(f"{_MODULE}.rebase_onto_branch", return_value=True) as rebase,
        patch(f"{_MODULE}.get_current_branch_name", return_value="feature") as branch,
        patch(f"{_MODULE}.git_merge_base", return_value="true") as merge_base,
        patch(f"{_MODULE}.push_changes", return_value=True) as push,
        patch(f"{_MODULE}.reset_hard", return_value=_RESET_OK) as reset,
    ):
        yield _Mocks(latest_sha, rebase, branch, merge_base, push, reset)


class TestGuardUnit:
    """The guard's decisions, with every collaborator mocked."""

    def _assert_stopped(self, mocks: _Mocks, project_dir: Path, reason: str) -> None:
        """Run the attempt and assert ``reason``, no push and the reset's target."""
        outcome = _attempt_rebase_and_push(project_dir)

        assert outcome == RebaseOutcome(reason, "main", _BASE_SHA[:7])  # type: ignore[arg-type]
        assert outcome.ok is False
        assert outcome.files == ()
        mocks.push.assert_not_called()
        mocks.reset.assert_called_once_with(project_dir, _PRE_SHA)

    def test_merge_base_raises(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Test a check that raises is push_failed and undoes the rebase."""
        mocks.merge_base.side_effect = RuntimeError("boom")

        self._assert_stopped(mocks, tmp_path, "push_failed")

    def test_branch_name_unavailable(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Test an unreadable branch name is push_failed and undoes the rebase."""
        mocks.branch_name.return_value = None

        self._assert_stopped(mocks, tmp_path, "push_failed")

    def test_merge_base_unexpected_text(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Test an unexpected answer is push_failed and undoes the rebase."""
        mocks.merge_base.return_value = "No common ancestor found"

        self._assert_stopped(mocks, tmp_path, "push_failed")

    def test_branch_moved(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Test a remote that is no ancestor is branch_moved and undoes the rebase."""
        mocks.merge_base.return_value = "false"

        self._assert_stopped(mocks, tmp_path, "branch_moved")

    def test_reset_fails_on_moved(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Test a failed reset keeps branch_moved and still pushes nothing."""
        mocks.merge_base.return_value = "false"
        mocks.reset.return_value = _RESET_FAILED

        self._assert_stopped(mocks, tmp_path, "branch_moved")

    def test_reset_fails_on_error(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Test a failed reset keeps push_failed and still pushes nothing."""
        mocks.merge_base.side_effect = RuntimeError("boom")
        mocks.reset.return_value = _RESET_FAILED

        self._assert_stopped(mocks, tmp_path, "push_failed")

    def test_pre_rebase_head_unavailable(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Test an unreadable HEAD stops before the rebase can start."""
        mocks.latest_sha.return_value = None

        outcome = _attempt_rebase_and_push(tmp_path)

        assert outcome == RebaseOutcome("rebase_failed", "main", _BASE_SHA[:7])
        mocks.rebase.assert_not_called()
        mocks.push.assert_not_called()

    def test_moved_warns_with_reason_and_next_step(
        self, mocks: _Mocks, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test the warning carries the shared reason and next step."""
        mocks.merge_base.return_value = "false"

        with caplog.at_level(logging.WARNING):
            _attempt_rebase_and_push(tmp_path)

        warnings = [
            r.getMessage() for r in caplog.records if r.levelno == logging.WARNING
        ]
        assert any(
            rebase_module.BRANCH_MOVED_REASON in m
            and rebase_module.BRANCH_MOVED_NEXT_STEP in m
            for m in warnings
        )
        mocks.reset.assert_called_once_with(tmp_path, _PRE_SHA)

    def test_merge_base_compares_shas_never_names(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """Test the check passes the remote and pre-rebase SHAs."""
        _attempt_rebase_and_push(tmp_path)

        mocks.merge_base.assert_called_once_with(
            tmp_path, ["--is-ancestor", _REMOTE_SHA, _PRE_SHA]
        )
        mocks.push.assert_called_once_with(tmp_path, force_with_lease=True)
        mocks.reset.assert_not_called()
