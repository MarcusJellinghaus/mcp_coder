"""Tests for define_labels stale timeout configuration.

Tests cover:
- Stale timeout configuration validation
- Expected timeout values match requirements
"""

from pathlib import Path

from mcp_coder.utils.github_operations.label_config import load_labels_config


class TestStaleTimeoutConfiguration:
    """Test stale_timeout_minutes field in labels configuration."""

    def test_bot_busy_labels_have_stale_timeout(self, labels_config_path: Path) -> None:
        """Test that all bot_busy labels have stale_timeout_minutes field."""
        labels_config = load_labels_config(labels_config_path)

        bot_busy_labels = [
            label
            for label in labels_config["workflow_labels"]
            if label.get("category") == "bot_busy"
        ]

        # Ensure we have bot_busy labels to test
        assert len(bot_busy_labels) > 0, "Should have at least one bot_busy label"

        for label in bot_busy_labels:
            assert (
                "stale_timeout_minutes" in label
            ), f"bot_busy label '{label['name']}' should have stale_timeout_minutes field"

    def test_stale_timeout_values_are_positive_integers(
        self, labels_config_path: Path
    ) -> None:
        """Test that stale_timeout_minutes values are positive integers."""
        labels_config = load_labels_config(labels_config_path)

        bot_busy_labels = [
            label
            for label in labels_config["workflow_labels"]
            if label.get("category") == "bot_busy"
        ]

        for label in bot_busy_labels:
            timeout = label.get("stale_timeout_minutes")
            assert isinstance(
                timeout, int
            ), f"stale_timeout_minutes for '{label['name']}' should be an integer"
            assert (
                timeout > 0
            ), f"stale_timeout_minutes for '{label['name']}' should be positive"

    def test_expected_timeout_values(self, labels_config_path: Path) -> None:
        """Test specific timeout values match requirements."""
        labels_config = load_labels_config(labels_config_path)

        # Build lookup by internal_id
        labels_by_id = {
            label["internal_id"]: label for label in labels_config["workflow_labels"]
        }

        # Expected timeout values per spec
        expected_timeouts = {
            "planning": 15,
            "implementing": 120,
            "pr_creating": 15,
        }

        for internal_id, expected_timeout in expected_timeouts.items():
            assert (
                internal_id in labels_by_id
            ), f"Label with internal_id '{internal_id}' should exist"
            label = labels_by_id[internal_id]
            actual_timeout = label.get("stale_timeout_minutes")
            assert actual_timeout == expected_timeout, (
                f"stale_timeout_minutes for '{internal_id}' should be {expected_timeout}, "
                f"got {actual_timeout}"
            )
