"""Tests for create_pr post-creation (phase B) logic."""

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.rebase import RebaseOutcome
from mcp_coder.workflows.create_pr.post_creation import (
    apply_post_creation_label,
    run_post_creation,
)

_MODULE = "mcp_coder.workflows.create_pr.post_creation"
_PROJECT = Path("/test")
_BRANCH = "feat"
_PROVIDER = "claude"
_ISSUE = 123
_CI_STATUS: dict[str, Any] = {"run": {"status": "completed"}, "jobs": []}


@dataclass
class _Mocks:
    poll: MagicMock
    rebase: MagicMock
    ci_manager_cls: MagicMock
    ci_poll: MagicMock
    sha: MagicMock
    refresh: MagicMock
    apply_label: MagicMock
    order: MagicMock


@pytest.fixture
def mocks() -> Iterator[_Mocks]:
    """Patch the collaborators of ``run_post_creation``."""
    order = MagicMock()
    with (
        patch(f"{_MODULE}.apply_post_creation_label", return_value=0) as apply_label,
        patch(f"{_MODULE}._poll_mergeable_state", return_value="clean") as poll,
        patch(
            f"{_MODULE}._attempt_rebase_and_push",
            return_value=RebaseOutcome(reason="ok", base_branch="main"),
        ) as rebase,
        patch(f"{_MODULE}.CIResultsManager") as ci_manager_cls,
        patch(
            f"{_MODULE}._poll_for_ci_completion", return_value=(_CI_STATUS, True)
        ) as ci_poll,
        patch(f"{_MODULE}.get_latest_commit_sha", return_value="abc123") as sha,
        patch(f"{_MODULE}.refresh_pr_description", return_value=True) as refresh,
    ):
        order.attach_mock(rebase, "rebase")
        order.attach_mock(sha, "sha")
        order.attach_mock(ci_poll, "ci_poll")
        order.attach_mock(refresh, "refresh")
        yield _Mocks(
            poll=poll,
            rebase=rebase,
            ci_manager_cls=ci_manager_cls,
            ci_poll=ci_poll,
            sha=sha,
            refresh=refresh,
            apply_label=apply_label,
            order=order,
        )


def _label(mocks: _Mocks, *args: str | None) -> str:
    """Run ``run_post_creation``; return the final label it handed on."""
    assert (
        run_post_creation(
            _PROJECT,
            _BRANCH,
            _PROVIDER,
            *args,
            issue_number=_ISSUE,
            update_issue_labels=True,
        )
        == 0
    )
    mocks.apply_label.assert_called_once()
    label: str = mocks.apply_label.call_args.args[1]
    return label


