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
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from git import Repo

from mcp_coder.mcp_workspace_git import get_full_status
from mcp_coder.workflows.review import handoff

# --- _flush_round_log ------------------------------------------------------


def test_flush_commits_then_pushes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The happy path commits the round log, then pushes it."""
    commit = MagicMock(return_value={"success": True, "commit_hash": "abc"})
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
    commit = MagicMock(return_value={"success": False, "error": "nothing to commit"})
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
    commit = MagicMock(return_value={"success": True, "commit_hash": "abc"})
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
    commit = MagicMock(return_value={"success": True, "commit_hash": "abc"})
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
    commit = MagicMock(
        return_value={
            "success": True,
            "commit_hash": None,
            "error": None,
            "error_category": None,
        }
    )
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path)

    push.assert_not_called()
    assert not any(r.levelno == logging.WARNING for r in caplog.records)


@pytest.mark.parametrize(
    "staging_succeeds", [True, False], ids=["staging-succeeds", "staging-fails"]
)
def test_flush_only_commits_just_the_log(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    staging_succeeds: bool,
) -> None:
    """``only=`` stages and commits that one path — never the whole tree.

    An arbitrarily dirty working tree can therefore never be committed under
    the round-log message. A failed staging commits nothing and warns.
    """
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    stage = MagicMock(return_value=staging_succeeds)
    commit_staged = MagicMock(
        return_value={
            "success": True,
            "commit_hash": "abc",
            "error": None,
            "error_category": None,
        }
    )
    commit_all = MagicMock(return_value={"success": True, "commit_hash": "abc"})
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "stage_specific_files", stage)
    monkeypatch.setattr(handoff, "commit_staged_files", commit_staged)
    monkeypatch.setattr(handoff, "commit_all_changes", commit_all)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path, only=log_path)

    stage.assert_called_once_with([log_path], tmp_path)
    commit_all.assert_not_called()
    if staging_succeeds:
        commit_staged.assert_called_once()
        assert commit_staged.call_args.args[1] == tmp_path
        push.assert_called_once_with(tmp_path)
        assert not any(r.levelno == logging.WARNING for r in caplog.records)
    else:
        commit_staged.assert_not_called()
        push.assert_not_called()
        assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_flush_only_commits_by_pathspec_when_index_holds_unrelated_entries(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A pre-staged file sends the commit down the pathspec route.

    ``commit_staged_files`` commits the whole index, so it would carry someone
    else's staged work under "Add review round log". The round log must still
    land — this is the handoff path — so it is committed by pathspec instead,
    leaving the unrelated entry staged and uncommitted.
    """
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    stage = MagicMock(return_value=True)
    commit_staged = MagicMock(return_value={"success": True, "commit_hash": "abc"})
    execute = MagicMock(
        return_value=SimpleNamespace(
            return_code=0, stdout="", stderr="", execution_error=None
        )
    )
    monkeypatch.setattr(
        handoff,
        "get_full_status",
        MagicMock(
            return_value={
                "staged": ["src/unrelated.py"],
                "modified": [],
                "untracked": [],
            }
        ),
    )
    monkeypatch.setattr(handoff, "stage_specific_files", stage)
    monkeypatch.setattr(handoff, "commit_staged_files", commit_staged)
    monkeypatch.setattr(handoff, "execute_command", execute)
    monkeypatch.setattr(handoff, "get_latest_commit_sha", MagicMock(return_value="abc"))
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "push_changes", push)

    handoff._flush_round_log(tmp_path, only=log_path)

    stage.assert_called_once_with([log_path], tmp_path)
    # Never the whole index - that is what would sweep src/unrelated.py in.
    commit_staged.assert_not_called()
    assert execute.call_args.args[0] == [
        "git",
        "commit",
        "-m",
        "Add review round log",
        "--",
        "pr_info/plan_review_log_1.md",
    ]
    push.assert_called_once_with(tmp_path)


def test_flush_only_pathspec_commit_failure_is_warned_and_not_pushed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A non-zero ``git commit -- <path>`` warns and skips the push."""
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    push = MagicMock(return_value=True)
    monkeypatch.setattr(
        handoff,
        "get_full_status",
        MagicMock(
            return_value={
                "staged": ["src/unrelated.py"],
                "modified": [],
                "untracked": [],
            }
        ),
    )
    monkeypatch.setattr(handoff, "stage_specific_files", MagicMock(return_value=True))
    monkeypatch.setattr(
        handoff,
        "execute_command",
        MagicMock(
            return_value=SimpleNamespace(
                return_code=1,
                stdout="",
                stderr="nothing to commit",
                execution_error=None,
            )
        ),
    )
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path, only=log_path)

    assert "nothing to commit" in caplog.text
    push.assert_not_called()


def test_flush_only_pathspec_reports_an_execution_error_without_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A timeout / missing git / permission error is named, not swallowed.

    ``execute_command`` reports those as ``return_code=1`` with both streams
    empty and the cause only in ``execution_error``; the warning must carry it
    rather than degrade to a bare exit code.
    """
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    push = MagicMock(return_value=True)
    monkeypatch.setattr(
        handoff,
        "get_full_status",
        MagicMock(
            return_value={
                "staged": ["src/unrelated.py"],
                "modified": [],
                "untracked": [],
            }
        ),
    )
    monkeypatch.setattr(handoff, "stage_specific_files", MagicMock(return_value=True))
    monkeypatch.setattr(
        handoff,
        "execute_command",
        MagicMock(
            return_value=SimpleNamespace(
                return_code=1,
                stdout="",
                stderr="",
                execution_error="Process timed out after 30 seconds",
            )
        ),
    )
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path, only=log_path)

    assert "Process timed out after 30 seconds" in caplog.text
    push.assert_not_called()


