"""Tests for the pure liveness layer (``assess_liveness``).

Full rule matrix, no Windows — the #38 de-risker. The rule order is the
contract: title -> pid -> cmdline -> folder-existence. PID is a tie-breaker,
not a gate.
"""

from unittest.mock import Mock, patch

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.vscodeclaude.assessment import (
    IssueFacts,
)
from mcp_coder.workflows.vscodeclaude.assessment import (
    _issue_facts as _produce_issue_facts,
)
from mcp_coder.workflows.vscodeclaude.assessment import (
    apply_assessments,
    assess_issue_state,
    assess_liveness,
    assess_session,
    assess_transition,
    build_assessments,
    decide,
)
from mcp_coder.workflows.vscodeclaude.types import (
    Decision,
    DetectionSignals,
    IssueState,
    LivenessRule,
    LivenessVerdict,
    SessionAction,
    SessionAssessment,
    Transition,
    VSCodeClaudeSession,
)


def _signals(
    *,
    folder_exists: bool = True,
    title_match: bool = False,
    cmdline_match: bool = False,
    pid_alive: bool = False,
    found_pid: int | None = None,
    age_seconds: float = 0.0,
    within_grace: bool = False,
    directory_empty: bool = False,
) -> DetectionSignals:
    """Build DetectionSignals with everything off by default."""
    return DetectionSignals(
        folder_exists=folder_exists,
        title_match=title_match,
        cmdline_match=cmdline_match,
        pid_alive=pid_alive,
        found_pid=found_pid,
        age_seconds=age_seconds,
        within_grace=within_grace,
        directory_empty=directory_empty,
    )


class TestAssessLiveness:
    """Full rule matrix for the pure liveness verdict."""

    def test_title_hit_cmdline_miss_restores_38(self) -> None:
        """Title positive wins even when cmdline misses (the #38 restore case)."""
        verdict = assess_liveness(
            _signals(title_match=True, cmdline_match=False, pid_alive=False)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.TITLE)

    def test_bare_folder_cmdline_fallthrough(self) -> None:
        """Title miss + cmdline hit falls through to CMDLINE."""
        verdict = assess_liveness(
            _signals(title_match=False, pid_alive=False, cmdline_match=True)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.CMDLINE)

    def test_pid_alive_only(self) -> None:
        """PID alive (title + cmdline miss) yields ACTIVE via PID tie-breaker."""
        verdict = assess_liveness(
            _signals(title_match=False, pid_alive=True, cmdline_match=False)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.PID)

    def test_all_miss_folder_exists(self) -> None:
        """Everything misses but folder exists -> INACTIVE(NO_MATCH)."""
        verdict = assess_liveness(_signals(folder_exists=True))
        assert verdict == LivenessVerdict(active=False, rule=LivenessRule.NO_MATCH)

    def test_all_miss_folder_gone(self) -> None:
        """Everything misses and folder gone -> INACTIVE(NO_ARTIFACTS)."""
        verdict = assess_liveness(_signals(folder_exists=False))
        assert verdict == LivenessVerdict(active=False, rule=LivenessRule.NO_ARTIFACTS)

    def test_zombie_precursor_folder_gone_pid_alive(self) -> None:
        """Folder gone but PID alive -> ACTIVE(PID): no folder-gone short-circuit."""
        verdict = assess_liveness(_signals(folder_exists=False, pid_alive=True))
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.PID)

    def test_title_wins_over_pid_and_cmdline(self) -> None:
        """Title is authoritative even when pid and cmdline also match."""
        verdict = assess_liveness(
            _signals(title_match=True, pid_alive=True, cmdline_match=True)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.TITLE)

    def test_pid_wins_over_cmdline(self) -> None:
        """PID precedes cmdline in the rule order."""
        verdict = assess_liveness(
            _signals(title_match=False, pid_alive=True, cmdline_match=True)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.PID)

    def test_returns_frozen_verdict(self) -> None:
        """The verdict is a LivenessVerdict instance."""
        verdict = assess_liveness(_signals(title_match=True))
        assert isinstance(verdict, LivenessVerdict)


