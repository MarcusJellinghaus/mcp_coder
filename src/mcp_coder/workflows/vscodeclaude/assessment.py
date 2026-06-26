"""Assessment layers for vscodeclaude session state.

This module is the ``assess`` stage of the detect -> assess -> decide ->
render/apply pipeline. The layer functions (:func:`assess_liveness`,
:func:`assess_issue_state`, :func:`assess_transition`, :func:`decide`,
:func:`assess_session`) are PURE: they import only ``types`` (no
``sessions``/``psutil``/``win32``), so the rule matrix is unit-testable without
Windows.

The IssueFacts producer (:func:`_issue_facts`) is the one issue-data IO boundary
here: it reuses the cached-issue eligibility logic of ``get_stale_sessions`` so the
pure issue-state layer classifies issues identically to today's cleanup path.
"""

import logging
from dataclasses import dataclass

from ...mcp_workspace_github import (
    IssueData,
    IssueManager,
    RepoIdentifier,
    get_all_cached_issues,
)
from .issues import get_matching_ignore_label, is_status_eligible_for_session
from .status import is_session_stale
from .types import (
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

logger = logging.getLogger(__name__)


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


def _fetch_issue_individually(
    repo_full_name: str,
    issue_number: int,
) -> dict[int, IssueData] | None:
    """Individual-issue API fallback when a session issue is missing from cache.

    Mirrors ``get_stale_sessions``' fallback (cleanup.py): fetches through the
    caching layer with ``additional_issues=[issue_number]`` so the missing issue
    is populated without a double API round-trip. Returns the fetched issues
    keyed by number, or ``None`` when the fetch fails.
    """
    try:
        repo_url = f"https://github.com/{repo_full_name}"
        issue_manager = IssueManager(repo_url=repo_url)
        fetched = get_all_cached_issues(
            RepoIdentifier.from_full_name(repo_full_name),
            issue_manager=issue_manager,
            additional_issues=[issue_number],
        )
        return {issue["number"]: issue for issue in fetched}
    except (
        Exception
    ):  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.debug(
            "Failed to fetch issue #%d individually; skipping eligibility checks",
            issue_number,
        )
        return None


def _issue_facts(
    session: VSCodeClaudeSession,
    cached_issue: IssueData | None,
    *,
    github_username: str | None,
    ignore_labels: set[str],
    cached_for_stale_check: dict[int, IssueData] | None,
) -> IssueFacts:
    """Derive frozen :class:`IssueFacts` from cached issue data.

    Replicates the eligibility logic of ``get_stale_sessions`` (cleanup.py):
    closed/blocked/ineligible/unassigned, plus ``is_session_stale`` — the inputs
    :func:`assess_issue_state` classifies. Reuses the existing helpers rather than
    re-implementing them.

    When ``cached_issue`` is ``None`` (the issue is missing from the cache) the
    individual-issue API fallback is invoked to populate it. Staleness is computed
    ONLY when the issue is not closed/blocked/unassigned/ineligible — calling
    ``is_session_stale`` on such an issue triggers a spurious staleness warning the
    current code explicitly guards against (cleanup.py short-circuit).
    """
    issue = cached_issue
    stale_cache = cached_for_stale_check

    # Individual-issue API fallback when the issue is missing from the cache.
    if issue is None:
        fetched_dict = _fetch_issue_individually(
            session["repo"], session["issue_number"]
        )
        if fetched_dict is not None:
            issue = fetched_dict.get(session["issue_number"])
            if issue is not None:
                stale_cache = fetched_dict

    is_closed = False
    is_blocked = False
    is_ineligible = False
    is_unassigned = False
    status_labels: list[str] = []

    if issue is not None:
        # Issue is closed?
        is_closed = issue["state"] == "closed"
        # Has a blocked/ignore label?
        if get_matching_ignore_label(issue["labels"], ignore_labels):
            is_blocked = True
        # Current status eligible for a session?
        status_labels = [lbl for lbl in issue["labels"] if lbl.startswith("status-")]
        if status_labels:
            current_status = status_labels[0]
            is_ineligible = not is_status_eligible_for_session(current_status)
            # Assignment only matters for open, eligible statuses — if the issue
            # is closed, blocked, or ineligible, assignment is irrelevant.
            if (
                github_username is not None
                and not is_closed
                and not is_blocked
                and not is_ineligible
                and is_status_eligible_for_session(current_status)
            ):
                is_unassigned = github_username not in issue["assignees"]

    # Short-circuit: compute staleness ONLY when the issue is otherwise eligible.
    # The ``and``-chain stops before ``is_session_stale`` for closed/blocked/
    # unassigned/ineligible issues, preserving the cleanup.py guard.
    is_stale = (
        not is_closed
        and not is_blocked
        and not is_unassigned
        and not is_ineligible
        and is_session_stale(session, cached_issues=stale_cache)
    )

    # Stale target for the reason string, derived exactly as cleanup.py does.
    stale_target: str | None = None
    if stale_cache is not None and status_labels:
        stale_target = status_labels[0]

    return IssueFacts(
        is_closed=is_closed,
        is_stale=is_stale,
        is_blocked=is_blocked,
        is_unassigned=is_unassigned,
        is_ineligible=is_ineligible,
        stale_target=stale_target,
    )
