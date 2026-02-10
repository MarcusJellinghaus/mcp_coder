"""Test issue selection and filtering for VSCode Claude."""

from typing import Any, cast
from unittest.mock import Mock

import pytest

from mcp_coder.utils.github_operations.issues import IssueData
from mcp_coder.workflows.vscodeclaude.issues import (
    _filter_eligible_vscodeclaude_issues,
    build_eligible_issues_with_branch_check,
    get_cached_eligible_vscodeclaude_issues,
    get_eligible_vscodeclaude_issues,
    get_human_action_labels,
    get_ignore_labels,
    get_linked_branch_for_issue,
    get_matching_ignore_label,
    is_status_eligible_for_session,
    status_requires_linked_branch,
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

        # Mock _load_labels_config to return our test config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues._load_labels_config",
            lambda: mock_labels_config,
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


class TestFilterEligibleVscodeclaudeIssues:
    """Test _filter_eligible_vscodeclaude_issues helper function."""

    def test_filter_eligible_issues_filters_correctly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Filters pre-fetched issues by eligibility criteria."""
        # Pre-fetched issues list (simulating cache data)
        all_issues = [
            {
                "number": 1,
                "title": "Eligible issue",
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
                "title": "Wrong assignee",
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
                "title": "Closed issue",
                "body": "",
                "state": "closed",
                "labels": ["status-07:code-review"],
                "assignees": ["testuser"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/3",
                "locked": False,
            },
            {
                "number": 4,
                "title": "Has ignore label",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review", "Overview"],
                "assignees": ["testuser"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/4",
                "locked": False,
            },
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

        # Filter issues - cast for mypy
        eligible = _filter_eligible_vscodeclaude_issues(
            cast(list[IssueData], all_issues), "testuser"
        )

        # Should only have issue #1 (others filtered out)
        assert len(eligible) == 1
        assert eligible[0]["number"] == 1

    def test_filter_eligible_issues_sorts_by_priority(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Issues are sorted by VSCODECLAUDE_PRIORITY."""
        all_issues = [
            {
                "number": 1,
                "title": "Created",
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
                "title": "Code review",
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

        eligible = _filter_eligible_vscodeclaude_issues(
            cast(list[IssueData], all_issues), "user"
        )

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
            {
                "number": 1,
                "title": "Cached issue",
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
            repo_full_name="owner/repo",
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
            {
                "number": 99,
                "title": "API issue",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": ["testuser"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/99",
                "locked": False,
            },
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


class TestNumericPriorityExtraction:
    """Test numeric priority extraction from status labels."""

    def test_extracts_priority_from_standard_labels(self) -> None:
        """Extracts numeric priority from status-NN:name format."""
        from mcp_coder.workflows.vscodeclaude.issues import _get_status_priority

        assert _get_status_priority("status-10:pr-created") == 10
        assert _get_status_priority("status-07:code-review") == 7
        assert _get_status_priority("status-04:plan-review") == 4
        assert _get_status_priority("status-01:created") == 1

    def test_returns_zero_for_non_status_labels(self) -> None:
        """Returns 0 for labels that don't match pattern."""
        from mcp_coder.workflows.vscodeclaude.issues import _get_status_priority

        assert _get_status_priority("bug") == 0
        assert _get_status_priority("priority-high") == 0
        assert _get_status_priority("Overview") == 0
        assert _get_status_priority("") == 0


class TestGetIgnoreLabels:
    """Tests for get_ignore_labels function."""

    def test_returns_set_of_lowercase_labels(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return ignore_labels as lowercase set."""
        mock_labels_config = {
            "workflow_labels": [],
            "ignore_labels": ["Overview", "blocked", "wait"],
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues._load_labels_config",
            lambda: mock_labels_config,
        )

        result = get_ignore_labels()
        assert isinstance(result, set)
        assert "blocked" in result
        assert "wait" in result
        assert "overview" in result

    def test_all_labels_are_lowercase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """All returned labels should be lowercase."""
        mock_labels_config = {
            "workflow_labels": [],
            "ignore_labels": ["Overview", "BLOCKED", "Wait"],
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues._load_labels_config",
            lambda: mock_labels_config,
        )

        result = get_ignore_labels()
        for label in result:
            assert label == label.lower()

    def test_handles_empty_ignore_labels(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should handle missing or empty ignore_labels."""
        mock_labels_config: dict[str, list[str]] = {
            "workflow_labels": [],
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues._load_labels_config",
            lambda: mock_labels_config,
        )

        result = get_ignore_labels()
        assert result == set()


class TestGetMatchingIgnoreLabel:
    """Tests for get_matching_ignore_label function."""

    def test_finds_exact_match(self) -> None:
        """Should find label with exact case."""
        result = get_matching_ignore_label(
            ["status-01:created", "blocked"],
            {"blocked", "wait"},
        )
        assert result == "blocked"

    def test_finds_case_insensitive_match(self) -> None:
        """Should match regardless of case."""
        result = get_matching_ignore_label(
            ["status-01:created", "Blocked"],
            {"blocked", "wait"},
        )
        assert result == "Blocked"  # Preserves original case

    def test_finds_uppercase_match(self) -> None:
        """Should match UPPERCASE labels."""
        result = get_matching_ignore_label(
            ["WAIT", "status-04:plan-review"],
            {"blocked", "wait"},
        )
        assert result == "WAIT"

    def test_returns_first_match(self) -> None:
        """Should return first matching label."""
        result = get_matching_ignore_label(
            ["blocked", "wait"],
            {"blocked", "wait"},
        )
        assert result == "blocked"  # First one

    def test_returns_none_when_no_match(self) -> None:
        """Should return None when no ignore labels found."""
        result = get_matching_ignore_label(
            ["status-01:created", "bug"],
            {"blocked", "wait"},
        )
        assert result is None

    def test_handles_empty_issue_labels(self) -> None:
        """Should handle empty issue labels list."""
        result = get_matching_ignore_label([], {"blocked", "wait"})
        assert result is None

    def test_handles_empty_ignore_labels(self) -> None:
        """Should handle empty ignore labels set."""
        result = get_matching_ignore_label(["blocked"], set())
        assert result is None


class TestIsStatusEligibleForSession:
    """Tests for is_status_eligible_for_session function."""

    @pytest.mark.parametrize(
        "status,expected",
        [
            # Eligible statuses (have initial_command)
            ("status-01:created", True),
            ("status-04:plan-review", True),
            ("status-07:code-review", True),
            # Ineligible - bot_pickup (no vscodeclaude config)
            ("status-02:awaiting-planning", False),
            ("status-05:plan-ready", False),
            ("status-08:ready-pr", False),
            # Ineligible - bot_busy (no vscodeclaude config)
            ("status-03:planning", False),
            ("status-06:implementing", False),
            ("status-09:pr-creating", False),
            # Ineligible - pr-created (has config but null initial_command)
            ("status-10:pr-created", False),
            # Edge cases
            ("", False),
            ("invalid-status", False),
            ("status-99:unknown", False),
        ],
    )
    def test_status_eligibility(self, status: str, expected: bool) -> None:
        """Check if status should have a VSCodeClaude session."""
        result = is_status_eligible_for_session(status)
        assert result == expected, f"Expected {expected} for status '{status}'"


class TestStatusRequiresLinkedBranch:
    """Tests for status_requires_linked_branch()."""

    def test_status_01_does_not_require_branch(self) -> None:
        """status-01:created allows fallback to main."""
        assert status_requires_linked_branch("status-01:created") is False

    def test_status_04_requires_branch(self) -> None:
        """status-04:plan-review requires linked branch."""
        assert status_requires_linked_branch("status-04:plan-review") is True

    def test_status_07_requires_branch(self) -> None:
        """status-07:code-review requires linked branch."""
        assert status_requires_linked_branch("status-07:code-review") is True

    def test_bot_statuses_do_not_require_branch(self) -> None:
        """Bot statuses don't require linked branch."""
        assert status_requires_linked_branch("status-02:bot-pickup") is False
        assert status_requires_linked_branch("status-05:bot-pickup") is False
        assert status_requires_linked_branch("status-08:bot-pickup") is False

    def test_pr_created_does_not_require_branch(self) -> None:
        """status-10:pr-created doesn't require linked branch."""
        assert status_requires_linked_branch("status-10:pr-created") is False

    def test_empty_string_returns_false(self) -> None:
        """Empty string returns False."""
        assert status_requires_linked_branch("") is False

    def test_invalid_status_returns_false(self) -> None:
        """Invalid status string returns False."""
        assert status_requires_linked_branch("invalid") is False
        assert status_requires_linked_branch("status-99:unknown") is False


class TestBuildEligibleIssuesWithBranchCheck:
    """Tests for build_eligible_issues_with_branch_check()."""

    def test_returns_empty_for_no_repos(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty repo list returns empty results."""
        # Mock load_config to return empty repos
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: {"coordinator": {"repos": {}}},
        )

        eligible_issues, issues_without_branch = (
            build_eligible_issues_with_branch_check([])
        )

        assert eligible_issues == []
        assert issues_without_branch == set()

    def test_returns_eligible_issues(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returns eligible issues from all repos."""
        # Mock config
        mock_config = {
            "coordinator": {
                "repos": {
                    "test-repo": {"repo_url": "https://github.com/owner/repo.git"},
                },
                "vscodeclaude": {"github_username": "testuser"},
            }
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: mock_config,
        )

        # Mock vscodeclaude config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_vscodeclaude_config",
            lambda: {"github_username": "testuser"},
        )

        # Mock eligible issues
        mock_issue = {
            "number": 1,
            "title": "Test",
            "body": "",
            "state": "open",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/1",
            "locked": False,
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_cached_eligible_vscodeclaude_issues",
            lambda **kwargs: [mock_issue],
        )

        # Mock get_issue_status
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_issue_status",
            lambda issue: "status-01:created",
        )

        eligible_issues, issues_without_branch = (
            build_eligible_issues_with_branch_check(["test-repo"])
        )

        assert len(eligible_issues) == 1
        assert eligible_issues[0][0] == "owner/repo"
        assert eligible_issues[0][1]["number"] == 1
        assert issues_without_branch == set()

    def test_identifies_status_04_without_branch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Issues at status-04 without linked branch added to set."""
        # Mock config
        mock_config = {
            "coordinator": {
                "repos": {
                    "test-repo": {"repo_url": "https://github.com/owner/repo.git"},
                },
                "vscodeclaude": {"github_username": "testuser"},
            }
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: mock_config,
        )

        # Mock vscodeclaude config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_vscodeclaude_config",
            lambda: {"github_username": "testuser"},
        )

        # Mock issue at status-04
        mock_issue = {
            "number": 1,
            "title": "Test",
            "body": "",
            "state": "open",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/1",
            "locked": False,
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_cached_eligible_vscodeclaude_issues",
            lambda **kwargs: [mock_issue],
        )

        # Mock get_issue_status
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_issue_status",
            lambda issue: "status-04:plan-review",
        )

        # Mock get_linked_branch_for_issue to return None (no branch)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_linked_branch_for_issue",
            lambda branch_manager, issue_number: None,
        )

        eligible_issues, issues_without_branch = (
            build_eligible_issues_with_branch_check(["test-repo"])
        )

        assert len(eligible_issues) == 1
        assert ("owner/repo", 1) in issues_without_branch

    def test_identifies_status_07_without_branch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Issues at status-07 without linked branch added to set."""
        # Mock config
        mock_config = {
            "coordinator": {
                "repos": {
                    "test-repo": {"repo_url": "https://github.com/owner/repo.git"},
                },
                "vscodeclaude": {"github_username": "testuser"},
            }
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: mock_config,
        )

        # Mock vscodeclaude config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_vscodeclaude_config",
            lambda: {"github_username": "testuser"},
        )

        # Mock issue at status-07
        mock_issue = {
            "number": 2,
            "title": "Test",
            "body": "",
            "state": "open",
            "labels": ["status-07:code-review"],
            "assignees": ["testuser"],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/2",
            "locked": False,
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_cached_eligible_vscodeclaude_issues",
            lambda **kwargs: [mock_issue],
        )

        # Mock get_issue_status
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_issue_status",
            lambda issue: "status-07:code-review",
        )

        # Mock get_linked_branch_for_issue to return None (no branch)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_linked_branch_for_issue",
            lambda branch_manager, issue_number: None,
        )

        eligible_issues, issues_without_branch = (
            build_eligible_issues_with_branch_check(["test-repo"])
        )

        assert len(eligible_issues) == 1
        assert ("owner/repo", 2) in issues_without_branch

    def test_handles_multiple_branches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Issues with multiple linked branches added to set."""
        # Mock config
        mock_config = {
            "coordinator": {
                "repos": {
                    "test-repo": {"repo_url": "https://github.com/owner/repo.git"},
                },
                "vscodeclaude": {"github_username": "testuser"},
            }
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: mock_config,
        )

        # Mock vscodeclaude config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_vscodeclaude_config",
            lambda: {"github_username": "testuser"},
        )

        # Mock issue at status-04
        mock_issue = {
            "number": 3,
            "title": "Test",
            "body": "",
            "state": "open",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/3",
            "locked": False,
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_cached_eligible_vscodeclaude_issues",
            lambda **kwargs: [mock_issue],
        )

        # Mock get_issue_status
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_issue_status",
            lambda issue: "status-04:plan-review",
        )

        # Mock get_linked_branch_for_issue to raise ValueError (multiple branches)
        def mock_get_linked_branch(branch_manager: Mock, issue_number: int) -> None:
            raise ValueError("Multiple branches")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_linked_branch_for_issue",
            mock_get_linked_branch,
        )

        eligible_issues, issues_without_branch = (
            build_eligible_issues_with_branch_check(["test-repo"])
        )

        assert len(eligible_issues) == 1
        assert ("owner/repo", 3) in issues_without_branch

    def test_status_01_without_branch_not_in_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-01 issues without branch NOT added to set."""
        # Mock config
        mock_config = {
            "coordinator": {
                "repos": {
                    "test-repo": {"repo_url": "https://github.com/owner/repo.git"},
                },
                "vscodeclaude": {"github_username": "testuser"},
            }
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: mock_config,
        )

        # Mock vscodeclaude config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_vscodeclaude_config",
            lambda: {"github_username": "testuser"},
        )

        # Mock issue at status-01
        mock_issue = {
            "number": 4,
            "title": "Test",
            "body": "",
            "state": "open",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/4",
            "locked": False,
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_cached_eligible_vscodeclaude_issues",
            lambda **kwargs: [mock_issue],
        )

        # Mock get_issue_status
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_issue_status",
            lambda issue: "status-01:created",
        )

        # Mock get_linked_branch_for_issue to return None (no branch)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_linked_branch_for_issue",
            lambda branch_manager, issue_number: None,
        )

        eligible_issues, issues_without_branch = (
            build_eligible_issues_with_branch_check(["test-repo"])
        )

        assert len(eligible_issues) == 1
        assert ("owner/repo", 4) not in issues_without_branch
        assert issues_without_branch == set()

    def test_continues_on_repo_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Continues processing if one repo fails."""
        # Mock config with two repos
        mock_config = {
            "coordinator": {
                "repos": {
                    "bad-repo": {"repo_url": "https://github.com/owner/bad.git"},
                    "good-repo": {"repo_url": "https://github.com/owner/good.git"},
                },
                "vscodeclaude": {"github_username": "testuser"},
            }
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_config",
            lambda: mock_config,
        )

        # Mock vscodeclaude config
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.load_vscodeclaude_config",
            lambda: {"github_username": "testuser"},
        )

        # Mock get_cached_eligible_vscodeclaude_issues to fail for bad-repo
        def mock_get_cached(repo_full_name: str, **kwargs: Any) -> list[dict[str, Any]]:
            if "bad" in repo_full_name:
                raise Exception("API error")
            return [
                {
                    "number": 5,
                    "title": "Good issue",
                    "body": "",
                    "state": "open",
                    "labels": ["status-01:created"],
                    "assignees": ["testuser"],
                    "user": None,
                    "created_at": None,
                    "updated_at": None,
                    "url": "https://github.com/owner/good/issues/5",
                    "locked": False,
                }
            ]

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_cached_eligible_vscodeclaude_issues",
            mock_get_cached,
        )

        # Mock get_issue_status
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.get_issue_status",
            lambda issue: "status-01:created",
        )

        eligible_issues, issues_without_branch = (
            build_eligible_issues_with_branch_check(["bad-repo", "good-repo"])
        )

        # Should have issue from good-repo only
        assert len(eligible_issues) == 1
        assert eligible_issues[0][0] == "owner/good"
        assert eligible_issues[0][1]["number"] == 5