def _issue_facts(
    *,
    is_closed: bool = False,
    is_stale: bool = False,
    is_blocked: bool = False,
    is_unassigned: bool = False,
    is_ineligible: bool = False,
    stale_target: str | None = None,
) -> IssueFacts:
    """Build IssueFacts with everything off (i.e. eligible) by default."""
    return IssueFacts(
        is_closed=is_closed,
        is_stale=is_stale,
        is_blocked=is_blocked,
        is_unassigned=is_unassigned,
        is_ineligible=is_ineligible,
        stale_target=stale_target,
    )


def _active(rule: LivenessRule = LivenessRule.TITLE) -> LivenessVerdict:
    """A live verdict."""
    return LivenessVerdict(active=True, rule=rule)


def _inactive(rule: LivenessRule = LivenessRule.NO_MATCH) -> LivenessVerdict:
    """An inactive verdict."""
    return LivenessVerdict(active=False, rule=rule)


def _eligible_state() -> IssueState:
    """An eligible (open, not stale/blocked/unassigned) issue state."""
    return assess_issue_state(_issue_facts())


def _stale_state(stale_target: str | None = "status-05:bot-pickup") -> IssueState:
    """A stale issue state (destruction candidate)."""
    return assess_issue_state(_issue_facts(is_stale=True, stale_target=stale_target))


_NO_FLIP = Transition(flipped_to_inactive=False)


def _session() -> VSCodeClaudeSession:
    """A minimal session for serializer tests."""
    return VSCodeClaudeSession(
        folder="C:/work/issue-42",
        repo="owner/repo",
        issue_number=42,
        status="status-07:code-review",
        vscode_pid=None,
        vscode_pid_create_time=None,
        started_at="2026-06-26T00:00:00",
        is_intervention=False,
        last_active=None,
        last_active_rule=None,
    )


class TestAssessIssueState:
    """Per-fact-combo mapping for the pure issue-state layer."""

    def test_eligible_when_all_clear(self) -> None:
        state = assess_issue_state(_issue_facts())
        assert state.is_eligible is True
        assert state.is_open is True
        assert state.is_stale is False

    def test_closed_is_not_open_and_ineligible(self) -> None:
        state = assess_issue_state(_issue_facts(is_closed=True))
        assert state.is_open is False
        assert state.is_eligible is False

    def test_stale_carries_target_and_is_ineligible(self) -> None:
        state = assess_issue_state(
            _issue_facts(is_stale=True, stale_target="status-05:bot-pickup")
        )
        assert state.is_stale is True
        assert state.stale_target == "status-05:bot-pickup"
        assert state.is_eligible is False

    def test_blocked_is_ineligible(self) -> None:
        assert assess_issue_state(_issue_facts(is_blocked=True)).is_eligible is False

    def test_unassigned_is_ineligible(self) -> None:
        assert assess_issue_state(_issue_facts(is_unassigned=True)).is_eligible is False

    def test_ineligible_flag_is_ineligible(self) -> None:
        assert assess_issue_state(_issue_facts(is_ineligible=True)).is_eligible is False


class TestAssessTransition:
    """The active->inactive flip flag."""

    def test_prior_active_now_inactive_flips(self) -> None:
        transition = assess_transition(True, _inactive())
        assert transition.flipped_to_inactive is True

    def test_prior_active_still_active_no_flip(self) -> None:
        transition = assess_transition(True, _active())
        assert transition.flipped_to_inactive is False

    def test_prior_inactive_no_flip(self) -> None:
        transition = assess_transition(False, _inactive())
        assert transition.flipped_to_inactive is False

    def test_none_prior_blind_spot_no_flip(self) -> None:
        transition = assess_transition(None, _inactive())
        assert transition.flipped_to_inactive is False


