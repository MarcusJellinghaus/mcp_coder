"""Tests for rejected-push detection in ``push_changes``."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import git
import pytest

from mcp_coder.workflow_steps.commit import (
    PUSH_REJECTED_ERROR,
    PushRejectedError,
    push_changes,
)
from tests.conftest import setup_git_config

GIT_PUSH = "mcp_coder.workflow_steps.commit.git_push"
REJECTED_HINT = (
    "hint: Updates were rejected because the remote contains work that you do\n"
    "hint: not have locally."
)


def _git_error(stderr_body: str, branch: str = "x") -> str:
    """Build an error string shaped like a stringified ``GitCommandError``."""
    return (
        "Git error during push: Cmd('git') failed due to: exit code(1)\n"
        f"  cmdline: git push origin {branch}\n"
        "  stderr: 'To https://github.com/owner/repo.git\n"
        f"{stderr_body}\n"
        "error: failed to push some refs to 'https://github.com/owner/repo.git'\n"
        f"{REJECTED_HINT}'"
    )


class TestPushRejectedDetection:
    """``push_changes`` with ``git_push`` patched."""

    @pytest.mark.parametrize("reason", ["fetch first", "non-fast-forward"])
    @patch(GIT_PUSH)
    def test_branch_moved_raises_with_status_line(
        self, mock_git_push: MagicMock, reason: str, tmp_path: Path
    ) -> None:
        """Both rejection reasons raise, carrying the fixed sentence and the line."""
        status_line = f"! [rejected]        x -> x ({reason})"
        mock_git_push.return_value = {
            "success": False,
            "error": _git_error(f" {status_line}"),
        }

        with pytest.raises(PushRejectedError) as exc_info:
            push_changes(tmp_path, raise_on_rejected=True)

        assert str(exc_info.value) == f"{PUSH_REJECTED_ERROR}: {status_line}"

    @pytest.mark.parametrize(
        "error",
        [
            pytest.param(
                _git_error(" ! [remote rejected] x -> x (pre-receive hook declined)"),
                id="remote_rejected",
            ),
            pytest.param(
                _git_error(
                    "remote:  ! [rejected] x -> x (fetch first)\n"
                    " ! [remote rejected] x -> x (pre-receive hook declined)"
                ),
                id="hook_echo",
            ),
            pytest.param(
                _git_error(
                    "fatal: unable to access: Could not resolve host",
                    branch="fix/rejected-push",
                ),
                id="network_failure_branch_with_rejected",
            ),
            pytest.param(
                _git_error(
                    "fatal: unable to access: Could not resolve host",
                    branch="fix/non-fast-forward",
                ),
                id="network_failure_branch_with_non_fast_forward",
            ),
            pytest.param(
                _git_error("fatal: Authentication failed"),
                id="authentication_failure",
            ),
        ],
    )
    @patch(GIT_PUSH)
    def test_other_failures_return_false(
        self, mock_git_push: MagicMock, error: str, tmp_path: Path
    ) -> None:
        """Failures that are not a moved branch keep returning False."""
        mock_git_push.return_value = {"success": False, "error": error}

        assert push_changes(tmp_path, raise_on_rejected=True) is False

    @patch(GIT_PUSH)
    def test_rejected_without_keyword_returns_false(
        self, mock_git_push: MagicMock, tmp_path: Path
    ) -> None:
        """Without the opt-in keyword a rejected push returns False."""
        mock_git_push.return_value = {
            "success": False,
            "error": _git_error(" ! [rejected]        x -> x (fetch first)"),
        }

        assert push_changes(tmp_path) is False

    @patch(GIT_PUSH)
    def test_git_push_exception_returns_false(
        self, mock_git_push: MagicMock, tmp_path: Path
    ) -> None:
        """An exception from ``git_push`` returns False."""
        mock_git_push.side_effect = RuntimeError(
            " ! [rejected]        x -> x (fetch first)"
        )

        assert push_changes(tmp_path, raise_on_rejected=True) is False

    @patch(GIT_PUSH)
    def test_success_returns_true(
        self, mock_git_push: MagicMock, tmp_path: Path
    ) -> None:
        """A successful push returns True with the keyword set."""
        mock_git_push.return_value = {"success": True, "error": None}

        assert push_changes(tmp_path, raise_on_rejected=True) is True


def _commit_file(repo: git.Repo, project_dir: Path, name: str) -> git.Commit:
    """Commit a new file and return the commit."""
    (project_dir / name).write_text(f"{name}\n", encoding="utf-8")
    repo.index.add([name])
    return repo.index.commit(f"Add {name}")


@pytest.fixture
def bare_with_two_clones(
    tmp_path: Path,
) -> tuple[git.Repo, tuple[git.Repo, Path], tuple[git.Repo, Path]]:
    """A bare ``origin`` on ``main`` and two clones at the same commit."""
    bare = git.Repo.init(tmp_path / "origin.git", bare=True)
    bare.git.symbolic_ref("HEAD", "refs/heads/main")

    dir_a = tmp_path / "clone_a"
    repo_a = git.Repo.clone_from(str(tmp_path / "origin.git"), dir_a)
    setup_git_config(repo_a)
    _commit_file(repo_a, dir_a, "initial.txt")
    repo_a.git.branch("-M", "main")
    repo_a.git.push("origin", "main")

    dir_b = tmp_path / "clone_b"
    repo_b = git.Repo.clone_from(str(tmp_path / "origin.git"), dir_b)
    setup_git_config(repo_b)

    return bare, (repo_a, dir_a), (repo_b, dir_b)


@pytest.mark.git_integration
def test_real_git_rejection_is_detected(
    bare_with_two_clones: tuple[git.Repo, tuple[git.Repo, Path], tuple[git.Repo, Path]],
) -> None:
    """Real git's error text raises for both reasons and leaves the remote alone."""
    bare, (repo_a, dir_a), (repo_b, dir_b) = bare_with_two_clones

    tip_b = _commit_file(repo_b, dir_b, "from_b.txt")
    repo_b.git.push("origin", "main")
    _commit_file(repo_a, dir_a, "from_a.txt")

    with pytest.raises(PushRejectedError, match=r"\(fetch first\)"):
        push_changes(dir_a, raise_on_rejected=True)

    repo_a.git.fetch("origin")

    with pytest.raises(PushRejectedError, match=r"\(non-fast-forward\)"):
        push_changes(dir_a, raise_on_rejected=True)

    assert bare.commit("main").hexsha == tip_b.hexsha
