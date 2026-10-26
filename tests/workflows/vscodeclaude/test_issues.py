"""Test issue selection and filtering for VSCode Claude."""

import pytest

from mcp_coder.workflows.vscodeclaude.issues import (
    get_ignore_labels,
    get_matching_ignore_label,
    is_status_eligible_for_session,
    status_requires_linked_branch,
)


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
            # Eligible statuses (have commands)
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
            # Ineligible - pr-created (has config but no commands)
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
