"""Step 6 — handoff flush tests (``_flush_round_log`` + its commit helpers).

These deterministic tests exercise the round-log flush in isolation with the
git externals mocked. ``_flush_round_log`` must be best-effort (never raise,
warn on a falsy or raised result, skip the push when the commit did not
succeed), and with ``only=`` it must commit that one path and nothing else.

``_route_to_human`` and ``_fail``, the callers of this helper, are covered in
``test_handoff_route.py``.
"""

import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from git import Repo

from mcp_coder.mcp_workspace_git import get_full_status
from mcp_coder.workflows.review import handoff


def _commit_result(
    success: bool = True,
    commit_hash: str | None = "abc1234",
    error: str | None = None,
    error_category: str | None = None,
) -> dict[str, Any]:
    """Build a full ``CommitResult``-shaped mock return value."""
    return {
        "success": success,
        "commit_hash": commit_hash,
        "error": error,
        "error_category": error_category,
        "returncode": 0 if success else 1,
        "stderr": "",
    }


# --- _flush_round_log ------------------------------------------------------


def test_flush_commits_then_pushes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The happy path commits the round log, then pushes it."""
    commit = MagicMock(return_value=_commit_result())
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    handoff._flush_round_log(tmp_path)

    commit.assert_called_once()
    assert commit.call_args.args[1] == tmp_path
    push.assert_called_once_with(tmp_path)


def test_flush_falsy_commit_warns_and_skips_push(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A falsy commit result warns and does not push (nothing landed to push)."""
    commit = MagicMock(
        return_value=_commit_result(
            success=False,
            commit_hash=None,
            error="hook rejected",
            error_category="commit_failed",
        )
    )
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path)  # must not raise

    push.assert_not_called()
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_flush_falsy_push_warns(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A falsy push return warns but does not raise."""
    commit = MagicMock(return_value=_commit_result())
    push = MagicMock(return_value=False)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path)

    push.assert_called_once()
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_flush_swallows_commit_raise(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """An unexpected raise from the commit is swallowed (warned, not propagated)."""
    commit = MagicMock(side_effect=RuntimeError("boom"))
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path)  # must not raise

    push.assert_not_called()
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_flush_swallows_push_raise(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """An unexpected raise from the push is swallowed too."""
    commit = MagicMock(return_value=_commit_result())
    push = MagicMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path)  # must not raise

    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_flush_no_commit_skips_push(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A successful commit that committed nothing skips the push, quietly.

    ``commit_all_changes`` reports an empty tree as ``success: True`` with
    ``commit_hash: None``; there is nothing to push and nothing to warn about
    (unlike the ``success: False`` path above, which does warn).
    """
    commit = MagicMock(return_value=_commit_result(commit_hash=None))
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path)

    push.assert_not_called()
    assert not any(r.levelno == logging.WARNING for r in caplog.records)


@pytest.mark.parametrize("push_enabled", [True, False], ids=["push", "no-push"])
def test_flush_only_commits_just_the_log(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    push_enabled: bool,
) -> None:
    """``only=`` stages that one path, then commits it alone via ``commit_paths``.

    An arbitrarily dirty working tree - staged or not - can therefore never be
    committed under the round-log message.
    """
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    stage = MagicMock(return_value=True)
    commit_paths = MagicMock(return_value=_commit_result())
    commit_all = MagicMock(return_value=_commit_result())
    unstage = MagicMock()
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "stage_specific_files", stage)
    monkeypatch.setattr(handoff, "commit_paths", commit_paths)
    monkeypatch.setattr(handoff, "commit_all_changes", commit_all)
    monkeypatch.setattr(handoff, "unstage_paths", unstage)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path, only=log_path, push=push_enabled)

    stage.assert_called_once_with([log_path], tmp_path)
    commit_paths.assert_called_once_with("Add review round log", [log_path], tmp_path)
    commit_all.assert_not_called()
    unstage.assert_not_called()
    if push_enabled:
        push.assert_called_once_with(tmp_path)
    else:
        push.assert_not_called()
    assert not any(r.levelno == logging.WARNING for r in caplog.records)


