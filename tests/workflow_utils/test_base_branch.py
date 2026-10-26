"""Tests for base branch detection functionality.

Detection itself lives upstream (``mcp_workspace``); these tests cover the
local wrapper that builds and injects the GitHub managers.
"""

from collections.abc import Generator
from pathlib import Path
from typing import NamedTuple
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.mcp_workspace_git import BaseBranchSource
from mcp_coder.workflow_utils.base_branch import (
    check_base_branch_on_origin,
    detect_base_branch,
    detect_base_branch_with_source,
)
from tests.github_factories import make_issue_data

MODULE = "mcp_coder.workflow_utils.base_branch"
PROJECT_DIR = Path("/test/project")


class BaseBranchMocks(NamedTuple):
    """Mocks for the wrapper's collaborators."""

    upstream: MagicMock  # _upstream_detect_with_source
    pr_manager: MagicMock  # PullRequestManager class
    issue_manager: MagicMock  # IssueManager class
    branch: MagicMock  # get_current_branch_name


@pytest.fixture
def mocks() -> Generator[BaseBranchMocks, None, None]:
    """Patch upstream detection, both manager classes and the branch reader."""
    with (
        patch(f"{MODULE}._upstream_detect_with_source") as mock_upstream,
        patch(f"{MODULE}.PullRequestManager") as mock_pr,
        patch(f"{MODULE}.IssueManager") as mock_issue,
        patch(f"{MODULE}.get_current_branch_name") as mock_branch,
    ):
        mock_upstream.return_value = ("develop", BaseBranchSource.PR)
        yield BaseBranchMocks(
            upstream=mock_upstream,
            pr_manager=mock_pr,
            issue_manager=mock_issue,
            branch=mock_branch,
        )


class TestDetectBaseBranchWithSource:
    """Tests for the detect_base_branch_with_source wrapper."""

    def test_builds_and_injects_both_managers(self, mocks: BaseBranchMocks) -> None:
        """Both managers are built and passed upstream; its tuple is returned."""
        result = detect_base_branch_with_source(
            PROJECT_DIR, current_branch="370-feature"
        )

        assert result == ("develop", BaseBranchSource.PR)
        mocks.pr_manager.assert_called_once_with(PROJECT_DIR)
        mocks.issue_manager.assert_called_once_with(project_dir=PROJECT_DIR)
        mocks.upstream.assert_called_once_with(
            PROJECT_DIR,
            "370-feature",
            None,
            mocks.pr_manager.return_value,
            mocks.issue_manager.return_value,
        )

    def test_pr_manager_failure_passes_none(self, mocks: BaseBranchMocks) -> None:
        """A failing PullRequestManager is skipped, not raised."""
        mocks.pr_manager.side_effect = ValueError("no token")

        detect_base_branch_with_source(PROJECT_DIR, current_branch="370-feature")

        args = mocks.upstream.call_args.args
        assert args[3] is None
        assert args[4] is mocks.issue_manager.return_value

    def test_issue_manager_failure_passes_none(self, mocks: BaseBranchMocks) -> None:
        """A failing IssueManager is skipped, not raised."""
        mocks.issue_manager.side_effect = ValueError("no token")

        detect_base_branch_with_source(PROJECT_DIR, current_branch="370-feature")

        args = mocks.upstream.call_args.args
        assert args[3] is mocks.pr_manager.return_value
        assert args[4] is None

    def test_issue_data_given_skips_issue_manager(self, mocks: BaseBranchMocks) -> None:
        """Pre-fetched issue data is forwarded; no IssueManager is built."""
        issue_data = make_issue_data(
            number=370, title="Test Issue", url="", base_branch="feature/v2"
        )

        detect_base_branch_with_source(
            PROJECT_DIR, current_branch="370-feature", issue_data=issue_data
        )

        mocks.issue_manager.assert_not_called()
        args = mocks.upstream.call_args.args
        assert args[2] is issue_data
        assert args[4] is None

    def test_branch_without_issue_number_skips_issue_manager(
        self, mocks: BaseBranchMocks
    ) -> None:
        """A branch name without an issue number never builds an IssueManager."""
        detect_base_branch_with_source(PROJECT_DIR, current_branch="feature-x")

        mocks.issue_manager.assert_not_called()
        assert mocks.upstream.call_args.args[4] is None

    def test_auto_detects_current_branch(self, mocks: BaseBranchMocks) -> None:
        """Without current_branch, the checked-out branch is passed upstream."""
        mocks.branch.return_value = "370-feature"

        detect_base_branch_with_source(PROJECT_DIR)

        mocks.branch.assert_called_once_with(PROJECT_DIR)
        assert mocks.upstream.call_args.args[1] == "370-feature"

    def test_detached_head_returns_none(self, mocks: BaseBranchMocks) -> None:
        """Detached HEAD returns None without calling upstream."""
        mocks.branch.return_value = None

        assert detect_base_branch_with_source(PROJECT_DIR) is None
        mocks.upstream.assert_not_called()

    def test_merge_base_source_value(self) -> None:
        """The upstream enum spells the merge-base source ``merge_base``."""
        assert BaseBranchSource.MERGE_BASE.value == "merge_base"


