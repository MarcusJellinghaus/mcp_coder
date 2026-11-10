"""Tests for the pure assessment layers and serializer.

Full rule matrix, no Windows — the #38 de-risker. The liveness rule order is
the contract: a title match always wins; past grace with an authoritative
title a miss is decisive (NO_WINDOW when only pid/cmdline still reference the
folder); otherwise pid -> cmdline -> folder-existence. The decide layer owns
the full git-status safety matrix and is the ONLY place a destructive DELETE
can be produced.
"""

import pytest

from mcp_coder.workflows.vscodeclaude.assessment import (
    CONFIRMING_REASON,
    NO_WINDOW_REASON,
    assess_issue_state,
    assess_liveness,
    assess_session,
    assess_transition,
    decide,
    guard_reason,
)
from mcp_coder.workflows.vscodeclaude.types import (
    Decision,
    IssueState,
    LivenessRule,
    LivenessVerdict,
    SessionAction,
    SessionAssessment,
    Transition,
)
from tests.workflows.vscodeclaude.conftest import (
    NO_FLIP,
    make_active,
    make_eligible_state,
    make_inactive,
    make_issue_facts,
    make_session,
    make_signals,
    make_stale_state,
    make_transition,
)


class TestAssessLiveness:
    """Full rule matrix for the pure liveness verdict."""

    def test_title_hit_cmdline_miss_restores_38(self) -> None:
        """Title positive wins even when cmdline misses (the #38 restore case)."""
        verdict = assess_liveness(
            make_signals(title_match=True, cmdline_match=False, pid_alive=False)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.TITLE)

    def test_bare_folder_cmdline_fallthrough(self) -> None:
        """Title miss + cmdline hit falls through to CMDLINE."""
        verdict = assess_liveness(
            make_signals(title_match=False, pid_alive=False, cmdline_match=True)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.CMDLINE)

    def test_pid_alive_only(self) -> None:
        """PID alive (title not authoritative, cmdline miss) yields ACTIVE(PID)."""
        verdict = assess_liveness(
            make_signals(title_match=False, pid_alive=True, cmdline_match=False)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.PID)

    def test_all_miss_folder_exists(self) -> None:
        """Everything misses but folder exists -> INACTIVE(NO_MATCH)."""
        verdict = assess_liveness(make_signals(folder_exists=True))
        assert verdict == LivenessVerdict(active=False, rule=LivenessRule.NO_MATCH)

    def test_all_miss_folder_gone(self) -> None:
        """Everything misses and folder gone -> INACTIVE(NO_ARTIFACTS)."""
        verdict = assess_liveness(make_signals(folder_exists=False))
        assert verdict == LivenessVerdict(active=False, rule=LivenessRule.NO_ARTIFACTS)

    def test_zombie_precursor_folder_gone_pid_alive(self) -> None:
        """Folder gone but PID alive -> ACTIVE(PID): no folder-gone short-circuit."""
        verdict = assess_liveness(make_signals(folder_exists=False, pid_alive=True))
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.PID)

    def test_title_wins_over_pid_and_cmdline(self) -> None:
        """Title is authoritative even when pid and cmdline also match."""
        verdict = assess_liveness(
            make_signals(title_match=True, pid_alive=True, cmdline_match=True)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.TITLE)

    def test_pid_wins_over_cmdline(self) -> None:
        """PID precedes cmdline in the rule order."""
        verdict = assess_liveness(
            make_signals(title_match=False, pid_alive=True, cmdline_match=True)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.PID)

    def test_returns_frozen_verdict(self) -> None:
        """The verdict is a LivenessVerdict instance."""
        verdict = assess_liveness(make_signals(title_match=True))
        assert isinstance(verdict, LivenessVerdict)

    @pytest.mark.parametrize(
        ("authoritative", "within_grace", "signals", "expected"),
        [
            (True, False, {"pid_alive": True}, (False, LivenessRule.NO_WINDOW)),
            (True, False, {"cmdline_match": True}, (False, LivenessRule.NO_WINDOW)),
            (
                True,
                False,
                {"pid_alive": True, "folder_exists": False},
                (False, LivenessRule.NO_ARTIFACTS),
            ),
            (True, False, {}, (False, LivenessRule.NO_MATCH)),
            (True, True, {"pid_alive": True}, (True, LivenessRule.PID)),
            (True, True, {"cmdline_match": True}, (True, LivenessRule.CMDLINE)),
            (False, False, {"pid_alive": True}, (True, LivenessRule.PID)),
            (False, False, {"cmdline_match": True}, (True, LivenessRule.CMDLINE)),
            (
                True,
                False,
                {"title_match": True, "pid_alive": True},
                (True, LivenessRule.TITLE),
            ),
        ],
        ids=[
            "auth_past_grace_pid_is_no_window",
            "auth_past_grace_cmdline_is_no_window",
            "auth_past_grace_folder_missing_is_no_artifacts",
            "auth_past_grace_nothing_is_no_match",
            "auth_within_grace_pid_active",
            "auth_within_grace_cmdline_active",
            "not_auth_pid_active",
            "not_auth_cmdline_active",
            "auth_past_grace_title_match_active",
        ],
    )
    def test_title_authoritative_matrix(
        self,
        authoritative: bool,
        within_grace: bool,
        signals: dict[str, bool],
        expected: tuple[bool, LivenessRule],
    ) -> None:
        """Past grace an authoritative title miss is decisive; else fallback."""
        verdict = assess_liveness(
            make_signals(
                title_authoritative=authoritative,
                within_grace=within_grace,
                **signals,
            )
        )
        assert verdict == LivenessVerdict(active=expected[0], rule=expected[1])