class TestDecide:
    """The full git-status safety matrix + zombie/keep/restart actions."""

    def test_zombie_active_pid_folder_missing(self) -> None:
        decision = decide(
            _active(LivenessRule.PID), _eligible_state(), _NO_FLIP, "Missing", False
        )
        assert decision.action == SessionAction.INVESTIGATE_ZOMBIE
        assert decision.destructive is False

    def test_remove_missing_inactive_folder_missing(self) -> None:
        decision = decide(_inactive(), _stale_state(), _NO_FLIP, "Missing", False)
        assert decision.action == SessionAction.REMOVE_MISSING
        assert decision.destructive is False

    def test_delete_inactive_stale_clean(self) -> None:
        decision = decide(_inactive(), _stale_state(), _NO_FLIP, "Clean", False)
        assert decision.action == SessionAction.DELETE
        assert decision.destructive is True
        assert "status-05:bot-pickup" in decision.reason

    def test_skip_dirty(self) -> None:
        decision = decide(_inactive(), _stale_state(), _NO_FLIP, "Dirty", False)
        assert decision.action == SessionAction.SKIP
        assert decision.reason == "dirty"
        assert decision.destructive is False

    def test_no_git_non_empty_skips_not_deletes(self) -> None:
        """DECISION 2 fix: weak evidence on a non-empty folder must NOT delete."""
        decision = decide(_inactive(), _stale_state(), _NO_FLIP, "No Git", False)
        assert decision.action == SessionAction.SKIP
        assert decision.destructive is False

    def test_no_git_empty_deletes(self) -> None:
        decision = decide(_inactive(), _stale_state(), _NO_FLIP, "No Git", True)
        assert decision.action == SessionAction.DELETE
        assert decision.destructive is True

    def test_error_non_empty_skips(self) -> None:
        decision = decide(_inactive(), _stale_state(), _NO_FLIP, "Error", False)
        assert decision.action == SessionAction.SKIP
        assert decision.destructive is False

    def test_restart_inactive_clean_eligible(self) -> None:
        decision = decide(_inactive(), _eligible_state(), _NO_FLIP, "Clean", False)
        assert decision.action == SessionAction.RESTART
        assert decision.destructive is False

    def test_keep_active_title_hit(self) -> None:
        decision = decide(
            _active(LivenessRule.TITLE), _eligible_state(), _NO_FLIP, "Clean", False
        )
        assert decision.action == SessionAction.KEEP_ACTIVE
        assert decision.destructive is False
        assert "title" in decision.reason


class TestDestructiveInvariant:
    """No Decision is destructive unless git_status is Clean OR directory_empty."""

    def test_no_destructive_without_clean_or_empty(self) -> None:
        verdicts = [_active(LivenessRule.PID), _inactive()]
        states = [
            _eligible_state(),
            _stale_state(),
            assess_issue_state(_issue_facts(is_closed=True)),
        ]
        statuses = ["Clean", "Dirty", "Missing", "No Git", "Error"]
        for verdict in verdicts:
            for state in states:
                for git_status in statuses:
                    for directory_empty in (True, False):
                        decision = decide(
                            verdict, state, _NO_FLIP, git_status, directory_empty
                        )
                        if decision.destructive:
                            assert git_status == "Clean" or directory_empty is True, (
                                f"destructive with git_status={git_status} "
                                f"empty={directory_empty}"
                            )
                            assert decision.action == SessionAction.DELETE


