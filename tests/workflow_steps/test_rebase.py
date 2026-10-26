"""Tests for the rebase-and-push workflow step."""

import logging
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.rebase import (
    RebaseOutcome,
    _attempt_rebase_and_push,
    _base_sha,
    _classify_failed_rebase,
    _get_rebase_target_branch,
    _reset_hard,
)
from mcp_coder.workflows.implement.core import run_implement_workflow

_MODULE = "mcp_coder.workflow_steps.rebase"
_FULL_SHA = "abc1234def5678abc1234def5678abc1234def56"


def _probe(status: str, files: list[str] | None = None) -> dict[str, object]:
    """Build a RebaseProbe-shaped dict for the mocked ``probe_rebase_conflicts``."""
    return {
        "success": status == "clean",
        "error": None if status in ("clean", "conflict") else status,
        "status": status,
        "files": files or [],
    }


@pytest.fixture(autouse=True)
def mock_check_base_on_origin() -> Iterator[MagicMock]:
    """Treat every base branch as present on origin unless a test overrides it."""
    with patch(
        f"{_MODULE}.check_base_branch_on_origin",
        return_value=None,
    ) as mock_check:
        yield mock_check


@pytest.fixture(autouse=True)
def mock_probe() -> Iterator[MagicMock]:
    """Keep the rebase conflict probe off real git."""
    with patch(
        f"{_MODULE}.probe_rebase_conflicts", return_value=_probe("error")
    ) as mock_probe_fn:
        yield mock_probe_fn


@pytest.fixture(autouse=True)
def mock_remote_sha() -> Iterator[MagicMock]:
    """Keep the origin/<base> sha lookup off real git; it finds nothing."""
    with patch(
        f"{_MODULE}.get_remote_branch_commit_sha", return_value=None
    ) as mock_sha:
        yield mock_sha


class TestRebaseOutcome:
    """Tests for the RebaseOutcome dataclass."""

    @pytest.mark.parametrize(
        "reason",
        [
            "dirty_tree",
            "no_base",
            "base_missing",
            "conflict",
            "rebase_failed",
            "push_failed",
        ],
    )
    def test_ok_false_for_every_failure_reason(self, reason: str) -> None:
        """Test .ok is False for every non-"ok" reason."""
        assert RebaseOutcome(reason).ok is False  # type: ignore[arg-type]

    def test_ok_true_only_for_ok(self) -> None:
        """Test .ok is True for the "ok" reason."""
        assert RebaseOutcome("ok", "main", "abc1234").ok is True


class TestBaseSha:
    """Tests for _base_sha."""

    def test_truncates_to_seven_chars(
        self, mock_remote_sha: MagicMock, tmp_path: Path
    ) -> None:
        """Test the SHA of origin/<base> is truncated to 7 chars."""
        mock_remote_sha.return_value = _FULL_SHA

        assert _base_sha(tmp_path, "main") == "abc1234"
        mock_remote_sha.assert_called_once_with(tmp_path, "main")

    def test_none_when_sha_unavailable(
        self, mock_remote_sha: MagicMock, tmp_path: Path
    ) -> None:
        """Test an unresolvable origin/<base> yields None."""
        mock_remote_sha.return_value = None

        assert _base_sha(tmp_path, "main") is None


class TestClassifyFailedRebase:
    """Tests for _classify_failed_rebase."""

    def test_conflict_with_files(self, mock_probe: MagicMock, tmp_path: Path) -> None:
        """Test a conflict probe classifies as a conflict with its files."""
        mock_probe.return_value = _probe("conflict", ["a.py", "b.py"])

        assert _classify_failed_rebase(tmp_path, "main") == (
            "conflict",
            ("a.py", "b.py"),
        )
        mock_probe.assert_called_once_with(tmp_path, "origin/main")

    @pytest.mark.parametrize("status", ["clean", "unsupported", "error"])
    def test_non_conflict_status_is_rebase_failed(
        self, mock_probe: MagicMock, tmp_path: Path, status: str
    ) -> None:
        """Test clean / unsupported / error probes are a generic failure."""
        mock_probe.return_value = _probe(status)

        assert _classify_failed_rebase(tmp_path, "main") == ("rebase_failed", ())

    def test_probe_raising_is_rebase_failed(
        self, mock_probe: MagicMock, tmp_path: Path
    ) -> None:
        """Test an exception from the probe is a generic failure."""
        mock_probe.side_effect = RuntimeError("boom")

        assert _classify_failed_rebase(tmp_path, "main") == ("rebase_failed", ())


