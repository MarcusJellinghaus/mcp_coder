"""Tests for the create-pr resume path: an open PR for the branch skips phase A."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.create_pr.core import run_create_pr_workflow

_CORE = "mcp_coder.workflows.create_pr.core"
_PR = {"number": 42, "url": "https://github.com/test/repo/pull/42"}


@dataclass
class _Mocks:
    linkage: MagicMock
    find_pr: MagicMock
    cleanup: MagicMock
    resolve: MagicMock
    post_creation: MagicMock
    update_label: MagicMock
    handle_failure: MagicMock
    git_clean: MagicMock
    prereqs: MagicMock
    generate: MagicMock
    create_pr: MagicMock


@pytest.fixture
def mocks() -> Iterator[_Mocks]:
    """Patch every collaborator of the resume path; an open PR exists."""
    with (
        patch(f"{_CORE}.validate_branch_issue_linkage", return_value=5) as linkage,
        patch(f"{_CORE}._find_open_pr", return_value=_PR) as find_pr,
        patch(f"{_CORE}._cleanup_commit_push", return_value=None) as cleanup,
        patch(f"{_CORE}._resolve_issue_from_pr", return_value=None) as resolve,
        patch(f"{_CORE}.run_post_creation", return_value="pr_created") as post,
        patch(f"{_CORE}.apply_final_label", return_value=0) as update_label,
        patch(f"{_CORE}._handle_create_pr_failure") as handle_failure,
        patch(f"{_CORE}.get_current_branch_name", return_value="5-feat"),
        patch(f"{_CORE}.check_prerequisites") as prereqs,
        patch(f"{_CORE}.generate_pr_summary") as generate,
        patch(f"{_CORE}.create_pull_request") as create_pr,
        patch(
            "mcp_coder.workflows.create_pr.pre_creation.check_git_clean",
            return_value=True,
        ) as git_clean,
    ):
        yield _Mocks(
            linkage=linkage,
            find_pr=find_pr,
            cleanup=cleanup,
            resolve=resolve,
            post_creation=post,
            update_label=update_label,
            handle_failure=handle_failure,
            git_clean=git_clean,
            prereqs=prereqs,
            generate=generate,
            create_pr=create_pr,
        )


class TestResumePath:
    """run_create_pr_workflow with an open PR for the current branch."""

    def test_no_pr_info_skips_to_phase_b(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Phase A creation steps are skipped; phase B and the final label run."""
        result = run_create_pr_workflow(tmp_path, "claude", update_issue_labels=True)

        assert result == 0
        mocks.prereqs.assert_not_called()
        mocks.generate.assert_not_called()
        mocks.create_pr.assert_not_called()
        mocks.cleanup.assert_not_called()
        mocks.post_creation.assert_called_once_with(
            tmp_path, "5-feat", "claude", None, None
        )
        mocks.update_label.assert_called_once_with(
            tmp_path, "pr_creating", "pr_created", 5
        )

    def test_pr_info_clean_runs_cleanup_then_phase_b(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """pr_info/ left over → cleanup/commit/push, then phase B."""
        (tmp_path / "pr_info").mkdir()
        manager = MagicMock()
        manager.attach_mock(mocks.cleanup, "cleanup")
        manager.attach_mock(mocks.post_creation, "post_creation")

        result = run_create_pr_workflow(tmp_path, "claude")

        assert result == 0
        mocks.cleanup.assert_called_once_with(tmp_path)
        assert [c[0] for c in manager.mock_calls] == ["cleanup", "post_creation"]

    def test_pr_info_dirty_tree_fails(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Dirty tree with pr_info/ → resume_cleanup failure, no phase B."""
        (tmp_path / "pr_info").mkdir()
        mocks.git_clean.return_value = False

        result = run_create_pr_workflow(tmp_path, "claude")

        assert result == 1
        mocks.cleanup.assert_not_called()
        mocks.handle_failure.assert_called_once()
        assert mocks.handle_failure.call_args.kwargs["stage"] == "resume_cleanup"
        mocks.post_creation.assert_not_called()

    def test_push_failure_fails(self, mocks: _Mocks, tmp_path: Path) -> None:
        """Cleanup push rejected → failure handler with stage push, no phase B."""
        (tmp_path / "pr_info").mkdir()
        mocks.cleanup.return_value = ("push", "rejected")

        result = run_create_pr_workflow(tmp_path, "claude")

        assert result == 1
        kwargs = mocks.handle_failure.call_args.kwargs
        assert kwargs["stage"] == "push"
        assert kwargs["message"] == "rejected"
        mocks.post_creation.assert_not_called()

    def test_issue_resolved_from_pr_when_not_linked(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """Linkage None → closing-references fallback feeds failure and label."""
        mocks.linkage.return_value = None
        mocks.resolve.return_value = 5
        (tmp_path / "pr_info").mkdir()
        mocks.git_clean.return_value = False

        result = run_create_pr_workflow(tmp_path, "claude", update_issue_labels=True)

        assert result == 1
        mocks.resolve.assert_called_once_with(tmp_path, 42)
        assert mocks.handle_failure.call_args.kwargs["issue_number"] == 5

        mocks.handle_failure.reset_mock()
        mocks.git_clean.return_value = True

        result = run_create_pr_workflow(tmp_path, "claude", update_issue_labels=True)

        assert result == 0
        mocks.handle_failure.assert_not_called()
        assert mocks.update_label.call_args.args[3] == 5

    def test_no_resolve_without_label_updates(
        self, mocks: _Mocks, tmp_path: Path
    ) -> None:
        """The closing-references fallback keeps the update_issue_labels gate."""
        mocks.linkage.return_value = None

        result = run_create_pr_workflow(tmp_path, "claude")

        assert result == 0
        mocks.resolve.assert_not_called()

    @patch(
        "mcp_coder.workflow_utils.failure_handling._branch_head",
        return_value=("5-feat", "abc1234"),
    )
    @patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure")
    def test_crash_in_cleanup_netted_by_phase_a_guard(
        self,
        mock_workflow_failure: MagicMock,
        _mock_branch_head: MagicMock,
        mocks: _Mocks,
        tmp_path: Path,
    ) -> None:
        """A crash in the resume cleanup → pr_creating_failed with the resolved issue."""
        mocks.linkage.return_value = None
        mocks.resolve.return_value = 5
        (tmp_path / "pr_info").mkdir()
        mocks.cleanup.side_effect = RuntimeError("boom")

        result = run_create_pr_workflow(tmp_path, "claude", update_issue_labels=True)

        assert result == 1
        mock_workflow_failure.assert_called_once()
        failure = mock_workflow_failure.call_args.args[0]
        assert failure.category == "pr_creating_failed"
        assert mock_workflow_failure.call_args.kwargs["issue_number"] == 5
        mocks.post_creation.assert_not_called()
