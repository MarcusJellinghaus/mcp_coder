"""Tests for the IO-boundary IssueFacts producer (``_issue_facts``).

Cached issue data -> frozen IssueFacts. Mirrors ``get_stale_sessions``
eligibility incl. the staleness short-circuit (closed/blocked/unassigned/
ineligible never reach ``is_session_stale``) and the individual-issue API
fallback when the issue is missing from the cache.
"""

from unittest.mock import patch

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.vscodeclaude.assessment import (
    IssueFacts,
)
from mcp_coder.workflows.vscodeclaude.assessment import (
    _issue_facts as _produce_issue_facts,
)
from mcp_coder.workflows.vscodeclaude.assessment import (
    assess_issue_state,
)
from tests.workflows.vscodeclaude.conftest import make_session

_STALE = "mcp_coder.workflows.vscodeclaude.assessment.is_session_stale"
_GET_ALL = "mcp_coder.workflows.vscodeclaude.assessment.get_all_cached_issues"
_ISSUE_MANAGER = "mcp_coder.workflows.vscodeclaude.assessment.IssueManager"
_REPO_ID = "mcp_coder.workflows.vscodeclaude.assessment.RepoIdentifier"


def _make_issue(
    *,
    number: int = 42,
    state: str = "open",
    labels: list[str] | None = None,
    assignees: list[str] | None = None,
) -> IssueData:
    """Build a minimal IssueData for the IssueFacts producer tests."""
    issue: IssueData = {
        "number": number,
        "title": "Test issue",
        "body": "",
        "state": state,
        "labels": labels if labels is not None else [],
        "assignees": assignees if assignees is not None else [],
        "user": None,
        "created_at": None,
        "updated_at": None,
        "url": "",
        "locked": False,
    }
    return issue


