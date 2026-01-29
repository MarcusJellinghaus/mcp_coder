"""Test issue selection and filtering for VSCode Claude."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mcp_coder.utils.vscodeclaude.issues import (
    get_eligible_vscodeclaude_issues,
    get_human_action_labels,
    get_linked_branch_for_issue,
)


class TestIssueSelection:
    """Test issue filtering for vscodeclaude."""

    def test_get_human_action_labels(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Extracts human_action labels from config."""
        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-01:created", "category": "human_action"},
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-04:plan-review", "category": "human_action"},
            ],
            "ignore_labels": ["Overview"],
        }

        def mock_load_labels_config(self: Any, config_path: Path) -> dict[str, Any]:
            return mock_labels_config

        mock_coordinator = type(
            "MockCoordinator", (), {"load_labels_config": mock_load_labels_config}
        )()
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.issues._get_coordinator",
            lambda: mock_coordinator,
        )

        labels = get_human_action_labels()
        assert "status-01:created" in labels
        assert "status-04:plan-review" in labels
        assert "status-02:awaiting-planning" not in labels

    def test_get_eligible_issues_filters_by_assignment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Only returns issues assigned to user."""
        mock_issues = [
            {
                "number": 1,
                "title": "Issue 1",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": ["testuser"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/1",
                "locked": False,
            },
            {
                "number": 2,
                "title": "Issue 2",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": ["otheruser"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/2",
                "locked": False,
            },
            {
                "number": 3,
                "title": "Issue 3",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": [],  # Unassigned
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/3",
                "locked": False,
            },
        ]

        mock_issue_manager = Mock()
        mock_issue_manager.list_issues.return_value = mock_issues

        # Mock labels config
        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": [],
        }

        def mock_load_labels_config(self: Any, config_path: Path) -> dict[str, Any]:
            return mock_labels_config

        mock_coordinator = type(
            "MockCoordinator", (), {"load_labels_config": mock_load_labels_config}
        )()
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.issues._get_coordinator",
            lambda: mock_coordinator,
        )

        eligible = get_eligible_vscodeclaude_issues(mock_issue_manager, "testuser")

        assert len(eligible) == 1
        assert eligible[0]["number"] == 1

    def test_get_eligible_issues_priority_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Issues sorted by priority (later stages first)."""
        mock_issues = [
            {
                "number": 1,
                "title": "Issue 1",
                "body": "",
                "state": "open",
                "labels": ["status-01:created"],
                "assignees": ["user"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/1",
                "locked": False,
            },
            {
                "number": 2,
                "title": "Issue 2",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": ["user"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/2",
                "locked": False,
            },
            {
                "number": 3,
                "title": "Issue 3",
                "body": "",
                "state": "open",
                "labels": ["status-04:plan-review"],
                "assignees": ["user"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/3",
                "locked": False,
            },
        ]

        mock_issue_manager = Mock()
        mock_issue_manager.list_issues.return_value = mock_issues

        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-01:created", "category": "human_action"},
                {"name": "status-04:plan-review", "category": "human_action"},
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": [],
        }

        def mock_load_labels_config(self: Any, config_path: Path) -> dict[str, Any]:
            return mock_labels_config

        mock_coordinator = type(
            "MockCoordinator", (), {"load_labels_config": mock_load_labels_config}
        )()
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.issues._get_coordinator",
            lambda: mock_coordinator,
        )

        eligible = get_eligible_vscodeclaude_issues(mock_issue_manager, "user")

        # Should be: code-review, plan-review, created (index 0, 1, 3 in priority)
        assert len(eligible) == 3
        assert eligible[0]["number"] == 2  # code-review
        assert eligible[1]["number"] == 3  # plan-review
        assert eligible[2]["number"] == 1  # created

    def test_get_eligible_issues_excludes_ignore_labels(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips issues with ignore_labels."""
        mock_issues = [
            {
                "number": 1,
                "title": "Issue 1",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review", "Overview"],
                "assignees": ["user"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/1",
                "locked": False,
            },
            {
                "number": 2,
                "title": "Issue 2",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": ["user"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/2",
                "locked": False,
            },
        ]

        mock_issue_manager = Mock()
        mock_issue_manager.list_issues.return_value = mock_issues

        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": ["Overview"],
        }

        def mock_load_labels_config(self: Any, config_path: Path) -> dict[str, Any]:
            return mock_labels_config

        mock_coordinator = type(
            "MockCoordinator", (), {"load_labels_config": mock_load_labels_config}
        )()
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.issues._get_coordinator",
            lambda: mock_coordinator,
        )

        eligible = get_eligible_vscodeclaude_issues(mock_issue_manager, "user")

        assert len(eligible) == 1
        assert eligible[0]["number"] == 2

    def test_get_linked_branch_single(self) -> None:
        """Returns branch when exactly one linked."""
        mock_branch_manager = Mock()
        mock_branch_manager.get_linked_branches.return_value = ["feature-123"]

        branch = get_linked_branch_for_issue(mock_branch_manager, 123)
        assert branch == "feature-123"

    def test_get_linked_branch_none(self) -> None:
        """Returns None when no branches linked."""
        mock_branch_manager = Mock()
        mock_branch_manager.get_linked_branches.return_value = []

        branch = get_linked_branch_for_issue(mock_branch_manager, 123)
        assert branch is None

    def test_get_linked_branch_multiple_raises(self) -> None:
        """Raises ValueError when multiple branches linked."""
        mock_branch_manager = Mock()
        mock_branch_manager.get_linked_branches.return_value = ["branch-a", "branch-b"]

        with pytest.raises(ValueError, match="multiple branches"):
            get_linked_branch_for_issue(mock_branch_manager, 123)