def test_commit_only_path_returns_a_short_commit_hash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The pathspec route reports the same 7-character hash as ``commit_staged_files``."""
    full_sha = "0123456789abcdef0123456789abcdef01234567"
    monkeypatch.setattr(
        handoff,
        "execute_command",
        MagicMock(
            return_value=SimpleNamespace(
                return_code=0, stdout="", stderr="", execution_error=None
            )
        ),
    )
    monkeypatch.setattr(
        handoff, "get_latest_commit_sha", MagicMock(return_value=full_sha)
    )

    result = handoff._commit_only_path(
        "Add review round log", tmp_path / "pr_info" / "plan_review_log_1.md", tmp_path
    )

    assert result["success"]
    assert result["commit_hash"] == "0123456"


def test_flush_only_unstages_the_log_when_the_commit_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A failed ``only=`` commit restores the log's index entry.

    Leaving it staged would be worse than not flushing at all: an untracked log
    does not stop a rebase, a staged one does.
    """
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    execute = MagicMock(
        return_value=SimpleNamespace(
            return_code=0, stdout="", stderr="", execution_error=None
        )
    )
    monkeypatch.setattr(
        handoff,
        "get_full_status",
        MagicMock(return_value={"staged": [], "modified": [], "untracked": []}),
    )
    monkeypatch.setattr(handoff, "stage_specific_files", MagicMock(return_value=True))
    monkeypatch.setattr(
        handoff,
        "commit_staged_files",
        MagicMock(return_value={"success": False, "error": "gpg failed to sign"}),
    )
    monkeypatch.setattr(handoff, "execute_command", execute)
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "push_changes", push)

    handoff._flush_round_log(tmp_path, only=log_path)

    assert execute.call_args.args[0] == [
        "git",
        "reset",
        "-q",
        "HEAD",
        "--",
        "pr_info/plan_review_log_1.md",
    ]
    push.assert_not_called()


def test_unstage_failure_warns_without_raising(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The restore is best-effort: a failing reset warns and never raises."""
    monkeypatch.setattr(
        handoff,
        "execute_command",
        MagicMock(
            return_value=SimpleNamespace(
                return_code=128,
                stdout="",
                stderr="fatal: ambiguous argument 'HEAD'",
                execution_error=None,
            )
        ),
    )

    with caplog.at_level(logging.WARNING):
        handoff._unstage_path(tmp_path / "pr_info" / "plan_review_log_1.md", tmp_path)

    assert "ambiguous argument" in caplog.text


@pytest.mark.git_integration
def test_failed_flush_leaves_the_log_unstaged_and_others_staged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Against a real repo: a failed ``only=`` flush adds no blocking state.

    The round-log path must end up untracked again — as it was before the
    flush — while the unrelated entry that sent the commit down the pathspec
    route stays staged.
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
        "_commit_only_path",
        MagicMock(
            return_value={
                "success": False,
                "commit_hash": None,
                "error": "pre-commit hook rejected the commit",
                "error_category": "commit_failed",
            }
        ),
    )
    monkeypatch.setattr(handoff, "push_changes", MagicMock(return_value=True))

    handoff._flush_round_log(tmp_path, only=log_path)

    status = get_full_status(tmp_path)
    assert status["staged"] == ["src/unrelated.py"]
    assert "pr_info/plan_review_log_1.md" in status["untracked"]
    assert log_path.read_bytes() == b"## Round 3\n"


def test_flush_only_proceeds_when_the_log_itself_is_already_staged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The round log already sitting in the index is not an unrelated entry."""
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    commit_staged = MagicMock(return_value={"success": True, "commit_hash": "abc"})
    monkeypatch.setattr(
        handoff,
        "get_full_status",
        MagicMock(
            return_value={
                "staged": ["pr_info/plan_review_log_1.md"],
                "modified": [],
                "untracked": [],
            }
        ),
    )
    monkeypatch.setattr(handoff, "stage_specific_files", MagicMock(return_value=True))
    monkeypatch.setattr(handoff, "commit_staged_files", commit_staged)
    monkeypatch.setattr(handoff, "push_changes", MagicMock(return_value=True))

    handoff._flush_round_log(tmp_path, only=log_path)

    commit_staged.assert_called_once()


def test_flush_push_false_commits_without_pushing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``push=False`` lands the commit locally and leaves the push to the caller."""
    commit = MagicMock(return_value={"success": True, "commit_hash": "abc"})
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    handoff._flush_round_log(tmp_path, push=False)

    commit.assert_called_once()
    push.assert_not_called()