class TestIssueFacts:
    """The IO-boundary producer: cached issue data -> frozen IssueFacts.

    Mirrors ``get_stale_sessions`` eligibility incl. the staleness short-circuit
    (closed/blocked/unassigned/ineligible never reach ``is_session_stale``) and
    the individual-issue API fallback when the issue is missing from the cache.
    """

    @patch(_STALE)
    def test_closed_issue_short_circuits_stale(self, mock_stale: object) -> None:
        """Closed issue maps to is_closed and never calls is_session_stale."""
        issue = _make_issue(state="closed", labels=["status-07:code-review"])
        facts = _produce_issue_facts(
            make_session(),
            issue,
            github_username="testuser",
            ignore_labels=set(),
            cached_for_stale_check={42: issue},
        )
        assert facts.is_closed is True
        assert facts.is_stale is False
        mock_stale.assert_not_called()  # type: ignore[attr-defined]

    @patch(_STALE)
    def test_blocked_short_circuits_stale(self, mock_stale: object) -> None:
        """A matching ignore label sets is_blocked and short-circuits staleness."""
        issue = _make_issue(labels=["status-07:code-review", "blocked"])
        facts = _produce_issue_facts(
            make_session(),
            issue,
            github_username="testuser",
            ignore_labels={"blocked"},
            cached_for_stale_check={42: issue},
        )
        assert facts.is_blocked is True
        assert facts.is_stale is False
        mock_stale.assert_not_called()  # type: ignore[attr-defined]

    @patch(_STALE)
    def test_ineligible_status_short_circuits_stale(self, mock_stale: object) -> None:
        """A bot/ineligible status sets is_ineligible and short-circuits staleness."""
        issue = _make_issue(labels=["status-02:awaiting-planning"])
        facts = _produce_issue_facts(
            make_session(),
            issue,
            github_username="testuser",
            ignore_labels=set(),
            cached_for_stale_check={42: issue},
        )
        assert facts.is_ineligible is True
        assert facts.is_stale is False
        mock_stale.assert_not_called()  # type: ignore[attr-defined]

    @patch(_STALE)
    def test_unassigned_short_circuits_stale(self, mock_stale: object) -> None:
        """An eligible open issue with the user removed sets is_unassigned."""
        issue = _make_issue(labels=["status-07:code-review"], assignees=[])
        facts = _produce_issue_facts(
            make_session(),
            issue,
            github_username="testuser",
            ignore_labels=set(),
            cached_for_stale_check={42: issue},
        )
        assert facts.is_unassigned is True
        assert facts.is_stale is False
        mock_stale.assert_not_called()  # type: ignore[attr-defined]

    @patch(_STALE, return_value=True)
    def test_eligible_issue_calls_stale(self, mock_stale: object) -> None:
        """Eligible, assigned, open issue reaches is_session_stale; result flows."""
        issue = _make_issue(labels=["status-07:code-review"], assignees=["testuser"])
        facts = _produce_issue_facts(
            make_session(),
            issue,
            github_username="testuser",
            ignore_labels=set(),
            cached_for_stale_check={42: issue},
        )
        mock_stale.assert_called_once()  # type: ignore[attr-defined]
        assert facts.is_stale is True
        assert facts.stale_target == "status-07:code-review"

    @patch(_STALE, return_value=False)
    def test_eligible_not_stale_carries_through(self, mock_stale: object) -> None:
        """When is_session_stale returns False the facts are all-clear (eligible)."""
        issue = _make_issue(labels=["status-07:code-review"], assignees=["testuser"])
        facts = _produce_issue_facts(
            make_session(),
            issue,
            github_username="testuser",
            ignore_labels=set(),
            cached_for_stale_check={42: issue},
        )
        mock_stale.assert_called_once()  # type: ignore[attr-defined]
        assert facts.is_stale is False
        assert facts == IssueFacts(
            is_closed=False,
            is_stale=False,
            is_blocked=False,
            is_unassigned=False,
            is_ineligible=False,
            stale_target="status-07:code-review",
        )

    @patch(_STALE, return_value=False)
    @patch(_REPO_ID)
    @patch(_ISSUE_MANAGER)
    @patch(_GET_ALL)
    def test_missing_from_cache_triggers_fallback(
        self,
        mock_get_all: object,
        mock_issue_manager: object,
        mock_repo_id: object,
        mock_stale: object,
    ) -> None:
        """Issue missing from cache -> individual-issue API fallback is invoked."""
        issue = _make_issue(labels=["status-07:code-review"], assignees=["testuser"])
        mock_get_all.return_value = [issue]  # type: ignore[attr-defined]
        facts = _produce_issue_facts(
            make_session(),
            None,
            github_username="testuser",
            ignore_labels=set(),
            cached_for_stale_check=None,
        )
        mock_get_all.assert_called_once()  # type: ignore[attr-defined]
        _, kwargs = mock_get_all.call_args  # type: ignore[attr-defined]
        assert kwargs["additional_issues"] == [42]
        # The fetched issue flows through into the facts.
        assert facts.is_closed is False
        assert facts.stale_target == "status-07:code-review"

    @patch(_STALE, return_value=False)
    @patch(_REPO_ID)
    @patch(_ISSUE_MANAGER)
    @patch(_GET_ALL, side_effect=RuntimeError("network down"))
    def test_fallback_failure_leaves_facts_clear(
        self,
        mock_get_all: object,
        mock_issue_manager: object,
        mock_repo_id: object,
        mock_stale: object,
    ) -> None:
        """A failed fallback skips eligibility checks (all flags default False)."""
        facts = _produce_issue_facts(
            make_session(),
            None,
            github_username="testuser",
            ignore_labels=set(),
            cached_for_stale_check=None,
        )
        assert facts == IssueFacts(
            is_closed=False,
            is_stale=False,
            is_blocked=False,
            is_unassigned=False,
            is_ineligible=False,
            stale_target=None,
        )

    @patch(_STALE)
    def test_closed_round_trips_to_issue_state(self, mock_stale: object) -> None:
        """Closed facts classify to an ineligible, not-open IssueState (Step 3)."""
        issue = _make_issue(state="closed", labels=["status-07:code-review"])
        facts = _produce_issue_facts(
            make_session(),
            issue,
            github_username="testuser",
            ignore_labels=set(),
            cached_for_stale_check={42: issue},
        )
        state = assess_issue_state(facts)
        assert state.is_open is False
        assert state.is_eligible is False

    @patch(_STALE, return_value=False)
    def test_eligible_round_trips_to_eligible_state(self, mock_stale: object) -> None:
        """Eligible facts classify to an eligible, open IssueState (Step 3)."""
        issue = _make_issue(labels=["status-07:code-review"], assignees=["testuser"])
        facts = _produce_issue_facts(
            make_session(),
            issue,
            github_username="testuser",
            ignore_labels=set(),
            cached_for_stale_check={42: issue},
        )
        state = assess_issue_state(facts)
        assert state.is_open is True
        assert state.is_eligible is True
