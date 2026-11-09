"""Tests for the checks that stop ``run_rebase_workflow`` on a moved branch."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflows import rebase as rebase_module
from mcp_coder.workflows.rebase import run_rebase_workflow
from tests.conftest import BareRemote
from tests.workflows.rebase.conftest import _run


class TestFirstCheck:
    """A stop before the baseline checks: nothing has changed, so no restore."""

    def test_moved_stops_before_anything_changes(
        self, patched: SimpleNamespace, tmp_path: Path
    ) -> None:
        patched.merge_base.return_value = "false"

        result = _run(tmp_path)

        assert (result.exit_code, result.branch_check) == (2, "moved")
        patched.all_checks.assert_not_called()
        patched.reset.assert_not_called()
        patched.push.assert_not_called()

    def test_error_stops_before_anything_changes(
        self, patched: SimpleNamespace, tmp_path: Path
    ) -> None:
        patched.merge_base.side_effect = RuntimeError("boom")

        result = _run(tmp_path)

        assert (result.exit_code, result.branch_check) == (2, "error")
        patched.all_checks.assert_not_called()
        patched.reset.assert_not_called()
        patched.push.assert_not_called()


class TestSecondCheck:
    """A stop just before the push: the rebase is undone."""

    def test_moved_restores_and_does_not_push(
        self, patched: SimpleNamespace, tmp_path: Path
    ) -> None:
        patched.merge_base.side_effect = ["true", "false"]

        result = _run(tmp_path)

        assert (result.exit_code, result.branch_check) == (2, "moved")
        patched.reset.assert_called_once()
        assert patched.reset.call_args.args[1] == "presha"
        patched.push.assert_not_called()

    def test_error_restores_and_does_not_push(
        self, patched: SimpleNamespace, tmp_path: Path
    ) -> None:
        patched.merge_base.side_effect = ["true", RuntimeError("boom")]

        result = _run(tmp_path)

        assert (result.exit_code, result.branch_check) == (2, "error")
        patched.reset.assert_called_once()
        assert patched.reset.call_args.args[1] == "presha"
        patched.push.assert_not_called()


def test_both_checks_pass_pushes(patched: SimpleNamespace, tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert (result.exit_code, result.branch_check) == (0, None)
    assert patched.merge_base.call_count == 2
    patched.reset.assert_not_called()
    patched.push.assert_called_once()


@pytest.fixture
def all_checks(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Stub everything but git around the workflow; return the checks stub."""
    checks = MagicMock(return_value=(set(), {}))
    monkeypatch.setattr(rebase_module, "_preflight", lambda _pd: None)
    monkeypatch.setattr(
        rebase_module, "_resolve_base_branch", lambda _pd, _arg: ("main", None)
    )
    monkeypatch.setattr(rebase_module, "prepare_llm_environment", lambda _pd: {})
    monkeypatch.setattr(rebase_module, "_run_all_checks", checks)
    return checks


def _run_real(remote: BareRemote) -> int:
    return run_rebase_workflow(remote.local_dir, provider="claude").exit_code


@pytest.mark.git_integration
class TestRealGit:
    """Every case moves the base: otherwise ``needs_rebase`` exits 0 early."""

    def test_foreign_commit_before_the_run(
        self, bare_remote: BareRemote, all_checks: MagicMock
    ) -> None:
        bare_remote.move_base("base2")
        foreign_sha = bare_remote.push_foreign("foreign1")

        exit_code = _run_real(bare_remote)

        # One comparison, so that a failure shows the exit code and the remote together.
        assert (exit_code, bare_remote.remote_sha()) == (2, foreign_sha)
        all_checks.assert_not_called()

    def test_foreign_commit_fetched_just_before_the_push(
        self, bare_remote: BareRemote, all_checks: MagicMock
    ) -> None:
        bare_remote.move_base("base2")
        pre_sha = bare_remote.local.head.commit.hexsha
        pushed: list[str] = []

        def foreign_push_on_second_call(
            _project_dir: Path, _automated: bool
        ) -> tuple[set[object], dict[str, str]]:
            if all_checks.call_count == 2:
                pushed.append(bare_remote.push_foreign("foreign1"))
                bare_remote.local.git.fetch("origin")
            return set(), {}

        all_checks.side_effect = foreign_push_on_second_call

        exit_code = _run_real(bare_remote)

        assert (
            exit_code,
            bare_remote.remote_sha(),
            bare_remote.local.head.commit.hexsha,
        ) == (2, pushed[0], pre_sha)

    def test_normal_rebase_pushes(
        self, bare_remote: BareRemote, all_checks: MagicMock
    ) -> None:
        base_sha = bare_remote.move_base("base2")
        bare_remote.commit_local("local1")

        exit_code = _run_real(bare_remote)

        local_head = bare_remote.local.head.commit.hexsha
        assert (exit_code, bare_remote.remote_sha()) == (0, local_head)
        assert base_sha in bare_remote.remote_log()
        assert all_checks.call_count == 2