class TestAssessSession:
    """The pure composer aggregating the four layers."""

    def test_transition_flips_via_composer(self) -> None:
        signals = _signals(title_match=False, folder_exists=True)
        assessment = assess_session(
            folder="C:/work/issue-42",
            signals=signals,
            issue_facts=_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=True,
        )
        assert assessment.transition.flipped_to_inactive is True

    def test_none_prior_no_flip_via_composer(self) -> None:
        signals = _signals(title_match=False, folder_exists=True)
        assessment = assess_session(
            folder="C:/work/issue-42",
            signals=signals,
            issue_facts=_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )
        assert assessment.transition.flipped_to_inactive is False

    def test_pid_needs_refresh_on_active_cmdline_match(self) -> None:
        signals = _signals(cmdline_match=True, found_pid=4321)
        assessment = assess_session(
            folder="C:/work/issue-42",
            signals=signals,
            issue_facts=_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )
        assert assessment.verdict.active is True
        assert assessment.pid_needs_refresh is True
        assert assessment.found_pid == 4321

    def test_no_pid_refresh_when_inactive(self) -> None:
        signals = _signals(found_pid=None)
        assessment = assess_session(
            folder="C:/work/issue-42",
            signals=signals,
            issue_facts=_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )
        assert assessment.pid_needs_refresh is False

    def test_embeds_all_four_sub_results(self) -> None:
        assessment = assess_session(
            folder="C:/work/issue-42",
            signals=_signals(title_match=True),
            issue_facts=_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )
        assert isinstance(assessment, SessionAssessment)
        assert isinstance(assessment.verdict, LivenessVerdict)
        assert isinstance(assessment.issue_state, IssueState)
        assert isinstance(assessment.transition, Transition)
        assert isinstance(assessment.decision, Decision)


class TestSerializer:
    """The single serializer feeding audit / --explain / VSCode column."""

    def test_to_audit_record_flattens(self) -> None:
        assessment = assess_session(
            folder="C:/work/issue-42",
            signals=_signals(title_match=True, found_pid=99),
            issue_facts=_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )
        record = assessment.to_audit_record(_session())
        assert record["verdict"]["rule"] == "title"
        assert record["decision"]["action"] == SessionAction.KEEP_ACTIVE.value
        assert record["signals"]["found_pid"] == 99
        assert record["repo"] == "owner/repo"
        assert record["issue_number"] == 42

    def test_to_explain_contains_rule_and_action(self) -> None:
        assessment = assess_session(
            folder="C:/work/issue-42",
            signals=_signals(title_match=True),
            issue_facts=_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )
        text = assessment.to_explain()
        assert "title" in text
        assert SessionAction.KEEP_ACTIVE.value in text


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
            _session(),
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
            _session(),
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
            _session(),
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
            _session(),
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
            _session(),
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
            _session(),
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
            _session(),
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
            _session(),
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
            _session(),
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
            _session(),
            issue,
            github_username="testuser",
            ignore_labels=set(),
            cached_for_stale_check={42: issue},
        )
        state = assess_issue_state(facts)
        assert state.is_open is True
        assert state.is_eligible is True


_SNAP = "mcp_coder.workflows.vscodeclaude.assessment.capture_detection_snapshot"
_GATHER = "mcp_coder.workflows.vscodeclaude.assessment.gather_signals"
_GIT_STATUS = "mcp_coder.workflows.vscodeclaude.assessment.get_folder_git_status"
_IGNORE = "mcp_coder.workflows.vscodeclaude.assessment.get_ignore_labels"
_USERNAME = "mcp_coder.workflows.vscodeclaude.assessment.get_github_username"
_LOAD = "mcp_coder.workflows.vscodeclaude.assessment.load_sessions"
_SAVE = "mcp_coder.workflows.vscodeclaude.assessment.save_sessions"
_CREATE_TIME = "mcp_coder.workflows.vscodeclaude.assessment.get_pid_create_time"


def _session_at(folder: str, issue_number: int = 42) -> VSCodeClaudeSession:
    """A minimal session at a specific folder/issue for orchestration tests."""
    session = _session()
    session["folder"] = folder
    session["issue_number"] = issue_number
    return session