class TestAssessIssueState:
    """Per-fact-combo mapping for the pure issue-state layer."""

    def test_eligible_when_all_clear(self) -> None:
        state = assess_issue_state(make_issue_facts())
        assert state.is_eligible is True
        assert state.is_open is True
        assert state.is_stale is False

    def test_closed_is_not_open_and_ineligible(self) -> None:
        state = assess_issue_state(make_issue_facts(is_closed=True))
        assert state.is_open is False
        assert state.is_eligible is False

    def test_stale_carries_target_and_is_ineligible(self) -> None:
        state = assess_issue_state(
            make_issue_facts(is_stale=True, stale_target="status-05:bot-pickup")
        )
        assert state.is_stale is True
        assert state.stale_target == "status-05:bot-pickup"
        assert state.is_eligible is False

    def test_blocked_is_ineligible(self) -> None:
        assert (
            assess_issue_state(make_issue_facts(is_blocked=True)).is_eligible is False
        )

    def test_unassigned_is_ineligible(self) -> None:
        assert (
            assess_issue_state(make_issue_facts(is_unassigned=True)).is_eligible
            is False
        )

    def test_ineligible_flag_is_ineligible(self) -> None:
        assert (
            assess_issue_state(make_issue_facts(is_ineligible=True)).is_eligible
            is False
        )


class TestAssessTransition:
    """The active->inactive flip flag."""

    def test_prior_active_now_inactive_flips(self) -> None:
        transition = assess_transition(True, make_inactive())
        assert transition.flipped_to_inactive is True

    def test_prior_active_still_active_no_flip(self) -> None:
        transition = assess_transition(True, make_active())
        assert transition.flipped_to_inactive is False

    def test_prior_inactive_no_flip(self) -> None:
        transition = assess_transition(False, make_inactive())
        assert transition.flipped_to_inactive is False

    def test_none_prior_blind_spot_no_flip(self) -> None:
        transition = assess_transition(None, make_inactive())
        assert transition.flipped_to_inactive is False

    @pytest.mark.parametrize("prior", [True, False, None])
    def test_carries_prior_last_active(self, prior: bool | None) -> None:
        transition = assess_transition(prior, make_inactive())
        assert transition.prior_last_active is prior
        assert transition == make_transition(prior)


