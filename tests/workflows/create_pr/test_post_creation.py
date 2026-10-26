"""Tests for create_pr post-creation (phase B) logic."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.rebase import RebaseOutcome
from mcp_coder.workflows.create_pr.post_creation import run_post_creation

_MODULE = "mcp_coder.workflows.create_pr.post_creation"
_PROJECT = Path("/test")
_BRANCH = "feat"
_PROVIDER = "claude"
_CI_STATUS: dict[str, Any] = {"run": {"status": "completed"}, "jobs": []}


@dataclass
class _Mocks:
    poll: MagicMock
    rebase: MagicMock
    ci_manager_cls: MagicMock
    ci_poll: MagicMock
    sha: MagicMock
    refresh: MagicMock
    order: MagicMock


@pytest.fixture
def mocks() -> Iterator[_Mocks]:
    """Patch the collaborators of ``run_post_creation``."""
    order = MagicMock()
    with (
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
            order=order,
        )


class TestRunPostCreation:
    """Tests for run_post_creation."""

    @pytest.mark.parametrize("state", ["clean", "behind", "unknown", None])
    def test_non_dirty_state_waits_for_ci(
        self, mocks: _Mocks, state: str | None
    ) -> None:
        """Any non-dirty state goes straight to the CI wait; no rebase."""
        mocks.poll.return_value = state

        assert run_post_creation(_PROJECT, _BRANCH, _PROVIDER) == "pr_created"

        mocks.poll.assert_called_once_with(_PROJECT, _BRANCH)
        mocks.rebase.assert_not_called()
        mocks.ci_poll.assert_called_once_with(
            mocks.ci_manager_cls.return_value, _BRANCH, expected_sha="abc123"
        )

    def test_ci_failure_returns_failing_ci(self, mocks: _Mocks) -> None:
        """CI completed but failed → failing_ci."""
        mocks.ci_poll.return_value = (_CI_STATUS, False)

        assert run_post_creation(_PROJECT, _BRANCH, _PROVIDER) == "failing_ci"

    def test_ci_no_status_returns_pr_created(self, mocks: _Mocks) -> None:
        """Timeout / no CI / API error (None, True) → pr_created."""
        mocks.ci_poll.return_value = (None, True)

        assert run_post_creation(_PROJECT, _BRANCH, _PROVIDER) == "pr_created"

    def test_dirty_then_clean_after_rebase(self, mocks: _Mocks) -> None:
        """Dirty PR is rebased once; clean afterwards → CI wait → pr_created."""
        mocks.poll.side_effect = ["dirty", "clean"]

        assert run_post_creation(_PROJECT, _BRANCH, _PROVIDER) == "pr_created"

        mocks.rebase.assert_called_once_with(_PROJECT)
        assert mocks.poll.call_count == 2
        mocks.ci_poll.assert_called_once()

    def test_dirty_after_rebase_returns_merge_conflict(self, mocks: _Mocks) -> None:
        """Still dirty after the rebase → pr_merge_conflict; CI not polled."""
        mocks.poll.side_effect = ["dirty", "dirty"]
        mocks.rebase.return_value = RebaseOutcome(reason="conflict", base_branch="main")

        assert run_post_creation(_PROJECT, _BRANCH, _PROVIDER) == "pr_merge_conflict"

        mocks.rebase.assert_called_once_with(_PROJECT)
        mocks.ci_manager_cls.assert_not_called()
        mocks.ci_poll.assert_not_called()

    def test_ci_manager_error_returns_pr_created(self, mocks: _Mocks) -> None:
        """CIResultsManager construction failure → pr_created, no CI poll."""
        mocks.ci_manager_cls.side_effect = ValueError("no token")

        assert run_post_creation(_PROJECT, _BRANCH, _PROVIDER) == "pr_created"

        mocks.ci_poll.assert_not_called()

    def test_expected_sha_read_after_rebase(self, mocks: _Mocks) -> None:
        """expected_sha is the HEAD read after the rebase."""
        mocks.poll.side_effect = ["dirty", "clean"]
        mocks.sha.side_effect = ["before-sha", "rebased-sha", "rebased-sha"]

        run_post_creation(_PROJECT, _BRANCH, _PROVIDER)

        names = [c[0] for c in mocks.order.mock_calls]
        assert names[:3] == ["sha", "rebase", "sha"]
        assert mocks.ci_poll.call_args.kwargs["expected_sha"] == "rebased-sha"

    def test_none_sha_passed_through(self, mocks: _Mocks) -> None:
        """A None HEAD is passed to the CI wait unchanged."""
        mocks.sha.return_value = None

        assert run_post_creation(_PROJECT, _BRANCH, _PROVIDER) == "pr_created"

        assert mocks.ci_poll.call_args.kwargs["expected_sha"] is None


class TestRunPostCreationRefresh:
    """Tests for the PR description refresh at the end of run_post_creation."""

    def test_head_unchanged_skips_refresh(self, mocks: _Mocks) -> None:
        """No push during phase B → no refresh."""
        assert run_post_creation(_PROJECT, _BRANCH, _PROVIDER) == "pr_created"

        mocks.refresh.assert_not_called()

    def test_rebase_changed_head_refreshes_after_ci(self, mocks: _Mocks) -> None:
        """Dirty rebase pushed a new HEAD → refresh after the CI wait."""
        mocks.poll.side_effect = ["dirty", "clean"]
        mocks.sha.side_effect = ["before", "after", "after"]

        result = run_post_creation(
            _PROJECT, _BRANCH, _PROVIDER, "mcp.json", "settings.json"
        )

        assert result == "pr_created"
        mocks.refresh.assert_called_once_with(
            _PROJECT, _BRANCH, _PROVIDER, "mcp.json", "settings.json"
        )
        names = [c[0] for c in mocks.order.mock_calls]
        assert names.index("ci_poll") < names.index("refresh")

    def test_merge_conflict_still_refreshes(self, mocks: _Mocks) -> None:
        """HEAD changed but still dirty → refresh runs, label pr_merge_conflict."""
        mocks.poll.side_effect = ["dirty", "dirty"]
        mocks.sha.side_effect = ["before", "after"]

        assert run_post_creation(_PROJECT, _BRANCH, _PROVIDER) == "pr_merge_conflict"

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

        assert run_post_creation(_PROJECT, _BRANCH, _PROVIDER) == "failing_ci"

        mocks.refresh.assert_called_once()
