"""Test suite for standalone update_workflow_label() function.

Migrated from tests/utils/github_operations/test_issue_manager_label_update.py.
Tests the extracted function in mcp_coder.workflow_utils.label_transitions.
"""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_coder.mcp_workspace_github import (
    BaseGitHubManager,
    IssueBranchManager,
    IssueData,
    IssueManager,
)
from mcp_coder.workflow_utils.label_transitions import update_workflow_label

# Mock label configuration
MOCK_LABELS_CONFIG: Dict[str, Any] = {
    "workflow_labels": [
        {
            "internal_id": "implementing",
            "name": "status-06:implementing",
            "color": "bfdbfe",
            "description": "Code being written",
            "category": "bot_busy",
        },
        {
            "internal_id": "code_review",
            "name": "status-07:code-review",
            "color": "f59e0b",
            "description": "Implementation complete",
            "category": "human_action",
        },
        {
            "internal_id": "planning",
            "name": "status-03:planning",
            "color": "bfdbfe",
            "description": "Planning in progress",
            "category": "bot_busy",
        },
        {
            "internal_id": "plan_review",
            "name": "status-04:plan-review",
            "color": "f59e0b",
            "description": "Plan ready for review",
            "category": "human_action",
        },
    ],
    "ignore_labels": [],
}

# All workflow label names from the config
ALL_WORKFLOW_NAMES = {
    "status-06:implementing",
    "status-07:code-review",
    "status-03:planning",
    "status-04:plan-review",
}


@pytest.fixture
def mock_github() -> Mock:
    """Mock GitHub client and repository with issue data."""
    mock_repo = Mock()
    mock_issue = Mock()

    mock_label_implementing = Mock()
    mock_label_implementing.name = "status-06:implementing"
    mock_label_bug = Mock()
    mock_label_bug.name = "bug"

    mock_issue.number = 123
    mock_issue.labels = [mock_label_implementing, mock_label_bug]
    mock_repo.get_issue.return_value = mock_issue

    return mock_repo


@pytest.fixture
def _mock_git_repo() -> Any:
    """Mock _init_with_project_dir to avoid git repository checks."""

    def _fake_init(self: Any, project_dir: Any) -> None:
        self.project_dir = project_dir
        self._repo_full_name = None  # pylint: disable=protected-access

    with patch.object(
        BaseGitHubManager,
        "_init_with_project_dir",
        _fake_init,
    ):
        yield


