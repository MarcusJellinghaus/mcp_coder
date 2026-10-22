"""Tests for is_branch_linked_to_issue."""

import logging
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import ClosingPRRef
from mcp_coder.workflow_utils.branch_linkage import is_branch_linked_to_issue

LOGGER_NAME = "mcp_coder.workflow_utils.branch_linkage"


def _manager(return_value: object) -> MagicMock:
    manager = MagicMock()
    manager.get_linked_branch_and_closing_prs_or_none.return_value = return_value
    return manager


class TestIsBranchLinkedToIssue:
    """Tests for is_branch_linked_to_issue."""

    def test_linked_branch_match(self, caplog: pytest.LogCaptureFixture) -> None:
        """A linked branch with the same name returns True."""
        manager = _manager((["123-feature"], []))

        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            result = is_branch_linked_to_issue(manager, 123, "123-feature")

        assert result is True
        assert any(
            r.levelno == logging.INFO and "linked branch" in r.getMessage()
            for r in caplog.records
        )
        manager.get_linked_branch_and_closing_prs_or_none.assert_called_once_with(123)

    def test_closing_pr_head_match(self, caplog: pytest.LogCaptureFixture) -> None:
        """An open closing PR whose head ref matches returns True."""
        manager = _manager(([], [ClosingPRRef(42, "123-feature")]))

        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            result = is_branch_linked_to_issue(manager, 123, "123-feature")

        assert result is True
        assert any(
            r.levelno == logging.INFO and "#42" in r.getMessage()
            for r in caplog.records
        )
        manager.get_linked_branch_and_closing_prs_or_none.assert_called_once_with(123)

    def test_closing_prs_none_matching(self, caplog: pytest.LogCaptureFixture) -> None:
        """Closing PRs with other head refs return False."""
        manager = _manager(([], [ClosingPRRef(42, "other-branch")]))

        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            result = is_branch_linked_to_issue(manager, 123, "123-feature")

        assert result is False
        assert any(
            r.levelno == logging.WARNING and "not linked" in r.getMessage()
            for r in caplog.records
        )
        manager.get_linked_branch_and_closing_prs_or_none.assert_called_once_with(123)

    def test_lookup_failed(self, caplog: pytest.LogCaptureFixture) -> None:
        """A failed lookup returns None and logs an error."""
        manager = _manager(None)

        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            result = is_branch_linked_to_issue(manager, 123, "123-feature")

        assert result is None
        assert any(
            r.levelno == logging.ERROR
            and "Could not determine linkage" in r.getMessage()
            for r in caplog.records
        )
        manager.get_linked_branch_and_closing_prs_or_none.assert_called_once_with(123)