def test_flush_only_staging_failure_commits_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A failed staging warns and makes no commit call at all."""
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    commit_paths = MagicMock(return_value=_commit_result())
    commit_all = MagicMock(return_value=_commit_result())
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "stage_specific_files", MagicMock(return_value=False))
    monkeypatch.setattr(handoff, "commit_paths", commit_paths)
    monkeypatch.setattr(handoff, "commit_all_changes", commit_all)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path, only=log_path)

    commit_paths.assert_not_called()
    commit_all.assert_not_called()
    push.assert_not_called()
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_flush_only_nothing_to_commit_is_quiet(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """``nothing_to_commit`` is not a failure: no warning, no unstage, no push."""
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    unstage = MagicMock()
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "stage_specific_files", MagicMock(return_value=True))
    monkeypatch.setattr(
        handoff,
        "commit_paths",
        MagicMock(
            return_value=_commit_result(
                success=False,
                commit_hash=None,
                error="Nothing to commit for the given paths",
                error_category="nothing_to_commit",
            )
        ),
    )
    monkeypatch.setattr(handoff, "unstage_paths", unstage)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.DEBUG, logger=handoff.__name__):
        handoff._flush_round_log(tmp_path, only=log_path)

    assert not any(r.levelno == logging.WARNING for r in caplog.records)
    assert "nothing to commit" in caplog.text
    unstage.assert_not_called()
    push.assert_not_called()


def test_flush_only_unstages_the_log_when_the_commit_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A failed ``only=`` commit warns and restores the log's index entry.

    Leaving it staged would be worse than not flushing at all: an untracked log
    does not stop a rebase, a staged one does.
    """
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    unstage = MagicMock(
        return_value={"success": True, "error": None, "returncode": 0, "stderr": ""}
    )
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "stage_specific_files", MagicMock(return_value=True))
    monkeypatch.setattr(
        handoff,
        "commit_paths",
        MagicMock(
            return_value=_commit_result(
                success=False,
                commit_hash=None,
                error="gpg failed to sign",
                error_category="commit_failed",
            )
        ),
    )
    monkeypatch.setattr(handoff, "unstage_paths", unstage)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path, only=log_path)

    assert "gpg failed to sign" in caplog.text
    unstage.assert_called_once_with([log_path], tmp_path)
    push.assert_not_called()


def test_unstage_failure_warns_without_raising(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The restore is best-effort: a failing unstage warns and never raises."""
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    monkeypatch.setattr(
        handoff,
        "unstage_paths",
        MagicMock(
            return_value={
                "success": False,
                "error": "git reset failed (exit 128)",
                "returncode": 128,
                "stderr": "fatal: ambiguous argument 'HEAD'",
            }
        ),
    )

    with caplog.at_level(logging.WARNING):
        handoff._unstage_path(log_path, tmp_path)

    assert "ambiguous argument" in caplog.text
    assert str(log_path) in caplog.text


def test_unstage_failure_without_stderr_reports_the_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A validation failure (no git ran, ``stderr`` None) still names a cause."""
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    monkeypatch.setattr(
        handoff,
        "unstage_paths",
        MagicMock(
            return_value={
                "success": False,
                "error": "path is outside the project",
                "returncode": None,
                "stderr": None,
            }
        ),
    )

    with caplog.at_level(logging.WARNING):
        handoff._unstage_path(log_path, tmp_path)

    assert "path is outside the project" in caplog.text


@pytest.mark.git_integration
def test_failed_flush_leaves_the_log_unstaged_and_others_staged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Against a real repo: a failed ``only=`` flush adds no blocking state.

    The round-log path must end up untracked again — as it was before the
    flush — while an unrelated staged entry stays staged.
    """
    repo = Repo.init(tmp_path)
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")
        config.set_value("commit", "gpgsign", "false")
    (tmp_path / "README.md").write_bytes(b"# Test\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "unrelated.py").write_bytes(b"x = 1\n")
    repo.index.add(["src/unrelated.py"])
    repo.index.write()

    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    log_path.parent.mkdir()
    log_path.write_bytes(b"## Round 3\n")

    # Stands in for the hook rejection / signing failure the fix is about; the
    # staging before it and the unstaging after it are the real thing.
    monkeypatch.setattr(
        handoff,
        "commit_paths",
        MagicMock(
            return_value=_commit_result(
                success=False,
                commit_hash=None,
                error="pre-commit hook rejected the commit",
                error_category="commit_failed",
            )
        ),
    )
    monkeypatch.setattr(handoff, "push_changes", MagicMock(return_value=True))

    handoff._flush_round_log(tmp_path, only=log_path)

    status = get_full_status(tmp_path)
    assert status["staged"] == ["src/unrelated.py"]
    assert "pr_info/plan_review_log_1.md" in status["untracked"]
    assert log_path.read_bytes() == b"## Round 3\n"


def test_flush_push_false_commits_without_pushing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``push=False`` lands the commit locally and leaves the push to the caller."""
    commit = MagicMock(return_value=_commit_result())
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    handoff._flush_round_log(tmp_path, push=False)

    commit.assert_called_once()
    push.assert_not_called()