class TestRunPostCreation:
    """Tests for run_post_creation."""

    @pytest.mark.parametrize("state", ["clean", "behind", "unknown", None])
    def test_non_dirty_state_waits_for_ci(
        self, mocks: _Mocks, state: str | None
    ) -> None:
        """Any non-dirty state goes straight to the CI wait; no rebase."""
        mocks.poll.return_value = state

        assert _label(mocks) == "pr_created"

        mocks.poll.assert_called_once_with(_PROJECT, _BRANCH)
        mocks.rebase.assert_not_called()
        mocks.ci_poll.assert_called_once_with(
            mocks.ci_manager_cls.return_value, _BRANCH, expected_sha="abc123"
        )

    def test_ci_failure_returns_failing_ci(self, mocks: _Mocks) -> None:
        """CI completed but failed → failing_ci."""
        mocks.ci_poll.return_value = (_CI_STATUS, False)

        assert _label(mocks) == "failing_ci"

    def test_ci_no_status_returns_pr_created(self, mocks: _Mocks) -> None:
        """Timeout / no CI / API error (None, True) → pr_created."""
        mocks.ci_poll.return_value = (None, True)

        assert _label(mocks) == "pr_created"

    def test_dirty_then_clean_after_rebase(self, mocks: _Mocks) -> None:
        """Dirty PR is rebased once; clean afterwards → CI wait → pr_created."""
        mocks.poll.side_effect = ["dirty", "clean"]

        assert _label(mocks) == "pr_created"

        mocks.rebase.assert_called_once_with(_PROJECT)
        assert mocks.poll.call_count == 2
        mocks.ci_poll.assert_called_once()

    def test_dirty_after_rebase_returns_merge_conflict(self, mocks: _Mocks) -> None:
        """Still dirty after the rebase → pr_merge_conflict; CI not polled."""
        mocks.poll.side_effect = ["dirty", "dirty"]
        mocks.rebase.return_value = RebaseOutcome(reason="conflict", base_branch="main")

        assert _label(mocks) == "pr_merge_conflict"

        mocks.rebase.assert_called_once_with(_PROJECT)
        mocks.ci_manager_cls.assert_not_called()
        mocks.ci_poll.assert_not_called()

    def test_ci_manager_error_returns_pr_created(self, mocks: _Mocks) -> None:
        """CIResultsManager construction failure → pr_created, no CI poll."""
        mocks.ci_manager_cls.side_effect = ValueError("no token")

        assert _label(mocks) == "pr_created"

        mocks.ci_poll.assert_not_called()

    def test_expected_sha_read_after_rebase(self, mocks: _Mocks) -> None:
        """expected_sha is the HEAD read after the rebase."""
        mocks.poll.side_effect = ["dirty", "clean"]
        mocks.sha.side_effect = ["before-sha", "rebased-sha", "rebased-sha"]

        _label(mocks)

        names = [c[0] for c in mocks.order.mock_calls]
        assert names[:3] == ["sha", "rebase", "sha"]
        assert mocks.ci_poll.call_args.kwargs["expected_sha"] == "rebased-sha"

    def test_push_failed_waits_on_pushed_sha_without_refresh(
        self, mocks: _Mocks
    ) -> None:
        """Rebase push fails → HEAD reset; CI waits on the PR's SHA; no refresh."""
        head = {"sha": "pushed-sha"}

        def rebase(_project_dir: Path) -> RebaseOutcome:
            head["sha"] = "unpushed-sha"
            return RebaseOutcome(reason="push_failed", base_branch="main")

        def reset(_project_dir: Path, sha: str) -> bool:
            head["sha"] = sha
            return True

        mocks.poll.side_effect = ["dirty", "clean"]
        mocks.rebase.side_effect = rebase
        mocks.sha.side_effect = lambda _project_dir: head["sha"]

        with patch(f"{_MODULE}._reset_hard", side_effect=reset) as mock_reset:
            assert _label(mocks) == "pr_created"

        mock_reset.assert_called_once_with(_PROJECT, "pushed-sha")
        assert mocks.ci_poll.call_args.kwargs["expected_sha"] == "pushed-sha"
        mocks.refresh.assert_not_called()

    def test_none_sha_passed_through(self, mocks: _Mocks) -> None:
        """A None HEAD is passed to the CI wait unchanged."""
        mocks.sha.return_value = None

        assert _label(mocks) == "pr_created"

        assert mocks.ci_poll.call_args.kwargs["expected_sha"] is None


class TestRunPostCreationRefresh:
    """Tests for the PR description refresh at the end of run_post_creation."""

    def test_head_unchanged_skips_refresh(self, mocks: _Mocks) -> None:
        """No push during phase B → no refresh."""
        assert _label(mocks) == "pr_created"

        mocks.refresh.assert_not_called()

    def test_rebase_changed_head_refreshes_after_ci(self, mocks: _Mocks) -> None:
        """Dirty rebase pushed a new HEAD → refresh after the CI wait."""
        mocks.poll.side_effect = ["dirty", "clean"]
        mocks.sha.side_effect = ["before", "after", "after"]

        assert _label(mocks, "mcp.json", "settings.json") == "pr_created"
        mocks.refresh.assert_called_once_with(
            _PROJECT, _BRANCH, _PROVIDER, "mcp.json", "settings.json"
        )
        names = [c[0] for c in mocks.order.mock_calls]
        assert names.index("ci_poll") < names.index("refresh")

    def test_merge_conflict_still_refreshes(self, mocks: _Mocks) -> None:
        """HEAD changed but still dirty → refresh runs, label pr_merge_conflict."""
        mocks.poll.side_effect = ["dirty", "dirty"]
        mocks.sha.side_effect = ["before", "after"]

        assert _label(mocks) == "pr_merge_conflict"

        mocks.refresh.assert_called_once_with(_PROJECT, _BRANCH, _PROVIDER, None, None)

    @pytest.mark.parametrize("refreshed", [True, False])
    def test_label_unchanged_by_refresh_result(
        self, mocks: _Mocks, refreshed: bool
    ) -> None:
        """The refresh result never changes the returned label."""
        mocks.poll.side_effect = ["dirty", "clean"]
        mocks.sha.side_effect = ["before", "after", "after"]
        mocks.ci_poll.return_value = (_CI_STATUS, False)
        mocks.refresh.return_value = refreshed

        assert _label(mocks) == "failing_ci"

        mocks.refresh.assert_called_once()