class TestDetectBaseBranch:
    """Tests for detect_base_branch."""

    def test_returns_branch_only(self, mocks: BaseBranchMocks) -> None:
        """Only the branch name of the detected tuple is returned."""
        assert detect_base_branch(PROJECT_DIR, current_branch="370-feature") == (
            "develop"
        )

    def test_returns_none_when_detection_fails(self, mocks: BaseBranchMocks) -> None:
        """Upstream None is passed through."""
        mocks.upstream.return_value = None

        assert detect_base_branch(PROJECT_DIR, current_branch="370-feature") is None


class TestCheckBaseBranchOnOrigin:
    """Tests for check_base_branch_on_origin."""

    PROBE = "mcp_coder.workflow_utils.base_branch.probe_origin_branch"

    @staticmethod
    def _probe(
        exists: bool | None, stderr: str | None = "", error: str | None = None
    ) -> dict[str, object]:
        return {
            "success": exists is not None,
            "error": error,
            "returncode": 0 if exists is not None else 128,
            "stderr": stderr,
            "exists": exists,
        }

    def test_returns_none_when_branch_exists(self) -> None:
        """exists=True means the branch exists on origin."""
        project_dir = Path("/test/project")
        with patch(self.PROBE, return_value=self._probe(True)) as mock_probe:
            result = check_base_branch_on_origin(project_dir, "main")

        assert result is None
        mock_probe.assert_called_once_with(project_dir, "main")

    def test_returns_message_when_branch_missing(self) -> None:
        """exists=False without detail gives the bare message."""
        with patch(self.PROBE, return_value=self._probe(False, stderr="")):
            result = check_base_branch_on_origin(Path("/test/project"), "main")

        assert result == (
            "Base branch 'main' not found on origin; create and push it first"
        )

    def test_message_includes_stderr(self) -> None:
        """Origin unreachable includes git's stderr in the message."""
        probe = self._probe(None, stderr="fatal: could not read from remote\n")
        with patch(self.PROBE, return_value=probe):
            result = check_base_branch_on_origin(Path("/test/project"), "main")

        assert result is not None
        assert result.startswith("Base branch 'main' not found on origin")
        assert result.endswith("(fatal: could not read from remote)")

    def test_message_falls_back_to_error(self) -> None:
        """Without stderr, the probe's error is the detail."""
        probe = self._probe(
            None, stderr=None, error="Not a git repository: /test/project"
        )
        with patch(self.PROBE, return_value=probe):
            result = check_base_branch_on_origin(Path("/test/project"), "main")

        assert result is not None
        assert result.endswith("(Not a git repository: /test/project)")