class TestBuildAssessments:
    """READ-ONLY builder: snapshot once, no disk writes, one entry per session."""

    @patch(_SAVE)
    @patch(_GIT_STATUS, return_value="Clean")
    @patch(_GATHER)
    @patch(_SNAP)
    @patch(_USERNAME, return_value="testuser")
    @patch(_IGNORE, return_value=set())
    def test_build_assessments_performs_no_disk_writes(
        self,
        mock_ignore: object,
        mock_username: object,
        mock_snap: object,
        mock_gather: Mock,
        mock_git: object,
        mock_save: Mock,
    ) -> None:
        """build_assessments never writes sessions.json (save_sessions untouched)."""
        mock_gather.return_value = _signals(title_match=True, found_pid=7)
        sessions = [_session_at("C:/work/a", 1)]

        result = build_assessments(sessions, cached_issues_by_repo=None)

        assert set(result) == {"C:/work/a"}
        assert result["C:/work/a"].verdict.active is True
        mock_save.assert_not_called()

    @patch(_SAVE)
    @patch(_GIT_STATUS, return_value="Clean")
    @patch(_GATHER)
    @patch(_SNAP)
    @patch(_USERNAME, return_value="testuser")
    @patch(_IGNORE, return_value=set())
    def test_snapshot_captured_exactly_once_per_call(
        self,
        mock_ignore: object,
        mock_username: object,
        mock_snap: Mock,
        mock_gather: Mock,
        mock_git: object,
        mock_save: object,
    ) -> None:
        """One DetectionSnapshot per build (R4), gathered once per session."""
        mock_gather.return_value = _signals()
        sessions = [
            _session_at("C:/work/a", 1),
            _session_at("C:/work/b", 2),
            _session_at("C:/work/c", 3),
        ]

        result = build_assessments(sessions)

        assert mock_snap.call_count == 1
        assert mock_gather.call_count == len(sessions)
        assert set(result) == {"C:/work/a", "C:/work/b", "C:/work/c"}


class TestApplyAssessments:
    """Apply-only mutation point: PID refresh + last_active advance, single save."""

    @patch(_CREATE_TIME, return_value=123.5)
    @patch(_SAVE)
    @patch(_LOAD)
    def test_apply_advances_last_active_and_refreshes_pid_once(
        self,
        mock_load: Mock,
        mock_save: Mock,
        mock_ct: Mock,
    ) -> None:
        """An active session refreshes the stale PID and advances last_active."""
        session = _session_at("C:/work/a", 1)
        session["vscode_pid"] = 100
        mock_load.return_value = {"sessions": [session], "last_updated": ""}

        assessment = assess_session(
            folder="C:/work/a",
            signals=_signals(title_match=True, found_pid=200),
            issue_facts=_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )

        apply_assessments({"C:/work/a": assessment}, write_audit=False)

        saved_store = mock_save.call_args[0][0]
        saved = saved_store["sessions"][0]
        assert saved["vscode_pid"] == 200
        assert saved["vscode_pid_create_time"] == 123.5
        assert saved["last_active"] is True
        assert saved["last_active_rule"] == "title"
        mock_ct.assert_called_once_with(200)
        mock_save.assert_called_once()

    @patch(_CREATE_TIME)
    @patch(_SAVE)
    @patch(_LOAD)
    def test_apply_inactive_skips_pid_refresh(
        self,
        mock_load: Mock,
        mock_save: Mock,
        mock_ct: Mock,
    ) -> None:
        """An inactive session advances last_active to False without touching PID."""
        session = _session_at("C:/work/a", 1)
        session["vscode_pid"] = 100
        mock_load.return_value = {"sessions": [session], "last_updated": ""}

        assessment = assess_session(
            folder="C:/work/a",
            signals=_signals(folder_exists=True),  # all miss -> INACTIVE(NO_MATCH)
            issue_facts=_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=True,
        )

        apply_assessments({"C:/work/a": assessment}, write_audit=False)

        saved = mock_save.call_args[0][0]["sessions"][0]
        assert saved["vscode_pid"] == 100  # unchanged
        assert saved["last_active"] is False
        assert saved["last_active_rule"] == "no_match"
        mock_ct.assert_not_called()
        mock_save.assert_called_once()