class TestRunPostCreationLabel:
    """run_post_creation hands the label on and returns its exit code."""

    @pytest.mark.parametrize("update_issue_labels", [True, False])
    @pytest.mark.parametrize("rc", [0, 1])
    def test_forwards_issue_and_returns_exit_code(
        self, mocks: _Mocks, update_issue_labels: bool, rc: int
    ) -> None:
        """Issue number and labels flag are forwarded; the exit code is returned."""
        mocks.apply_label.return_value = rc

        result = run_post_creation(
            _PROJECT,
            _BRANCH,
            _PROVIDER,
            issue_number=_ISSUE,
            update_issue_labels=update_issue_labels,
        )

        assert result == rc
        mocks.apply_label.assert_called_once_with(
            _PROJECT,
            "pr_created",
            issue_number=_ISSUE,
            update_issue_labels=update_issue_labels,
        )


class TestApplyPostCreationLabel:
    """Tests for apply_post_creation_label: final label write + exit code."""

    @pytest.mark.parametrize(
        ("label", "expected"),
        [("pr_merge_conflict", 1), ("failing_ci", 0), ("pr_created", 0)],
    )
    def test_exit_code_per_label(self, label: str, expected: int) -> None:
        """pr_merge_conflict (74) exits 1; failing_ci / pr_created exit 0."""
        with patch(f"{_MODULE}.apply_final_label", return_value=0) as mock_apply:
            result = apply_post_creation_label(
                _PROJECT, label, issue_number=_ISSUE, update_issue_labels=True
            )

        assert result == expected
        mock_apply.assert_called_once_with(_PROJECT, "pr_creating", label, _ISSUE)

    def test_label_write_failure_returns_1(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A failed label write → exit 1."""
        with (
            patch(f"{_MODULE}.apply_final_label", return_value=1),
            caplog.at_level(logging.DEBUG),
        ):
            result = apply_post_creation_label(
                _PROJECT, "pr_created", issue_number=_ISSUE, update_issue_labels=True
            )

        assert result == 1
        assert "final issue label not applied" in caplog.text

    @pytest.mark.parametrize(
        ("label", "expected"),
        [("pr_merge_conflict", 1), ("failing_ci", 0), ("pr_created", 0)],
    )
    def test_labels_off_skips_write_keeps_exit_code(
        self, label: str, expected: int
    ) -> None:
        """update_issue_labels=False → no label write; 74 still exits 1."""
        with patch(f"{_MODULE}.apply_final_label") as mock_apply:
            result = apply_post_creation_label(
                _PROJECT, label, issue_number=_ISSUE, update_issue_labels=False
            )

        assert result == expected
        mock_apply.assert_not_called()

    def test_no_issue_skips_write_with_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Labels on but no linked issue → no write, 'completed with warnings'."""
        with (
            patch(f"{_MODULE}.apply_final_label") as mock_apply,
            caplog.at_level(logging.DEBUG),
        ):
            result = apply_post_creation_label(
                _PROJECT, "pr_created", issue_number=None, update_issue_labels=True
            )

        assert result == 0
        mock_apply.assert_not_called()
        assert "completed with warnings" in caplog.text
