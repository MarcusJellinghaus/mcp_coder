"""A failed live issue fetch is "unknown", never "closed"."""

from collections.abc import Callable
from unittest.mock import MagicMock, Mock

import pytest

from mcp_coder.mcp_workspace_github import (
    GithubException,
    GitHubRateLimitError,
    create_empty_issue_data,
)
from mcp_coder.workflows.vscodeclaude.assessment import _issue_facts
from mcp_coder.workflows.vscodeclaude.status import (
    get_issue_current_status,
    is_issue_closed,
    is_session_stale,
)
from tests.github_factories import make_issue_data
from tests.workflows.vscodeclaude.conftest import make_session

STATUS = "mcp_coder.workflows.vscodeclaude.status"
ASSESSMENT = "mcp_coder.workflows.vscodeclaude.assessment"


def _auth_error() -> GithubException:
    return GithubException(401, {"message": "Bad credentials"})


def _rate_limit() -> GithubException:
    return GithubException(
        403,
        {"message": "API rate limit exceeded"},
        headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1900000000"},
    )


def _patch_manager(monkeypatch: pytest.MonkeyPatch, manager: MagicMock) -> None:
    monkeypatch.setattr(f"{STATUS}.IssueManager", Mock(return_value=manager))


def _failing_manager(side_effect: BaseException) -> MagicMock:
    manager = MagicMock()
    manager.get_issue.side_effect = side_effect
    return manager


def _empty_manager() -> MagicMock:
    manager = MagicMock()
    manager.get_issue.return_value = create_empty_issue_data()
    return manager


UNKNOWN_CASES = [
    pytest.param(lambda: _failing_manager(_auth_error()), id="exception"),
    pytest.param(_empty_manager, id="empty-issue-data"),
]


class TestUnknownState:
    """Live fetch failures yield (None, None) and are neither closed nor stale."""

    @pytest.mark.parametrize("make_manager", UNKNOWN_CASES)
    def test_get_issue_current_status_unknown(
        self, make_manager: Callable[[], MagicMock]
    ) -> None:
        manager = make_manager()

        assert get_issue_current_status(42, issue_manager=manager) == (None, None)

    @pytest.mark.parametrize("make_manager", UNKNOWN_CASES)
    def test_is_session_stale_false(
        self, monkeypatch: pytest.MonkeyPatch, make_manager: Callable[[], MagicMock]
    ) -> None:
        _patch_manager(monkeypatch, make_manager())

        assert is_session_stale(make_session()) is False

    @pytest.mark.parametrize("make_manager", UNKNOWN_CASES)
    def test_is_issue_closed_false(
        self, monkeypatch: pytest.MonkeyPatch, make_manager: Callable[[], MagicMock]
    ) -> None:
        _patch_manager(monkeypatch, make_manager())

        assert is_issue_closed(make_session()) is False

    def test_issue_facts_not_stale(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            f"{ASSESSMENT}._fetch_issue_individually", Mock(return_value=None)
        )
        _patch_manager(monkeypatch, _failing_manager(side_effect=_auth_error()))

        facts = _issue_facts(
            make_session(),
            None,
            github_username=None,
            ignore_labels=set(),
            cached_for_stale_check=None,
        )

        assert facts.is_stale is False


class TestRateLimitPropagates:
    """A rate limit on the live fetch is raised, not swallowed."""

    def test_get_issue_current_status(self) -> None:
        manager = _failing_manager(side_effect=_rate_limit())

        with pytest.raises(GitHubRateLimitError):
            get_issue_current_status(42, issue_manager=manager)

    def test_is_session_stale(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_manager(monkeypatch, _failing_manager(side_effect=_rate_limit()))

        with pytest.raises(GitHubRateLimitError):
            is_session_stale(make_session())


class TestKnownState:
    """Open and closed issues fetched live keep their existing results."""

    def test_open_issue(self) -> None:
        manager = MagicMock()
        manager.get_issue.return_value = make_issue_data(
            number=42, state="open", labels=["status-07:code-review"]
        )

        assert get_issue_current_status(42, issue_manager=manager) == (
            "status-07:code-review",
            True,
        )

    def test_closed_issue(self, monkeypatch: pytest.MonkeyPatch) -> None:
        manager = MagicMock()
        manager.get_issue.return_value = make_issue_data(
            number=42, state="closed", labels=[]
        )
        _patch_manager(monkeypatch, manager)

        assert get_issue_current_status(42, issue_manager=manager) == (None, False)
        assert is_issue_closed(make_session()) is True
        assert is_session_stale(make_session()) is True