_NO_WINDOW = make_inactive(LivenessRule.NO_WINDOW)


class TestDecideGuards:
    """Override (NO_WINDOW) and confirmation guards on DELETE/RESTART."""

    @pytest.mark.parametrize(
        ("verdict", "eligible", "git_status", "prior", "action", "reason"),
        [
            (make_inactive(), False, "Clean", False, SessionAction.DELETE, None),
            (
                make_inactive(),
                False,
                "Clean",
                True,
                SessionAction.SKIP,
                CONFIRMING_REASON,
            ),
            (
                make_inactive(),
                False,
                "Clean",
                None,
                SessionAction.SKIP,
                CONFIRMING_REASON,
            ),
            (_NO_WINDOW, False, "Clean", False, SessionAction.SKIP, NO_WINDOW_REASON),
            (make_inactive(), True, "Clean", False, SessionAction.RESTART, None),
            (
                make_inactive(),
                True,
                "Clean",
                True,
                SessionAction.SKIP,
                CONFIRMING_REASON,
            ),
            (
                make_inactive(),
                True,
                "Clean",
                None,
                SessionAction.SKIP,
                CONFIRMING_REASON,
            ),
            (_NO_WINDOW, True, "Clean", False, SessionAction.RESTART, None),
            (_NO_WINDOW, True, "Clean", None, SessionAction.SKIP, CONFIRMING_REASON),
            (make_inactive(), True, "Dirty", None, SessionAction.SKIP, "dirty"),
            (make_inactive(), False, "Dirty", None, SessionAction.SKIP, "dirty"),
            (_NO_WINDOW, True, "Dirty", None, SessionAction.SKIP, "dirty"),
            (_NO_WINDOW, False, "Dirty", None, SessionAction.SKIP, "dirty"),
            (
                make_inactive(LivenessRule.NO_ARTIFACTS),
                True,
                "Missing",
                None,
                SessionAction.REMOVE_MISSING,
                None,
            ),
            (
                make_inactive(LivenessRule.NO_ARTIFACTS),
                False,
                "Missing",
                None,
                SessionAction.REMOVE_MISSING,
                None,
            ),
        ],
    )
    def test_guard_matrix(
        self,
        verdict: LivenessVerdict,
        eligible: bool,
        git_status: str,
        prior: bool | None,
        action: SessionAction,
        reason: str | None,
    ) -> None:
        state = make_eligible_state() if eligible else make_stale_state()
        decision = decide(verdict, state, make_transition(prior), git_status, False)
        assert decision.action == action
        assert decision.destructive is (action == SessionAction.DELETE)
        if reason is not None:
            assert decision.reason == reason

    def test_guard_reason_allows_confirmed_no_match_delete(self) -> None:
        assert (
            guard_reason(make_inactive(), make_transition(False), SessionAction.DELETE)
            is None
        )


