"""Tests for the body-trust warning in create_plan check_prerequisites."""

import logging
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.mcp_workspace_github import (
    BodyTrust,
    BodyTrustResult,
    GitHubRateLimitError,
    IssueData,
    create_empty_issue_data,
)
from mcp_coder.workflows.create_plan import check_prerequisites
from tests.github_factories import make_issue_data

_MODULE = "mcp_coder.workflows.create_plan.prerequisites"


@pytest.fixture(name="issue")
def fixture_issue() -> IssueData:
    """Return a found issue."""
    return make_issue_data(number=42, title="Some issue", body="body")


@pytest.fixture(name="manager")
def fixture_manager(issue: IssueData) -> Iterator[MagicMock]:
    """Patch IssueManager so get_issue returns the issue fixture."""
    with patch(f"{_MODULE}.IssueManager") as manager_class:
        manager = MagicMock()
        manager.get_issue.return_value = issue
        manager_class.return_value = manager
        yield manager


def _warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]


class TestCheckPrerequisitesBodyTrust:
    """check_prerequisites warns on an untrusted body but keeps running."""

    def test_trusted_no_warning(
        self,
        tmp_path: Path,
        manager: MagicMock,
        issue: IssueData,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A trusted body passes without a warning."""
        result = BodyTrustResult(status=BodyTrust.TRUSTED, reason="author OWNER")
        with (
            patch(f"{_MODULE}.evaluate_body_trust", return_value=result) as evaluate,
            caplog.at_level(logging.WARNING, logger=_MODULE),
        ):
            assert check_prerequisites(tmp_path, 42) == (True, issue)
        evaluate.assert_called_once_with(manager, issue)
        assert not _warnings(caplog)

    def test_untrusted_warns(
        self,
        tmp_path: Path,
        manager: MagicMock,  # pylint: disable=unused-argument
        issue: IssueData,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An untrusted body logs one warning and still passes."""
        result = BodyTrustResult(status=BodyTrust.UNTRUSTED, reason="author NONE")
        with (
            patch(f"{_MODULE}.evaluate_body_trust", return_value=result),
            caplog.at_level(logging.WARNING, logger=_MODULE),
        ):
            assert check_prerequisites(tmp_path, 42) == (True, issue)
        warnings = _warnings(caplog)
        assert len(warnings) == 1
        assert "untrusted" in warnings[0]
        assert "author NONE" in warnings[0]

    def test_lookup_failed_warns(
        self,
        tmp_path: Path,
        manager: MagicMock,  # pylint: disable=unused-argument
        issue: IssueData,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A failed lookup logs a distinct warning and still passes."""
        result = BodyTrustResult(status=BodyTrust.LOOKUP_FAILED, reason="KeyError")
        with (
            patch(f"{_MODULE}.evaluate_body_trust", return_value=result),
            caplog.at_level(logging.WARNING, logger=_MODULE),
        ):
            assert check_prerequisites(tmp_path, 42) == (True, issue)
        warnings = _warnings(caplog)
        assert len(warnings) == 1
        assert "Could not verify" in warnings[0]
        assert "KeyError" in warnings[0]

    def test_rate_limit_warns_and_continues(
        self,
        tmp_path: Path,
        manager: MagicMock,  # pylint: disable=unused-argument
        issue: IssueData,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A rate limit during the lookup logs a warning, no exception."""
        with (
            patch(
                f"{_MODULE}.evaluate_body_trust",
                side_effect=GitHubRateLimitError("limited"),
            ),
            caplog.at_level(logging.WARNING, logger=_MODULE),
        ):
            assert check_prerequisites(tmp_path, 42) == (True, issue)
        warnings = _warnings(caplog)
        assert len(warnings) == 1
        assert "rate limit" in warnings[0]

    def test_issue_not_found_skips_lookup(self, tmp_path: Path) -> None:
        """No trust lookup when the issue does not exist."""
        with (
            patch(f"{_MODULE}.IssueManager") as manager_class,
            patch(f"{_MODULE}.evaluate_body_trust") as evaluate,
        ):
            manager_class.return_value.get_issue.return_value = (
                create_empty_issue_data()
            )
            success, _ = check_prerequisites(tmp_path, 42)
        assert success is False
        evaluate.assert_not_called()
