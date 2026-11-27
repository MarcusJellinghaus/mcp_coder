"""``round_applied``: a review round counts as applied only for non-log changes.

Review logs (``pr_info/*_review_log_*.md``) change on every round and may be
reformatted, so they never make a round "applied". The measure is taken right
after the round's commit and push, before ``_after_steps`` rebases the branch.
"""

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import git
import pytest

from mcp_coder.workflows.review import steps
from mcp_coder.workflows.review.steps import round_applied
from tests.workflows.review.conftest import _DISMISS, _TASKS, _resp, _reviewer, _run

_LOG_NAME = "implementation_review_log_1.md"

# --- unit tests (git_diff patched) ------------------------------------------


def test_unknown_sha_counts_as_applied_without_diffing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``sha_before=None`` -> True, and ``git_diff`` is never called."""
    diff = MagicMock()
    monkeypatch.setattr(steps, "git_diff", diff)

    assert round_applied(tmp_path, None) is True
    diff.assert_not_called()


def test_empty_diff_is_a_no_op(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``"No changes found"`` -> False."""
    monkeypatch.setattr(steps, "git_diff", MagicMock(return_value="No changes found"))

    assert round_applied(tmp_path, "abc") is False


def test_only_review_logs_changed_is_a_no_op(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A diff touching only review logs -> False."""
    monkeypatch.setattr(
        steps,
        "git_diff",
        MagicMock(
            return_value=(
                "pr_info/implementation_review_log_1.md\npr_info/plan_review_log_2.md"
            )
        ),
    )

    assert round_applied(tmp_path, "abc") is False


def test_a_non_log_file_makes_the_round_applied(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A review log plus a source file -> True."""
    monkeypatch.setattr(
        steps,
        "git_diff",
        MagicMock(return_value="pr_info/implementation_review_log_1.md\nsrc/a.py"),
    )

    assert round_applied(tmp_path, "abc") is True


def test_git_error_counts_as_applied_with_one_warning(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A raising ``git_diff`` -> True, with exactly one WARNING."""
    monkeypatch.setattr(steps, "git_diff", MagicMock(side_effect=RuntimeError("boom")))

    with caplog.at_level(logging.WARNING):
        assert round_applied(tmp_path, "abc") is True

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1


# --- real git --------------------------------------------------------------


@pytest.mark.git_integration
def test_real_git_ignores_logs_and_counts_source_changes(
    git_repo: tuple[git.Repo, Path],
) -> None:
    """Committed log changes are a no-op; uncommitted or committed source is not."""
    repo, project_dir = git_repo
    (project_dir / "a.py").write_text("x = 1\n", encoding="utf-8")
    repo.index.add(["a.py"])
    repo.index.commit("initial")
    sha = repo.head.commit.hexsha

    log = project_dir / "pr_info" / _LOG_NAME
    log.parent.mkdir()
    log.write_text("# Review log\n- round 1\n", encoding="utf-8")
    repo.index.add([f"pr_info/{_LOG_NAME}"])
    repo.index.commit("add review log")
    assert round_applied(project_dir, sha) is False

    log.write_text("# Review log\n\n- round 1\n", encoding="utf-8")
    repo.index.add([f"pr_info/{_LOG_NAME}"])
    repo.index.commit("reformat review log")
    assert round_applied(project_dir, sha) is False

    (project_dir / "a.py").write_text("x = 2\n", encoding="utf-8")
    assert round_applied(project_dir, sha) is True

    repo.index.add(["a.py"])
    repo.index.commit("change a.py")
    assert round_applied(project_dir, sha) is True


# --- core loop (env fixture) -------------------------------------------------


def test_no_op_round_is_measured_before_the_rebase(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """``round_applied`` runs before the rebase; the round-1 log reads no-op."""
    order: list[str] = []

    def _applied(*_a: Any) -> bool:
        order.append("round_applied")
        return False

    def _rebase(*_a: Any, **_k: Any) -> Any:
        order.append("rebase")
        return env.attempt_rebase_and_push.return_value

    env.round_applied.side_effect = _applied
    env.attempt_rebase_and_push.side_effect = _rebase
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),
        _reviewer(),
        _resp(_DISMISS),
    ]

    assert _run(tmp_path) == 0

    assert order.index("round_applied") < order.index("rebase")
    log = (tmp_path / "pr_info" / _LOG_NAME).read_text(encoding="utf-8")
    assert "no-op" in log
    assert "applied" not in log


def test_applied_round_is_logged_as_applied(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """The default ``round_applied=True`` writes ``applied`` to the round-1 log."""
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer(session_id="rev-1"),
        _reviewer(),
        _resp(_DISMISS),
    ]

    assert _run(tmp_path) == 0

    log = (tmp_path / "pr_info" / _LOG_NAME).read_text(encoding="utf-8")
    assert "applied" in log