@patch(f"{_MODULE}.push_changes")
@patch(f"{_MODULE}.rebase_onto_branch")
@patch(f"{_MODULE}.detect_base_branch")
@patch(f"{_MODULE}.get_full_status")
class TestAttemptRebaseOutcomes:
    """One test per RebaseOutcome reason from _attempt_rebase_and_push."""

    _CLEAN: dict[str, list[str]] = {"staged": [], "modified": [], "untracked": []}

    def test_ok(
        self,
        mock_status: MagicMock,
        mock_detect: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
        mock_remote_sha: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test a clean rebase + push returns ok with base and short SHA."""
        mock_status.return_value = self._CLEAN
        mock_detect.return_value = "main"
        mock_rebase.return_value = True
        mock_push.return_value = True
        mock_remote_sha.return_value = _FULL_SHA

        outcome = _attempt_rebase_and_push(tmp_path)

        assert outcome == RebaseOutcome("ok", "main", "abc1234")
        assert outcome.ok

    def test_dirty_tree(
        self,
        mock_status: MagicMock,
        mock_detect: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test files = staged + modified (untracked excluded); warning names them."""
        mock_status.return_value = {
            "staged": ["src/b.py"],
            "modified": ["src/a.py", "src/b.py"],
            "untracked": ["notes.txt"],
        }

        with caplog.at_level(logging.WARNING):
            outcome = _attempt_rebase_and_push(tmp_path)

        assert outcome == RebaseOutcome("dirty_tree", files=("src/a.py", "src/b.py"))
        mock_detect.assert_not_called()
        mock_rebase.assert_not_called()
        mock_push.assert_not_called()
        warnings = [
            r.getMessage() for r in caplog.records if r.levelno == logging.WARNING
        ]
        assert any("src/a.py, src/b.py" in m for m in warnings)
        assert not any("notes.txt" in m for m in warnings)

    def test_no_base(
        self,
        mock_status: MagicMock,
        mock_detect: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test no detected base branch returns no_base."""
        mock_status.return_value = self._CLEAN
        mock_detect.return_value = None

        outcome = _attempt_rebase_and_push(tmp_path)

        assert outcome == RebaseOutcome("no_base")
        mock_rebase.assert_not_called()

    def test_base_missing(
        self,
        mock_status: MagicMock,
        mock_detect: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
        mock_check_base_on_origin: MagicMock,
        mock_probe: MagicMock,
        mock_remote_sha: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test a base missing on origin returns base_missing with no SHA."""
        mock_status.return_value = self._CLEAN
        mock_detect.return_value = "epic/x"
        mock_check_base_on_origin.return_value = "missing"

        outcome = _attempt_rebase_and_push(tmp_path)

        assert outcome == RebaseOutcome("base_missing", "epic/x")
        assert outcome.base_sha is None
        mock_probe.assert_not_called()
        mock_remote_sha.assert_not_called()

    def test_conflict(
        self,
        mock_status: MagicMock,
        mock_detect: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
        mock_probe: MagicMock,
        mock_remote_sha: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test a failed rebase classified by the probe as a conflict."""
        mock_status.return_value = self._CLEAN
        mock_detect.return_value = "main"
        mock_rebase.return_value = False
        mock_remote_sha.return_value = _FULL_SHA
        mock_probe.return_value = _probe("conflict", ["a.py"])

        outcome = _attempt_rebase_and_push(tmp_path)

        assert outcome == RebaseOutcome("conflict", "main", "abc1234", ("a.py",))
        mock_push.assert_not_called()

    def test_rebase_failed(
        self,
        mock_status: MagicMock,
        mock_detect: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
        mock_probe: MagicMock,
        mock_remote_sha: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test a failed rebase the probe cannot explain is rebase_failed."""
        mock_status.return_value = self._CLEAN
        mock_detect.return_value = "main"
        mock_rebase.return_value = False
        mock_remote_sha.return_value = _FULL_SHA
        mock_probe.return_value = _probe("clean")

        outcome = _attempt_rebase_and_push(tmp_path)

        assert outcome == RebaseOutcome("rebase_failed", "main", "abc1234")
        mock_push.assert_not_called()

    def test_push_failed(
        self,
        mock_status: MagicMock,
        mock_detect: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
        mock_remote_sha: MagicMock,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test a successful rebase whose push fails returns push_failed."""
        mock_status.return_value = self._CLEAN
        mock_detect.return_value = "main"
        mock_rebase.return_value = True
        mock_push.return_value = False
        mock_remote_sha.return_value = _FULL_SHA

        with caplog.at_level(logging.WARNING):
            outcome = _attempt_rebase_and_push(tmp_path)

        assert outcome == RebaseOutcome("push_failed", "main", "abc1234")
        assert any(r.levelno == logging.WARNING for r in caplog.records)

    def test_base_sha_none_when_sha_unavailable(
        self,
        mock_status: MagicMock,
        mock_detect: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test base_sha is None when origin/<base> is unresolvable (default)."""
        mock_status.return_value = self._CLEAN
        mock_detect.return_value = "main"
        mock_rebase.return_value = True
        mock_push.return_value = True

        outcome = _attempt_rebase_and_push(tmp_path)

        assert outcome == RebaseOutcome("ok", "main", None)


class TestGetRebaseTargetBranch:
    """Tests for _get_rebase_target_branch function."""

    @patch("mcp_coder.workflow_steps.rebase.detect_base_branch")
    def test_returns_pr_base_branch(
        self, mock_detect_base: MagicMock, tmp_path: Path
    ) -> None:
        """Test returns base_branch when detect_base_branch finds a valid branch."""
        mock_detect_base.return_value = "develop"

        result = _get_rebase_target_branch(tmp_path)
        assert result == "develop"

    @patch("mcp_coder.workflow_steps.rebase.detect_base_branch")
    def test_returns_none_when_detection_fails(
        self, mock_detect_base: MagicMock, tmp_path: Path
    ) -> None:
        """Test returns None when detect_base_branch returns None."""
        mock_detect_base.return_value = None

        result = _get_rebase_target_branch(tmp_path)
        assert result is None

    @patch("mcp_coder.workflow_steps.rebase.detect_base_branch")
    def test_returns_valid_branch_from_detection(
        self, mock_detect_base: MagicMock, tmp_path: Path
    ) -> None:
        """Test returns the branch name when detect_base_branch returns a valid branch."""
        mock_detect_base.return_value = "main"

        result = _get_rebase_target_branch(tmp_path)
        assert result == "main"


class TestDirtyWorkingTreeGuard:
    """Tests for the dirty-working-tree guard in _attempt_rebase_and_push."""

    @patch("mcp_coder.workflow_steps.rebase.push_changes")
    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflow_steps.rebase.get_full_status")
    def test_dirty_tree_skips_rebase(
        self,
        mock_status: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test a modified tracked file skips the rebase with a warning."""
        mock_status.return_value = {
            "staged": [],
            "modified": ["src/foo.py"],
            "untracked": [],
        }

        with caplog.at_level(logging.WARNING):
            result = _attempt_rebase_and_push(tmp_path)

        assert result == RebaseOutcome("dirty_tree", files=("src/foo.py",))
        mock_get_target.assert_not_called()
        mock_rebase.assert_not_called()
        mock_push.assert_not_called()
        assert any(r.levelno == logging.WARNING for r in caplog.records)

    @patch("mcp_coder.workflow_steps.rebase.push_changes")
    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflow_steps.rebase.get_full_status")
    def test_ignored_artifact_alone_still_skips_rebase(
        self,
        mock_status: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test a modified uv.lock alone also skips: git refuses it like any other."""
        mock_status.return_value = {
            "staged": [],
            "modified": ["uv.lock"],
            "untracked": [],
        }

        with caplog.at_level(logging.WARNING):
            result = _attempt_rebase_and_push(tmp_path)

        assert result.reason == "dirty_tree"
        assert result.files == ("uv.lock",)
        mock_rebase.assert_not_called()
        mock_push.assert_not_called()
        assert any(r.levelno == logging.WARNING for r in caplog.records)

    @patch("mcp_coder.workflow_steps.rebase.push_changes")
    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflow_steps.rebase.get_full_status")
    def test_untracked_only_proceeds_to_rebase(
        self,
        mock_status: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test untracked files alone do not block: git rebase tolerates them."""
        mock_status.return_value = {
            "staged": [],
            "modified": [],
            "untracked": ["notes.txt"],
        }
        mock_get_target.return_value = "main"
        mock_rebase.return_value = True
        mock_push.return_value = True

        result = _attempt_rebase_and_push(tmp_path)

        assert result.ok
        mock_rebase.assert_called_once_with(tmp_path, "main")

    @patch("mcp_coder.workflow_steps.rebase.push_changes")
    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflow_steps.rebase.get_full_status")
    def test_clean_tree_proceeds_to_rebase(
        self,
        mock_status: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test a clean tree reaches the rebase and succeeds."""
        mock_status.return_value = {"staged": [], "modified": [], "untracked": []}
        mock_get_target.return_value = "main"
        mock_rebase.return_value = True
        mock_push.return_value = True

        result = _attempt_rebase_and_push(tmp_path)

        assert result.ok
        mock_rebase.assert_called_once_with(tmp_path, "main")


class TestMissingBaseGuard:
    """Tests for the missing-on-origin guard in _attempt_rebase_and_push."""

    @patch("mcp_coder.workflow_steps.rebase.push_changes")
    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflow_steps.rebase.get_full_status")
    def test_missing_base_skips_rebase(
        self,
        mock_status: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
        mock_check_base_on_origin: MagicMock,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test a base branch missing on origin skips the rebase with a warning."""
        mock_status.return_value = {"staged": [], "modified": [], "untracked": []}
        mock_get_target.return_value = "epic/x"
        mock_check_base_on_origin.return_value = (
            "Base branch 'epic/x' does not exist on origin"
        )

        with caplog.at_level(logging.WARNING):
            result = _attempt_rebase_and_push(tmp_path)

        assert result == RebaseOutcome("base_missing", "epic/x")
        mock_check_base_on_origin.assert_called_once_with(tmp_path, "epic/x")
        mock_rebase.assert_not_called()
        mock_push.assert_not_called()
        assert any(
            r.levelno == logging.WARNING and "epic/x" in r.getMessage()
            for r in caplog.records
        )


class TestRebaseIntegration:
    """Tests for rebase integration in workflow."""

    @patch("mcp_coder.workflow_steps.rebase.push_changes")
    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_rebase_and_push_called_after_prerequisites(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_prepare: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test rebase is attempted after prerequisites pass."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = False  # Stop here
        mock_get_target.return_value = "main"
        mock_rebase.return_value = True  # Rebase succeeds
        mock_push.return_value = True  # Push succeeds

        run_implement_workflow(Path("/test"), "claude")

        mock_get_target.assert_called_once()
        mock_rebase.assert_called_once_with(Path("/test"), "main")

    @patch("mcp_coder.workflow_steps.rebase.push_changes")
    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_push_with_force_with_lease_after_successful_rebase(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_prepare: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test push is called with force_with_lease=True after successful rebase."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = False  # Stop here
        mock_get_target.return_value = "main"
        mock_rebase.return_value = True  # Rebase succeeds
        mock_push.return_value = True  # Push succeeds

        run_implement_workflow(Path("/test"), "claude")

        # Verify push was called with force_with_lease=True
        mock_push.assert_called_once_with(Path("/test"), force_with_lease=True)

    @patch("mcp_coder.workflow_steps.rebase.push_changes")
    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_workflow_continues_when_rebase_fails(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_prepare: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test workflow continues even when rebase returns False."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = False  # Stop workflow here to focus on rebase
        mock_get_target.return_value = "main"
        mock_rebase.return_value = False  # Rebase failed

        # Should not fail - workflow continues past rebase failure
        result = run_implement_workflow(Path("/test"), "claude", "cli")

        # Workflow should have continued to prepare_task_tracker
        mock_prepare.assert_called_once()
        # Push should not be called when rebase fails
        mock_push.assert_not_called()
        # Result is 1 because prepare_task_tracker returns False, not because of rebase
        assert result == 1

    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_rebase_skipped_when_no_target_branch(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
    ) -> None:
        """Test rebase is skipped when target branch cannot be detected."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = False  # Stop here
        mock_get_target.return_value = None  # No target detected

        run_implement_workflow(Path("/test"), "claude")

        mock_rebase.assert_not_called()

    @patch("mcp_coder.workflow_steps.rebase.push_changes")
    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_workflow_continues_when_push_after_rebase_fails(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_prepare: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test workflow continues even when push after rebase fails."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = False  # Stop workflow here
        mock_get_target.return_value = "main"
        mock_rebase.return_value = True  # Rebase succeeds
        mock_push.return_value = False  # Push fails

        # Should not fail - workflow continues past push failure
        result = run_implement_workflow(Path("/test"), "claude", "cli")

        # Workflow should have continued to prepare_task_tracker
        mock_prepare.assert_called_once()
        # Result is 1 because prepare_task_tracker returns False
        assert result == 1


class TestResetHard:
    """Tests for _reset_hard."""

    @pytest.mark.parametrize(
        ("side_effect", "expected"),
        [
            pytest.param([_result(0)], True, id="ok"),
            pytest.param([_result(128)], False, id="nonzero"),
            pytest.param(OSError("no git"), False, id="exception"),
        ],
    )
    def test_reset_result(self, side_effect: object, expected: bool) -> None:
        with patch(f"{_MODULE}.execute_command", side_effect=side_effect) as cmd:
            assert _reset_hard(Path("/fake/project"), "abc123") is expected

        cmd.assert_called_once_with(
            ["git", "reset", "--hard", "abc123"], cwd=str(Path("/fake/project"))
        )
