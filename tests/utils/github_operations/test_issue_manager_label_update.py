"""Test suite for IssueManager.update_workflow_label() method.

This module tests the automatic label update functionality that transitions
workflow labels when operations complete successfully.
"""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_coder.utils.github_operations.issue_branch_manager import IssueBranchManager
from mcp_coder.utils.github_operations.issue_manager import IssueData, IssueManager

# Mock label configuration
MOCK_LABELS_CONFIG = {
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


@pytest.fixture
def mock_github() -> Mock:
    """Mock GitHub client and repository with issue data.

    Returns:
        Mock object configured to simulate GitHub API responses.
    """
    mock_repo = Mock()
    mock_issue = Mock()

    # Configure issue with labels
    mock_label_implementing = Mock()
    mock_label_implementing.name = "status-06:implementing"
    mock_label_bug = Mock()
    mock_label_bug.name = "bug"

    mock_issue.number = 123
    mock_issue.labels = [mock_label_implementing, mock_label_bug]
    mock_repo.get_issue.return_value = mock_issue

    return mock_repo


@pytest.fixture
def mock_label_config() -> Dict[str, Any]:
    """Mock label configuration loading.

    Returns:
        Dictionary containing test label configuration.
    """
    return MOCK_LABELS_CONFIG


@pytest.fixture
def mock_git_operations() -> Mock:
    """Mock git operations for branch name detection.

    Returns:
        Mock object for get_current_branch_name().
    """
    mock_git = Mock()
    mock_git.return_value = "123-feature"
    return mock_git


@pytest.fixture
def mock_git_repo() -> Any:
    """Mock is_git_repository to avoid subprocess calls.

    This fixture eliminates the need for actual git init in tests,
    significantly improving test performance.
    """
    with patch(
        "mcp_coder.utils.github_operations.base_manager.git_operations.is_git_repository",
        return_value=True,
    ):
        yield


class TestIssueManagerLabelUpdate:
    """Test suite for IssueManager.update_workflow_label() method."""

    def test_update_workflow_label_success_happy_path(
        self,
        mock_github: Mock,
        mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests successful label transition with all prerequisites met.

        Verifies that when a branch is properly linked to an issue and all
        conditions are met, the label successfully transitions from source
        to target state.
        """
        # Create mock issue data that get_issue will return
        mock_issue_data: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "labels": ["status-06:implementing", "bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/test/test/issues/123",
            "locked": False,
        }

        # Setup mocks
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.get_current_branch_name",
                return_value="123-feature",
            ),
            patch.object(IssueManager, "get_issue", return_value=mock_issue_data),
            patch.object(IssueManager, "set_labels") as mock_set_labels,
        ):
            # Configure mocks
            mock_config.return_value = {("github", "token"): "dummy-token"}
            mock_set_labels.return_value = mock_issue_data

            # Create manager and call update
            manager = IssueManager(project_dir=tmp_path)
            result = manager.update_workflow_label("implementing", "code_review")

            # Assert success
            assert result is True

            # Verify set_labels was called with correct label set
            mock_set_labels.assert_called_once()
            call_args = mock_set_labels.call_args[0]
            issue_number = call_args[0]
            labels = call_args[1:]

            assert issue_number == 123
            assert "status-07:code-review" in labels
            assert "status-06:implementing" not in labels
            assert "bug" in labels  # Other labels preserved

    def test_update_workflow_label_invalid_branch_name(
        self,
        mock_github: Mock,
        mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests branch name that doesn't match {number}-{title} pattern.

        Verifies that branches without a leading issue number are rejected
        gracefully with appropriate warning messages.
        """
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.get_current_branch_name",
                return_value="feature-branch",  # No issue number
            ),
        ):
            # Configure mock token
            mock_config.return_value = {("github", "token"): "dummy-token"}

            # Create manager and call update
            manager = IssueManager(project_dir=tmp_path)
            result = manager.update_workflow_label("implementing", "code_review")

            # Assert failure
            assert result is False

            # Verify appropriate log message
            assert "WARNING" in caplog.text or "does not match" in caplog.text.lower()

    def test_update_workflow_label_branch_not_linked(
        self,
        mock_github: Mock,
        mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests branch that exists but isn't linked to the issue.

        Verifies that unlinked branches (not in get_linked_branches result)
        are rejected for safety.
        """
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager,
                "get_linked_branches",
                return_value=[],  # No linked branches
            ),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.get_current_branch_name",
                return_value="123-feature",
            ),
        ):
            # Configure mock token
            mock_config.return_value = {("github", "token"): "dummy-token"}

            # Create manager and call update
            manager = IssueManager(project_dir=tmp_path)
            result = manager.update_workflow_label("implementing", "code_review")

            # Assert failure
            assert result is False

            # Verify appropriate log message
            assert "WARNING" in caplog.text or "not linked" in caplog.text.lower()

    def test_update_workflow_label_already_correct_state(
        self,
        mock_github: Mock,
        mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests idempotent behavior - issue already has target label.

        Verifies that if the issue already has the target label and doesn't
        have the source label, the operation succeeds without making changes.
        """
        # Configure issue to already have target label (without source label)
        mock_issue_data: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "labels": ["status-07:code-review", "bug"],  # Already has target, no source
            "assignees": [],
            "user": "testuser",
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/test/test/issues/123",
            "locked": False,
        }

        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.get_current_branch_name",
                return_value="123-feature",
            ),
            patch.object(IssueManager, "get_issue", return_value=mock_issue_data),
            patch.object(IssueManager, "set_labels") as mock_set_labels,
        ):
            # Configure mock token
            mock_config.return_value = {("github", "token"): "dummy-token"}

            # Create manager and call update
            manager = IssueManager(project_dir=tmp_path)
            result = manager.update_workflow_label("implementing", "code_review")

            # Assert success (idempotent)
            assert result is True

            # Verify set_labels was not called (no change needed)
            mock_set_labels.assert_not_called()

    def test_update_workflow_label_missing_source_label(
        self,
        mock_github: Mock,
        mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests transition when issue doesn't have source label.

        Verifies that missing source labels are handled gracefully - the
        target label is still added if not present.
        """
        # Configure issue without source label
        mock_issue_data: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "labels": ["bug"],  # No implementing label
            "assignees": [],
            "user": "testuser",
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/test/test/issues/123",
            "locked": False,
        }

        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.get_current_branch_name",
                return_value="123-feature",
            ),
            patch.object(IssueManager, "get_issue", return_value=mock_issue_data),
            patch.object(IssueManager, "set_labels") as mock_set_labels,
        ):
            # Configure mocks
            mock_config.return_value = {("github", "token"): "dummy-token"}
            mock_set_labels.return_value = mock_issue_data

            # Create manager and call update
            manager = IssueManager(project_dir=tmp_path)
            result = manager.update_workflow_label("implementing", "code_review")

            # Assert success (adds target label)
            assert result is True

            # Verify set_labels was called to add target label
            mock_set_labels.assert_called_once()
            call_args = mock_set_labels.call_args[0]
            labels = call_args[1:]

            assert "status-07:code-review" in labels
            assert "bug" in labels

    def test_update_workflow_label_label_not_in_config(
        self,
        mock_github: Mock,
        mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests when internal_id doesn't exist in labels.json.

        Verifies that invalid internal IDs (not found in config) are
        rejected with appropriate error messages.
        """
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.get_current_branch_name",
                return_value="123-feature",
            ),
        ):
            # Configure mock token
            mock_config.return_value = {("github", "token"): "dummy-token"}

            # Create manager and call update with invalid internal_id
            manager = IssueManager(project_dir=tmp_path)
            result = manager.update_workflow_label("invalid_source", "invalid_target")

            # Assert failure
            assert result is False

            # Verify appropriate error message
            assert "ERROR" in caplog.text or "not found" in caplog.text.lower()

    def test_update_workflow_label_github_api_error(
        self,
        mock_github: Mock,
        mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests GitHub API failure during label update.

        Verifies that API errors (like network failures or rate limiting)
        are caught and logged without raising exceptions.
        """
        from github.GithubException import GithubException

        # Create mock issue data that get_issue will return
        mock_issue_data: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "labels": ["status-06:implementing", "bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/test/test/issues/123",
            "locked": False,
        }

        # Configure set_labels to raise exception
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.get_current_branch_name",
                return_value="123-feature",
            ),
            patch.object(IssueManager, "get_issue", return_value=mock_issue_data),
            patch.object(
                IssueManager,
                "set_labels",
                side_effect=GithubException(500, "API Error"),
            ),
        ):
            # Configure mock token
            mock_config.return_value = {("github", "token"): "dummy-token"}

            # Create manager and call update
            manager = IssueManager(project_dir=tmp_path)
            result = manager.update_workflow_label("implementing", "code_review")

            # Assert failure (non-blocking)
            assert result is False

            # Verify appropriate error message
            assert "ERROR" in caplog.text or "failed" in caplog.text.lower()

    def test_update_workflow_label_no_branch_provided(
        self,
        mock_github: Mock,
        mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests automatic branch name detection from git.

        Verifies that when no branch name is explicitly provided, the
        method automatically detects the current branch from git.
        """
        # Create mock issue data that get_issue will return
        mock_issue_data: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "labels": ["status-06:implementing", "bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/test/test/issues/123",
            "locked": False,
        }

        # Setup mocks
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.get_current_branch_name",
                return_value="123-feature",
            ) as mock_get_branch,
            patch.object(IssueManager, "get_issue", return_value=mock_issue_data),
            patch.object(IssueManager, "set_labels") as mock_set_labels,
        ):
            # Configure mocks
            mock_config.return_value = {("github", "token"): "dummy-token"}
            mock_set_labels.return_value = mock_issue_data

            # Create manager and call update without branch parameter
            manager = IssueManager(project_dir=tmp_path)
            result = manager.update_workflow_label("implementing", "code_review")

            # Assert success
            assert result is True

            # Verify get_current_branch_name was called
            mock_get_branch.assert_called_once()

            # Verify set_labels was called
            mock_set_labels.assert_called_once()

    def test_update_workflow_label_removes_different_workflow_label(
        self,
        mock_github: Mock,
        mock_git_repo: Any,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests that transitioning removes ALL workflow labels, not just the source.

        Scenario: Issue has 'planning' label, but we're transitioning from
        'implementing' to 'code_review'. The 'planning' workflow label should
        also be removed, leaving only the target 'code_review' label.

        This test verifies the bug fix where workflow labels other than the
        source label were not being removed during transitions.
        """
        import logging

        caplog.set_level(logging.INFO)

        # Configure issue with a DIFFERENT workflow label (planning instead of implementing)
        # This simulates the bug scenario where a different workflow label exists
        mock_issue_data: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "labels": ["status-03:planning", "bug"],  # Has 'planning' workflow label
            "assignees": [],
            "user": "testuser",
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/test/test/issues/123",
            "locked": False,
        }

        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=["123-feature"]
            ),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.get_current_branch_name",
                return_value="123-feature",
            ),
            patch.object(IssueManager, "get_issue", return_value=mock_issue_data),
            patch.object(IssueManager, "set_labels") as mock_set_labels,
        ):
            # Configure mocks
            mock_config.return_value = {("github", "token"): "dummy-token"}
            mock_set_labels.return_value = mock_issue_data

            # Create manager and call update
            # Transitioning from implementing -> code_review
            # but issue has 'planning' label which should also be removed
            manager = IssueManager(project_dir=tmp_path)
            result = manager.update_workflow_label("implementing", "code_review")

            # Assert success
            assert result is True

            # Verify set_labels was called
            mock_set_labels.assert_called_once()
            call_args = mock_set_labels.call_args[0]
            labels = set(call_args[1:])  # Convert to set for easier assertion

            # The target label should be present
            assert "status-07:code-review" in labels

            # The 'planning' workflow label should be REMOVED
            # This is the key assertion - currently fails due to the bug
            assert "status-03:planning" not in labels

            # Non-workflow labels should be preserved
            assert "bug" in labels

            # Verify INFO log was emitted for missing source label
            assert "Source label 'status-06:implementing' not present" in caplog.text

    def test_update_workflow_label_with_validated_issue_number(
        self, mock_github: Mock, mock_git_repo: Any, tmp_path: Path
    ) -> None:
        """Tests that validated_issue_number skips branch linkage validation."""
        # Create mock issue data that get_issue will return
        mock_issue_data: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "labels": ["status-06:implementing", "bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/test/test/issues/123",
            "locked": False,
        }

        # Setup mocks - importantly, get_linked_branches returns empty list (post-PR state)
        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(
                IssueBranchManager, "get_linked_branches", return_value=[]
            ) as mock_get_linked,
            patch.object(IssueManager, "get_issue", return_value=mock_issue_data),
            patch.object(IssueManager, "set_labels") as mock_set_labels,
        ):
            # Configure mocks
            mock_config.return_value = {("github", "token"): "dummy-token"}
            mock_set_labels.return_value = mock_issue_data

            # Create manager and call update with validated_issue_number
            manager = IssueManager(project_dir=tmp_path)
            result = manager.update_workflow_label(
                "implementing", "code_review", validated_issue_number=123
            )

            # Assert success
            assert result is True

            # Assert get_linked_branches was NOT called (skipped branch validation)
            mock_get_linked.assert_not_called()

            # Verify set_labels was called with correct label set
            mock_set_labels.assert_called_once()
            call_args = mock_set_labels.call_args[0]
            issue_number = call_args[0]
            labels = call_args[1:]

            assert issue_number == 123
            assert "status-07:code-review" in labels
            assert "status-06:implementing" not in labels
            assert "bug" in labels  # Other labels preserved

    def test_update_workflow_label_validated_issue_number_invalid(
        self, mock_github: Mock, mock_git_repo: Any, tmp_path: Path
    ) -> None:
        """Tests that invalid validated_issue_number (non-existent issue) fails gracefully."""
        # Create empty issue data to simulate issue not found
        empty_issue_data: IssueData = {
            "number": 0,
            "title": "",
            "body": "",
            "state": "",
            "labels": [],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }

        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            patch.object(IssueManager, "get_issue", return_value=empty_issue_data),
        ):
            # Configure mock token
            mock_config.return_value = {("github", "token"): "dummy-token"}

            # Create manager and call update with invalid validated_issue_number
            manager = IssueManager(project_dir=tmp_path)
            result = manager.update_workflow_label(
                "implementing", "code_review", validated_issue_number=99999
            )

            # Assert failure
            assert result is False

    def test_update_workflow_label_race_condition_scenario(
        self, mock_github: Mock, mock_git_repo: Any, tmp_path: Path
    ) -> None:
        """Tests the race condition: linkedBranches empty after PR creation.

        Simulates:
        1. Branch was linked to issue before PR creation
        2. PR was created (GitHub removes linkedBranches)
        3. Caller provides validated_issue_number from earlier validation
        4. Label update succeeds despite empty linkedBranches
        """
        # Create mock issue data that get_issue will return
        mock_issue_data: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "labels": ["status-06:implementing", "bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/test/test/issues/123",
            "locked": False,
        }

        with (
            patch("mcp_coder.utils.user_config.get_config_values") as mock_config,
            patch.object(IssueManager, "_get_repository", return_value=mock_github),
            patch(
                "mcp_coder.utils.github_operations.issue_manager.load_labels_config",
                return_value=MOCK_LABELS_CONFIG,
            ),
            # Simulate post-PR state: linkedBranches is empty
            patch.object(IssueBranchManager, "get_linked_branches", return_value=[]),
            patch.object(IssueManager, "get_issue", return_value=mock_issue_data),
            patch.object(IssueManager, "set_labels") as mock_set_labels,
        ):
            # Configure mocks
            mock_config.return_value = {("github", "token"): "dummy-token"}
            mock_set_labels.return_value = mock_issue_data

            # Create manager and call update with validated_issue_number
            # This simulates the case where validation occurred before PR creation
            manager = IssueManager(project_dir=tmp_path)
            result = manager.update_workflow_label(
                "implementing", "code_review", validated_issue_number=123
            )

            # Assert success - the race condition is handled
            assert result is True

            # Verify label was updated correctly
            mock_set_labels.assert_called_once()
            call_args = mock_set_labels.call_args[0]
            issue_number = call_args[0]
            labels = call_args[1:]

            assert issue_number == 123
            assert "status-07:code-review" in labels
            assert "status-06:implementing" not in labels
            assert "bug" in labels  # Other labels preserved