class TestDecide:
    """The full git-status safety matrix + zombie/keep/restart actions."""

    def test_zombie_active_pid_folder_missing(self) -> None:
        decision = decide(
            make_active(LivenessRule.PID),
            make_eligible_state(),
            NO_FLIP,
            "Missing",
            False,
        )
        assert decision.action == SessionAction.INVESTIGATE_ZOMBIE
        assert decision.destructive is False

    def test_remove_missing_inactive_folder_missing(self) -> None:
        decision = decide(
            make_inactive(), make_stale_state(), NO_FLIP, "Missing", False
        )
        assert decision.action == SessionAction.REMOVE_MISSING
        assert decision.destructive is False

    def test_delete_inactive_stale_clean(self) -> None:
        decision = decide(make_inactive(), make_stale_state(), NO_FLIP, "Clean", False)
        assert decision.action == SessionAction.DELETE
        assert decision.destructive is True
        assert "status-05:bot-pickup" in decision.reason

    def test_skip_dirty(self) -> None:
        decision = decide(make_inactive(), make_stale_state(), NO_FLIP, "Dirty", False)
        assert decision.action == SessionAction.SKIP
        assert decision.reason == "dirty"
        assert decision.destructive is False

    def test_no_git_non_empty_skips_not_deletes(self) -> None:
        """DECISION 2 fix: weak evidence on a non-empty folder must NOT delete."""
        decision = decide(make_inactive(), make_stale_state(), NO_FLIP, "No Git", False)
        assert decision.action == SessionAction.SKIP
        assert decision.destructive is False

    def test_no_git_empty_deletes(self) -> None:
        decision = decide(make_inactive(), make_stale_state(), NO_FLIP, "No Git", True)
        assert decision.action == SessionAction.DELETE
        assert decision.destructive is True

    def test_error_non_empty_skips(self) -> None:
        decision = decide(make_inactive(), make_stale_state(), NO_FLIP, "Error", False)
        assert decision.action == SessionAction.SKIP
        assert decision.destructive is False

    def test_restart_inactive_clean_eligible(self) -> None:
        decision = decide(
            make_inactive(), make_eligible_state(), NO_FLIP, "Clean", False
        )
        assert decision.action == SessionAction.RESTART
        assert decision.destructive is False

    def test_keep_active_title_hit(self) -> None:
        decision = decide(
            make_active(LivenessRule.TITLE),
            make_eligible_state(),
            NO_FLIP,
            "Clean",
            False,
        )
        assert decision.action == SessionAction.KEEP_ACTIVE
        assert decision.destructive is False
        assert "title" in decision.reason


class TestDestructiveInvariant:
    """No Decision is destructive unless git_status is Clean OR directory_empty."""

    def test_no_destructive_without_clean_or_empty(self) -> None:
        verdicts = [make_active(LivenessRule.PID), make_inactive()]
        states = [
            make_eligible_state(),
            make_stale_state(),
            assess_issue_state(make_issue_facts(is_closed=True)),
        ]
        statuses = ["Clean", "Dirty", "Missing", "No Git", "Error"]
        for verdict in verdicts:
            for state in states:
                for git_status in statuses:
                    for directory_empty in (True, False):
                        decision = decide(
                            verdict, state, NO_FLIP, git_status, directory_empty
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
        signals = make_signals(title_match=False, folder_exists=True)
        assessment = assess_session(
            folder="C:/work/issue-42",
            signals=signals,
            issue_facts=make_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=True,
        )
        assert assessment.transition.flipped_to_inactive is True

    def test_none_prior_no_flip_via_composer(self) -> None:
        signals = make_signals(title_match=False, folder_exists=True)
        assessment = assess_session(
            folder="C:/work/issue-42",
            signals=signals,
            issue_facts=make_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )
        assert assessment.transition.flipped_to_inactive is False

    def test_embeds_all_four_sub_results(self) -> None:
        assessment = assess_session(
            folder="C:/work/issue-42",
            signals=make_signals(title_match=True),
            issue_facts=make_issue_facts(),
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
            signals=make_signals(title_match=True, found_pid=99),
            issue_facts=make_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )
        record = assessment.to_audit_record(make_session())
        assert record["verdict"]["rule"] == "title"
        assert record["decision"]["action"] == SessionAction.KEEP_ACTIVE.value
        assert record["signals"]["found_pid"] == 99
        assert record["repo"] == "owner/repo"
        assert record["issue_number"] == 42

    def test_to_explain_contains_rule_and_action(self) -> None:
        assessment = assess_session(
            folder="C:/work/issue-42",
            signals=make_signals(title_match=True),
            issue_facts=make_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )
        text = assessment.to_explain()
        assert "title" in text
        assert SessionAction.KEEP_ACTIVE.value in text
