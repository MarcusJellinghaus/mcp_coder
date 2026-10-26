from unittest.mock import Mock

import pytest

from mcp_coder.mcp_workspace_github import RepoIdentifier
from mcp_coder.workflows.vscodeclaude.issues import (
    _filter_eligible_vscodeclaude_issues,
    get_cached_eligible_vscodeclaude_issues,
    get_eligible_vscodeclaude_issues,
    get_human_action_labels,
)
from tests.github_factories import make_issue_data


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

        # Mock _load_labels_config to return our test config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues._load_labels_config",
            lambda: mock_labels_config,
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
            make_issue_data(
                labels=["status-07:code-review"],
                assignees=["testuser"],
            ),
            make_issue_data(
                number=2,
                labels=["status-07:code-review"],
                assignees=["otheruser"],
            ),
            make_issue_data(
                number=3,
                labels=["status-07:code-review"],
                assignees=[],  # Unassigned
            ),
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

        # Mock _load_labels_config to return our test config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues._load_labels_config",
            lambda: mock_labels_config,
        )

        eligible = get_eligible_vscodeclaude_issues(mock_issue_manager, "testuser")

        assert len(eligible) == 1
        assert eligible[0]["number"] == 1

    def test_get_eligible_issues_priority_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Issues sorted by priority (later stages first)."""
        mock_issues = [
            make_issue_data(labels=["status-01:created"], assignees=["user"]),
            make_issue_data(
                number=2, labels=["status-07:code-review"], assignees=["user"]
            ),
            make_issue_data(
                number=3, labels=["status-04:plan-review"], assignees=["user"]
            ),
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

        # Mock _load_labels_config to return our test config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues._load_labels_config",
            lambda: mock_labels_config,
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
            make_issue_data(
                labels=["status-07:code-review", "Overview"], assignees=["user"]
            ),
            make_issue_data(
                number=2, labels=["status-07:code-review"], assignees=["user"]
            ),
        ]

        mock_issue_manager = Mock()
        mock_issue_manager.list_issues.return_value = mock_issues

        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Mock _load_labels_config to return our test config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues._load_labels_config",
            lambda: mock_labels_config,
        )

        eligible = get_eligible_vscodeclaude_issues(mock_issue_manager, "user")

        assert len(eligible) == 1
        assert eligible[0]["number"] == 2


class TestFilterEligibleVscodeclaudeIssues:
    """Test _filter_eligible_vscodeclaude_issues helper function."""

    def test_filter_eligible_issues_filters_correctly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Filters pre-fetched issues by eligibility criteria."""
        # Pre-fetched issues list (simulating cache data)
        all_issues = [
            make_issue_data(
                title="Eligible issue",
                labels=["status-07:code-review"],
                assignees=["testuser"],
            ),
            make_issue_data(
                number=2,
                title="Wrong assignee",
                labels=["status-07:code-review"],
                assignees=["otheruser"],
            ),
            make_issue_data(
                number=3,
                title="Closed issue",
                state="closed",
                labels=["status-07:code-review"],
                assignees=["testuser"],
            ),
            make_issue_data(
                number=4,
                title="Has ignore label",
                labels=["status-07:code-review", "Overview"],
                assignees=["testuser"],
            ),
        ]

        # Mock labels config
        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Mock _load_labels_config to return our test config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues._load_labels_config",
            lambda: mock_labels_config,
        )

        eligible = _filter_eligible_vscodeclaude_issues(all_issues, "testuser")

        # Should only have issue #1 (others filtered out)
        assert len(eligible) == 1
        assert eligible[0]["number"] == 1

    def test_filter_eligible_issues_sorts_by_priority(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Issues are sorted by VSCODECLAUDE_PRIORITY."""
        all_issues = [
            make_issue_data(
                title="Created", labels=["status-01:created"], assignees=["user"]
            ),
            make_issue_data(
                number=2,
                title="Code review",
                labels=["status-07:code-review"],
                assignees=["user"],
            ),
        ]

        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-01:created", "category": "human_action"},
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": [],
        }

        # Mock _load_labels_config to return our test config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues._load_labels_config",
            lambda: mock_labels_config,
        )

        eligible = _filter_eligible_vscodeclaude_issues(all_issues, "user")

        # Code review comes before created in priority
        assert len(eligible) == 2
        assert eligible[0]["number"] == 2  # code-review first
        assert eligible[1]["number"] == 1  # created second


class TestGetCachedEligibleVscodeclaudeIssues:
    """Test get_cached_eligible_vscodeclaude_issues wrapper function."""

    def test_get_cached_eligible_issues_uses_cache(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Calls get_all_cached_issues and filters results."""
        cached_issues = [
            make_issue_data(
                title="Cached issue",
                labels=["status-07:code-review"],
                assignees=["testuser"],
            ),
        ]

        # Mock cache function
        mock_get_all_cached = Mock(return_value=cached_issues)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_all_cached_issues",
            mock_get_all_cached,
        )

        # Mock labels config
        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": [],
        }

        # Mock _load_labels_config to return our test config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues._load_labels_config",
            lambda: mock_labels_config,
        )

        mock_issue_manager = Mock()

        # Call function
        eligible = get_cached_eligible_vscodeclaude_issues(
            repo_full_name="owner/repo",
            issue_manager=mock_issue_manager,
            github_username="testuser",
            force_refresh=False,
            cache_refresh_minutes=1440,
        )

        # Verify cache was called
        mock_get_all_cached.assert_called_once_with(
            RepoIdentifier.from_full_name("owner/repo"),
            issue_manager=mock_issue_manager,
            force_refresh=False,
            cache_refresh_minutes=1440,
        )

        # Verify filtering worked
        assert len(eligible) == 1
        assert eligible[0]["number"] == 1

    def test_get_cached_eligible_issues_fallback_on_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Falls back to direct API fetch on cache errors."""
        # Mock cache to raise error
        mock_get_all_cached = Mock(side_effect=ValueError("Cache error"))
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_all_cached_issues",
            mock_get_all_cached,
        )

        # Mock direct API fetch
        api_issues = [
            make_issue_data(
                number=99,
                title="API issue",
                labels=["status-07:code-review"],
                assignees=["testuser"],
            ),
        ]
        mock_issue_manager = Mock()
        mock_issue_manager.list_issues.return_value = api_issues

        # Mock labels config
        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": [],
        }

        # Mock _load_labels_config to return our test config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues._load_labels_config",
            lambda: mock_labels_config,
        )

        # Call function
        eligible = get_cached_eligible_vscodeclaude_issues(
            repo_full_name="owner/repo",
            issue_manager=mock_issue_manager,
            github_username="testuser",
        )

        # Should fall back to API fetch
        mock_issue_manager.list_issues.assert_called_once()
        assert len(eligible) == 1
        assert eligible[0]["number"] == 99
