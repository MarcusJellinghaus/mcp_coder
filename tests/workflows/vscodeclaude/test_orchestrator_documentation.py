"""Tests to verify orchestrator documentation matches implementation."""

import pytest

from mcp_coder.workflows.vscodeclaude.issues import status_requires_linked_branch


class TestDocumentationAccuracy:
    """Verify decision matrix documentation matches actual behavior."""

    def test_status_01_allows_main_fallback(self) -> None:
        """Status-01 allows launching without linked branch (doc scenario 7)."""
        # This is tested via process_eligible_issues behavior
        assert not status_requires_linked_branch("status-01:created")

    def test_status_04_requires_linked_branch(self) -> None:
        """Status-04 requires linked branch (doc scenario 5)."""
        assert status_requires_linked_branch("status-04:plan-review")

    def test_status_07_requires_linked_branch(self) -> None:
        """Status-07 requires linked branch (doc scenario 5)."""
        assert status_requires_linked_branch("status-07:code-review")

    def test_status_10_does_not_require_branch(self) -> None:
        """Status-10 (pr-created) doesn't require linked branch."""
        assert not status_requires_linked_branch("status-10:pr-created")

    def test_other_statuses_do_not_require_branch(self) -> None:
        """Bot statuses don't require linked branch."""
        assert not status_requires_linked_branch("status-02:bot-planning")
        assert not status_requires_linked_branch("status-03:bot-busy")
        assert not status_requires_linked_branch("status-05:bot-pickup")
        assert not status_requires_linked_branch("status-06:bot-busy")
        assert not status_requires_linked_branch("status-08:bot-working")
        assert not status_requires_linked_branch("status-09:bot-busy")
