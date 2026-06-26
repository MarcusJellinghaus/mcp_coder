"""Pure assessment layers for vscodeclaude session state.

This module is the ``assess`` stage of the detect -> assess -> decide ->
render/apply pipeline. Every function here is PURE: it imports only ``types``
(no ``sessions``/``psutil``/``win32``), so the rule matrix is unit-testable
without Windows.
"""

from dataclasses import dataclass

from .types import (
    Decision,
    DetectionSignals,
    IssueState,
    LivenessRule,
    LivenessVerdict,
    SessionAction,
    SessionAssessment,
    Transition,
)


@dataclass(frozen=True)
class IssueFacts:
    """Immutable issue inputs injected into the pure issue-state layer.

    Produced at the IO boundary (Step 5 ``_issue_facts``); kept separate from
    :class:`IssueState` so :func:`assess_issue_state` stays pure and unit-testable.
    """

    is_closed: bool
    is_stale: bool
    is_blocked: bool
    is_unassigned: bool
    is_ineligible: bool
    stale_target: str | None = None  # e.g. "status-05:bot-pickup" for the reason


def assess_liveness(signals: DetectionSignals) -> LivenessVerdict:
    """Pure liveness verdict. Returns a frozen ``LivenessVerdict(active, rule)``.

    Ordering is the contract: a live process is detectable regardless of folder
    state, so the order is title -> pid -> cmdline -> folder-existence. PID is a
    tie-breaker, NOT a gate, and there is no folder-gone short-circuit (a live
    process for a deleted folder stays reachable as the zombie precursor).
    """
    if signals.title_match:
        return LivenessVerdict(active=True, rule=LivenessRule.TITLE)
    if signals.pid_alive:
        return LivenessVerdict(active=True, rule=LivenessRule.PID)
    if signals.cmdline_match:
        return LivenessVerdict(active=True, rule=LivenessRule.CMDLINE)
    if not signals.folder_exists:
        return LivenessVerdict(active=False, rule=LivenessRule.NO_ARTIFACTS)
    return LivenessVerdict(active=False, rule=LivenessRule.NO_MATCH)


def assess_issue_state(issue_facts: IssueFacts) -> IssueState:
    """Pure: classify the issue (open/stale/blocked/unassigned/eligible).

    Eligible means none of the disqualifiers (closed/stale/blocked/unassigned/
    ineligible) are set, i.e. the issue is a candidate for keep/restart rather
    than a destruction candidate.
    """
    is_eligible = not (
        issue_facts.is_closed
        or issue_facts.is_stale
        or issue_facts.is_blocked
        or issue_facts.is_unassigned
        or issue_facts.is_ineligible
    )
    return IssueState(
        is_open=not issue_facts.is_closed,
        is_stale=issue_facts.is_stale,
        is_blocked=issue_facts.is_blocked,
        is_unassigned=issue_facts.is_unassigned,
        is_eligible=is_eligible,
        stale_target=issue_facts.stale_target,
    )


def assess_transition(
    prior_last_active: bool | None, verdict: LivenessVerdict
) -> Transition:
    """Pure: the active->inactive flip flag.

    A ``None`` prior (never observed under the new system, e.g. a backfilled
    session) is a blind spot, so it can never be a flip.
    """
    flipped = prior_last_active is True and not verdict.active
    return Transition(flipped_to_inactive=flipped)


def _ineligibility_reasons(issue_state: IssueState) -> str:
    """Join the reasons an issue is ineligible into one human/audit string."""
    reasons: list[str] = []
    if issue_state.is_stale:
        if issue_state.stale_target:
            reasons.append(f"stale ({issue_state.stale_target})")
        else:
            reasons.append("stale")
    if not issue_state.is_open:
        reasons.append("closed")
    if issue_state.is_blocked:
        reasons.append("blocked")
    if issue_state.is_unassigned:
        reasons.append("unassigned")
    if not reasons:
        reasons.append("ineligible")
    return ", ".join(reasons)


def decide(
    verdict: LivenessVerdict,
    issue_state: IssueState,
    transition: Transition,
    git_status: str,  # "Clean"|"Dirty"|"Missing"|"No Git"|"Error"
    directory_empty: bool,
) -> Decision:
    """Pure: owns the FULL git-status safety matrix + zombie/keep/restart actions.

    DELETE is the ONLY destructive branch, and it requires ``git_status == "Clean"``
    OR ``directory_empty`` — never destruction on weak evidence ("No Git"/"Error"
    on a non-empty folder). This single place is covered by the invariant test.
    """
    if verdict.active and git_status == "Missing":
        return Decision(
            action=SessionAction.INVESTIGATE_ZOMBIE,
            reason="folder missing, process alive",
            destructive=False,
        )
    if verdict.active:
        return Decision(
            action=SessionAction.KEEP_ACTIVE,
            reason=f"active ({verdict.rule.value})",
            destructive=False,
        )
    if git_status == "Missing":
        return Decision(
            action=SessionAction.REMOVE_MISSING,
            reason="folder missing",
            destructive=False,
        )
    if git_status == "Dirty":
        return Decision(action=SessionAction.SKIP, reason="dirty", destructive=False)
    if not issue_state.is_eligible:
        # Destruction candidate (stale/closed/blocked/unassigned/ineligible).
        if git_status == "Clean" or directory_empty:
            return Decision(
                action=SessionAction.DELETE,
                reason=_ineligibility_reasons(issue_state),
                destructive=True,  # the ONLY destructive branch
            )
        # "No Git"/"Error" on a NON-empty folder -> weak evidence: refuse to delete.
        return Decision(
            action=SessionAction.SKIP,
            reason=f"unverified git status ({git_status}), non-empty",
            destructive=False,
        )
    return Decision(
        action=SessionAction.RESTART, reason="restartable", destructive=False
    )


def assess_session(
    folder: str,
    signals: DetectionSignals,
    issue_facts: IssueFacts,
    git_status: str,
    directory_empty: bool,
    prior_last_active: bool | None,
) -> SessionAssessment:
    """Pure composer: liveness -> issue-state -> transition -> decision.

    Aggregates the four pure layers into one frozen :class:`SessionAssessment`
    that EMBEDS the typed sub-results, so cleanup and status can never disagree
    on the same snapshot.
    """
    verdict = assess_liveness(signals)
    issue_state = assess_issue_state(issue_facts)
    transition = assess_transition(prior_last_active, verdict)
    decision = decide(verdict, issue_state, transition, git_status, directory_empty)
    pid_needs_refresh = verdict.active and signals.found_pid is not None
    return SessionAssessment(
        folder=folder,
        signals=signals,
        verdict=verdict,
        issue_state=issue_state,
        transition=transition,
        decision=decision,
        pid_needs_refresh=pid_needs_refresh,
        found_pid=signals.found_pid,
    )