class TestLabelTransitions:
    """Test suite for standalone update_workflow_label() function."""

    def test_update_workflow_label_success_happy_path(
        self,
        mock_github: Mock,
        _mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests successful label transition with all prerequisites met."""
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.workflow_utils.label_transitions.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.workflow_utils.label_transitions.get_current_branch_name",
                return_value="123-feature",
            ),
            patch.object(
                IssueManager, "transition_issue_label", return_value=True
            ) as mock_transition,
        ):
            mock_config.return_value = {("github", "token"): "dummy-token"}

            manager = IssueManager(project_dir=tmp_path)
            result = update_workflow_label(manager, "implementing", "code_review")

            assert result is True

            mock_transition.assert_called_once()
            call_args = mock_transition.call_args
            assert call_args[0][0] == 123  # issue_number
            assert call_args[0][1] == "status-07:code-review"  # new_label
            # labels_to_clear should contain all workflow names except target
            labels_to_clear = call_args[0][2]
            assert "status-07:code-review" not in labels_to_clear
            assert "status-06:implementing" in labels_to_clear

    def test_update_workflow_label_invalid_branch_name(
        self,
        mock_github: Mock,
        _mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests branch name that doesn't match {number}-{title} pattern."""
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.workflow_utils.label_transitions.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch(
                "mcp_coder.workflow_utils.label_transitions.get_current_branch_name",
                return_value="feature-branch",  # No issue number
            ),
        ):
            mock_config.return_value = {("github", "token"): "dummy-token"}

            manager = IssueManager(project_dir=tmp_path)
            result = update_workflow_label(manager, "implementing", "code_review")

            assert result is False
            assert "WARNING" in caplog.text or "does not match" in caplog.text.lower()

    def test_update_workflow_label_branch_not_linked(
        self,
        mock_github: Mock,
        _mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests branch that exists but isn't linked to the issue."""
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.workflow_utils.label_transitions.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager,
                "get_linked_branches",
                return_value=[],
            ),
            patch(
                "mcp_coder.workflow_utils.label_transitions.get_current_branch_name",
                return_value="123-feature",
            ),
        ):
            mock_config.return_value = {("github", "token"): "dummy-token"}

            manager = IssueManager(project_dir=tmp_path)
            result = update_workflow_label(manager, "implementing", "code_review")

            assert result is False
            assert "WARNING" in caplog.text or "not linked" in caplog.text.lower()

    def test_update_workflow_label_already_correct_state(
        self,
        mock_github: Mock,
        _mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests idempotent behavior - transition_issue_label handles this."""
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.workflow_utils.label_transitions.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.workflow_utils.label_transitions.get_current_branch_name",
                return_value="123-feature",
            ),
            patch.object(
                IssueManager, "transition_issue_label", return_value=True
            ) as mock_transition,
        ):
            mock_config.return_value = {("github", "token"): "dummy-token"}

            manager = IssueManager(project_dir=tmp_path)
            result = update_workflow_label(manager, "implementing", "code_review")

            # transition_issue_label handles idempotency internally
            assert result is True
            mock_transition.assert_called_once()

    def test_update_workflow_label_missing_source_label(
        self,
        mock_github: Mock,
        _mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests transition when issue doesn't have source label."""
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.workflow_utils.label_transitions.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.workflow_utils.label_transitions.get_current_branch_name",
                return_value="123-feature",
            ),
            patch.object(
                IssueManager, "transition_issue_label", return_value=True
            ) as mock_transition,
        ):
            mock_config.return_value = {("github", "token"): "dummy-token"}

            manager = IssueManager(project_dir=tmp_path)
            result = update_workflow_label(manager, "implementing", "code_review")

            assert result is True
            mock_transition.assert_called_once()
            call_args = mock_transition.call_args
            assert call_args[0][1] == "status-07:code-review"

    def test_update_workflow_label_label_not_in_config(
        self,
        mock_github: Mock,
        _mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests when internal_id doesn't exist in labels.json."""
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.workflow_utils.label_transitions.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.workflow_utils.label_transitions.get_current_branch_name",
                return_value="123-feature",
            ),
        ):
            mock_config.return_value = {("github", "token"): "dummy-token"}

            manager = IssueManager(project_dir=tmp_path)
            result = update_workflow_label(manager, "invalid_source", "invalid_target")

            assert result is False
            assert "ERROR" in caplog.text or "not found" in caplog.text.lower()

    def test_update_workflow_label_github_api_error(
        self,
        mock_github: Mock,
        _mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests GitHub API failure during label update."""
        from github.GithubException import GithubException

        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.workflow_utils.label_transitions.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.workflow_utils.label_transitions.get_current_branch_name",
                return_value="123-feature",
            ),
            patch.object(
                IssueManager,
                "transition_issue_label",
                side_effect=GithubException(500, "API Error"),
            ),
        ):
            mock_config.return_value = {("github", "token"): "dummy-token"}

            manager = IssueManager(project_dir=tmp_path)
            result = update_workflow_label(manager, "implementing", "code_review")

            assert result is False
            assert "ERROR" in caplog.text or "failed" in caplog.text.lower()

    def test_update_workflow_label_no_branch_provided(
        self,
        mock_github: Mock,
        _mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests automatic branch name detection from git."""
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.workflow_utils.label_transitions.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.workflow_utils.label_transitions.get_current_branch_name",
                return_value="123-feature",
            ) as mock_get_branch,
            patch.object(
                IssueManager, "transition_issue_label", return_value=True
            ) as mock_transition,
        ):
            mock_config.return_value = {("github", "token"): "dummy-token"}

            manager = IssueManager(project_dir=tmp_path)
            result = update_workflow_label(manager, "implementing", "code_review")

            assert result is True
            mock_get_branch.assert_called_once()
            mock_transition.assert_called_once()

    def test_update_workflow_label_removes_different_workflow_label(
        self,
        mock_github: Mock,
        _mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests that labels_to_clear includes ALL workflow labels except target.

        The standalone function computes labels_to_clear = all_names - {target}
        and passes it to transition_issue_label, which handles the actual removal.
        """
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.workflow_utils.label_transitions.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.workflow_utils.label_transitions.get_current_branch_name",
                return_value="123-feature",
            ),
            patch.object(
                IssueManager, "transition_issue_label", return_value=True
            ) as mock_transition,
        ):
            mock_config.return_value = {("github", "token"): "dummy-token"}

            manager = IssueManager(project_dir=tmp_path)
            result = update_workflow_label(manager, "implementing", "code_review")

            assert result is True
            mock_transition.assert_called_once()

            call_args = mock_transition.call_args
            labels_to_clear = set(call_args[0][2])

            # Target label should NOT be in labels_to_clear
            assert "status-07:code-review" not in labels_to_clear

            # All OTHER workflow labels should be in labels_to_clear
            assert "status-06:implementing" in labels_to_clear
            assert "status-03:planning" in labels_to_clear
            assert "status-04:plan-review" in labels_to_clear

    def test_update_workflow_label_with_validated_issue_number(
        self, mock_github: Mock, _mock_git_repo: Any, tmp_path: Path
    ) -> None:
        """Tests that validated_issue_number skips branch linkage validation."""
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.workflow_utils.label_transitions.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=[]
            ) as mock_get_linked,
            patch.object(
                IssueManager, "transition_issue_label", return_value=True
            ) as mock_transition,
        ):
            mock_config.return_value = {("github", "token"): "dummy-token"}

            manager = IssueManager(project_dir=tmp_path)
            result = update_workflow_label(
                manager, "implementing", "code_review", validated_issue_number=123
            )

            assert result is True
            mock_get_linked.assert_not_called()

            mock_transition.assert_called_once()
            call_args = mock_transition.call_args
            assert call_args[0][0] == 123
            assert call_args[0][1] == "status-07:code-review"
            labels_to_clear = call_args[0][2]
            assert "status-06:implementing" in labels_to_clear
            assert "status-07:code-review" not in labels_to_clear

    def test_update_workflow_label_validated_issue_number_invalid(
        self, mock_github: Mock, _mock_git_repo: Any, tmp_path: Path
    ) -> None:
        """Tests that invalid validated_issue_number fails gracefully."""
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.workflow_utils.label_transitions.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(IssueManager, "transition_issue_label", return_value=False),
        ):
            mock_config.return_value = {("github", "token"): "dummy-token"}

            manager = IssueManager(project_dir=tmp_path)
            result = update_workflow_label(
                manager, "implementing", "code_review", validated_issue_number=99999
            )

            assert result is False

    def test_update_workflow_label_race_condition_scenario(
        self, mock_github: Mock, _mock_git_repo: Any, tmp_path: Path
    ) -> None:
        """Tests the race condition: linkedBranches empty after PR creation.

        Caller provides validated_issue_number from earlier validation,
        so label update succeeds despite empty linkedBranches.
        """
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.workflow_utils.label_transitions.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(IssueBranchManager, "get_linked_branches", return_value=[]),
            patch.object(
                IssueManager, "transition_issue_label", return_value=True
            ) as mock_transition,
        ):
            mock_config.return_value = {("github", "token"): "dummy-token"}

            manager = IssueManager(project_dir=tmp_path)
            result = update_workflow_label(
                manager, "implementing", "code_review", validated_issue_number=123
            )

            assert result is True

            mock_transition.assert_called_once()
            call_args = mock_transition.call_args
            assert call_args[0][0] == 123
            assert call_args[0][1] == "status-07:code-review"
            labels_to_clear = call_args[0][2]
            assert "status-06:implementing" in labels_to_clear
            assert "status-07:code-review" not in labels_to_clear
