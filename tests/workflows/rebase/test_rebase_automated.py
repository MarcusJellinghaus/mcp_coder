"""Tests for ``rebase_with_llm_fallback`` (git-only rebase, then the LLM rebase)."""

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from git import Repo

from mcp_coder.workflow_steps import rebase as rebase_step_module
from mcp_coder.workflow_steps.rebase import BranchCheck, RebaseOutcome, RebaseReason
from mcp_coder.workflows import rebase as rebase_module
from mcp_coder.workflows import rebase_automated as module
from mcp_coder.workflows.rebase import RebaseRunResult
from mcp_coder.workflows.rebase_automated import (
    AUTOMATED_EXCLUDED_MARKERS,
    _mcp_coder_dir_problem,
    rebase_with_llm_fallback,
)
from tests.conftest import BareRemote

from .conftest import setup_git_config

_CONFLICT = RebaseOutcome("conflict", "main", "abc1234", ("a.py", "b.py"))


@pytest.fixture
def mocks(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Patch every collaborator to the happy LLM path from a git-only conflict."""
    attempt = MagicMock(return_value=_CONFLICT)
    ignore = MagicMock(return_value=".mcp-coder/rebase_sessions/probe")
    seen_settings: list[str | None] = []

    def _run(*args: Any, **kwargs: Any) -> RebaseRunResult:
        settings = args[4] if len(args) > 4 else kwargs.get("settings_file")
        seen_settings.append(settings)
        if settings is not None:
            assert Path(settings).exists()
        return RebaseRunResult(0, "Rebased onto main")

    run = MagicMock(side_effect=_run)
    push = MagicMock(return_value=True)
    monkeypatch.setattr(module, "_attempt_rebase_and_push", attempt)
    monkeypatch.setattr(module, "git_check_ignore", ignore)
    monkeypatch.setattr(module, "run_rebase_workflow", run)
    monkeypatch.setattr(module, "push_changes", push)
    return SimpleNamespace(
        attempt=attempt, ignore=ignore, run=run, push=push, settings=seen_settings
    )


def _call(tmp_path: Path, settings_override: str | None = None) -> RebaseOutcome:
    return rebase_with_llm_fallback(
        tmp_path, "claude", ".mcp.json", settings_override=settings_override
    )


@pytest.mark.parametrize(
    "outcome",
    [
        RebaseOutcome("ok", "main", "abc1234"),
        RebaseOutcome("dirty_tree", files=("x.py",)),
        RebaseOutcome("no_base"),
        RebaseOutcome("base_missing", "main"),
        RebaseOutcome("push_failed", "main", "abc1234"),
    ],
)
def test_non_trigger_outcome_returned_unchanged(
    tmp_path: Path, mocks: SimpleNamespace, outcome: RebaseOutcome
) -> None:
    mocks.attempt.return_value = outcome

    assert _call(tmp_path) is outcome
    mocks.run.assert_not_called()
    mocks.ignore.assert_not_called()


@pytest.mark.parametrize("reason", ["conflict", "rebase_failed"])
def test_trigger_reasons_run_llm(
    tmp_path: Path, mocks: SimpleNamespace, reason: RebaseReason
) -> None:
    mocks.attempt.return_value = RebaseOutcome(reason, "develop", "abc1234")

    result = _call(tmp_path)

    assert result.reason == "ok"
    mocks.run.assert_called_once()
    args, kwargs = mocks.run.call_args
    assert args[0] == tmp_path
    assert args[1] == "claude"
    assert args[2] == "develop"
    assert args[3] == ".mcp.json"
    assert kwargs["markers"] == AUTOMATED_EXCLUDED_MARKERS
    # Default settings: a temp file that existed during the call, gone afterwards.
    assert mocks.settings[0] is not None
    assert not Path(mocks.settings[0]).exists()


def test_settings_override_passed_through(
    tmp_path: Path, mocks: SimpleNamespace
) -> None:
    override = str(tmp_path / "custom_settings.json")
    Path(override).write_text("{}", encoding="utf-8")

    _call(tmp_path, settings_override=override)

    assert mocks.settings == [override]
    assert Path(override).exists()


def test_llm_success_and_push_ok(tmp_path: Path, mocks: SimpleNamespace) -> None:
    result = _call(tmp_path)

    assert result.reason == "ok"
    assert result.ok
    assert result.files == ()
    assert result.base_branch == "main"
    assert result.llm_detail == "Rebased onto main"
    mocks.push.assert_called_once_with(tmp_path)


def test_llm_success_and_push_rejected(tmp_path: Path, mocks: SimpleNamespace) -> None:
    mocks.push.return_value = False

    result = _call(tmp_path)

    assert result.reason == "push_failed"
    assert result.files == ()
    assert result.llm_detail is not None
    assert "push was rejected" in result.llm_detail


def test_llm_push_rejected_flag(tmp_path: Path, mocks: SimpleNamespace) -> None:
    mocks.run.side_effect = None
    mocks.run.return_value = RebaseRunResult(
        2, "Force-push rejected", push_rejected=True
    )

    result = _call(tmp_path)

    assert result.reason == "push_failed"
    assert result.files == ()
    assert result.llm_detail == "Force-push rejected"
    mocks.push.assert_not_called()


@pytest.mark.parametrize(
    ("branch_check", "reason"),
    [("moved", "branch_moved"), ("error", "push_failed")],
)
def test_llm_branch_check_stop(
    tmp_path: Path,
    mocks: SimpleNamespace,
    branch_check: BranchCheck,
    reason: RebaseReason,
) -> None:
    mocks.run.side_effect = None
    mocks.run.return_value = RebaseRunResult(
        2, "Branch check failed", branch_check=branch_check
    )

    result = _call(tmp_path)

    assert result.reason == reason
    assert result.files == ()
    assert result.llm_detail == "Branch check failed"
    mocks.push.assert_not_called()


@pytest.mark.parametrize(
    "run_result",
    [
        RebaseRunResult(1, "Same file conflicted 3 times"),
        RebaseRunResult(2, "Pre-flight failed: dirty tree"),
    ],
)
def test_llm_failure_keeps_git_only_reason(
    tmp_path: Path, mocks: SimpleNamespace, run_result: RebaseRunResult
) -> None:
    mocks.run.side_effect = None
    mocks.run.return_value = run_result

    result = _call(tmp_path)

    assert result.reason == "conflict"
    assert result.files == ("a.py", "b.py")
    assert result.llm_detail == run_result.reason
    mocks.push.assert_not_called()


def test_llm_crash_keeps_git_only_reason(
    tmp_path: Path, mocks: SimpleNamespace
) -> None:
    mocks.run.side_effect = RuntimeError("session exploded")

    result = _call(tmp_path)

    assert result.reason == "conflict"
    assert result.llm_detail is not None
    assert result.llm_detail.startswith("LLM rebase crashed:")
    assert "session exploded" in result.llm_detail
    mocks.push.assert_not_called()


def test_guard_not_ignored_skips_llm(tmp_path: Path, mocks: SimpleNamespace) -> None:
    mocks.ignore.return_value = "No paths are ignored."

    result = _call(tmp_path)

    assert result.reason == "conflict"
    assert result.llm_detail is not None
    assert ".mcp-coder/" in result.llm_detail
    mocks.run.assert_not_called()


def test_guard_check_raises_skips_llm(tmp_path: Path, mocks: SimpleNamespace) -> None:
    mocks.ignore.side_effect = RuntimeError("git broke")

    result = _call(tmp_path)

    assert result.reason == "conflict"
    assert result.llm_detail is not None
    assert "git broke" in result.llm_detail
    mocks.run.assert_not_called()


# --- real git repo: the .mcp-coder/ ignore guard ---


def _init_repo(tmp_path: Path, gitignore: str | None) -> Path:
    project_dir = tmp_path / "repo"
    project_dir.mkdir()
    repo = Repo.init(project_dir)
    setup_git_config(repo)
    if gitignore is not None:
        (project_dir / ".gitignore").write_text(gitignore, encoding="utf-8")
    return project_dir


@pytest.mark.git_integration
@pytest.mark.parametrize("rule", ["/.mcp-coder/*\n", ".mcp-coder/\n"])
def test_guard_ignored_rules(tmp_path: Path, rule: str) -> None:
    project_dir = _init_repo(tmp_path, rule)
    assert not (project_dir / ".mcp-coder").exists()

    assert _mcp_coder_dir_problem(project_dir) is None


@pytest.mark.git_integration
def test_guard_no_rule(tmp_path: Path) -> None:
    project_dir = _init_repo(tmp_path, None)

    problem = _mcp_coder_dir_problem(project_dir)

    assert problem is not None
    assert ".mcp-coder/" in problem


@pytest.fixture
def real_git(bare_remote: BareRemote, monkeypatch: pytest.MonkeyPatch) -> BareRemote:
    """Stub base detection, preflight, checks and LLM setup; the rest is real git."""
    exclude = bare_remote.local_dir / ".git" / "info" / "exclude"
    exclude.write_text(".mcp-coder/\n", encoding="utf-8")
    monkeypatch.setattr(rebase_step_module, "detect_base_branch", lambda _pd: "main")
    monkeypatch.setattr(rebase_module, "_preflight", lambda _pd: None)
    monkeypatch.setattr(rebase_module, "prepare_llm_environment", lambda _pd: {})
    monkeypatch.setattr(rebase_module, "_run_all_checks", lambda _pd, _m: set())
    return bare_remote


def _commit_conflict_with_base(remote: BareRemote) -> str:
    """Add ``x.txt`` differently in ``local`` and on ``main``; return local HEAD."""
    (remote.local_dir / "x.txt").write_text("local\n", encoding="utf-8")
    remote.local.git.add("x.txt")
    remote.local.git.commit("-m", "local x")
    remote.move_base("x")
    return remote.local.head.commit.hexsha


def _stub_llm(
    remote: BareRemote,
    monkeypatch: pytest.MonkeyPatch,
    during: Callable[[], None] = lambda: None,
) -> MagicMock:
    """Make the LLM session resolve ``x.txt``, running ``during`` inside it."""

    def resolve(*_args: Any, **_kwargs: Any) -> tuple[str, str]:
        (remote.local_dir / "x.txt").write_text("merged\n", encoding="utf-8")
        during()
        return "", "session"

    llm = MagicMock(side_effect=resolve)
    monkeypatch.setattr(rebase_module, "_prompt_in_session", llm)
    return llm


@pytest.mark.git_integration
class TestBranchMovedRealGit:
    """A branch-check stop surfaces as ``branch_moved``, never as ``conflict``."""

    def test_foreign_commit_before_the_conflict(
        self, real_git: BareRemote, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pre_sha = _commit_conflict_with_base(real_git)
        foreign_sha = real_git.push_foreign("foreign1")
        llm = _stub_llm(real_git, monkeypatch)

        outcome = rebase_with_llm_fallback(real_git.local_dir, "claude", None)

        # One comparison, so that a failure shows all three together.
        assert (
            outcome.reason,
            real_git.remote_sha(),
            real_git.local.head.commit.hexsha,
        ) == ("branch_moved", foreign_sha, pre_sha)
        llm.assert_not_called()

    def test_foreign_commit_fetched_during_the_llm_session(
        self, real_git: BareRemote, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pre_sha = _commit_conflict_with_base(real_git)
        pushed: list[str] = []

        def foreign_push_and_fetch() -> None:
            pushed.append(real_git.push_foreign("foreign1"))
            real_git.local.git.fetch("origin")

        llm = _stub_llm(real_git, monkeypatch, foreign_push_and_fetch)

        outcome = rebase_with_llm_fallback(real_git.local_dir, "claude", None)

        llm.assert_called()
        assert (
            outcome.reason,
            real_git.remote_sha(),
            real_git.local.head.commit.hexsha,
        ) == ("branch_moved", pushed[0], pre_sha)
