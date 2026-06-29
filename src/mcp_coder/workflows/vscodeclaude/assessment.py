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
from pathlib import Path
from typing import Any

from ...mcp_workspace_github import (
    IssueData,
    IssueManager,
    RepoIdentifier,
    get_all_cached_issues,
)
from .audit import append_run, assessment_to_record
from .config import get_github_username
from .detection import capture_detection_snapshot, gather_signals
from .issues import (
    get_ignore_labels,
    get_matching_ignore_label,
    is_status_eligible_for_session,
)
from .sessions import get_pid_create_time, load_sessions, save_sessions
from .status import get_folder_git_status, is_session_stale
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

    Returns:
        A frozen :class:`LivenessVerdict` carrying ``active`` and the winning
        :class:`LivenessRule`.
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

    Returns:
        A frozen :class:`IssueState` with the per-flag classification and the
        derived ``is_eligible``.
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

    Returns:
        A frozen :class:`Transition` whose ``flipped_to_inactive`` marks an
        active->inactive flip.
    """
    flipped = prior_last_active is True and not verdict.active
    return Transition(flipped_to_inactive=flipped)


def _ineligibility_reasons(issue_state: IssueState) -> str:
    """Join the reasons an issue is ineligible into one human/audit string.

    Returns:
        Comma-separated reason string (e.g. ``"stale, blocked"``), defaulting
        to ``"ineligible"`` when no specific reason applies.
    """
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

    Returns:
        A frozen :class:`Decision` carrying the resolved :class:`SessionAction`,
        a human reason, and the ``destructive`` flag.
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

    Returns:
        A frozen :class:`SessionAssessment` embedding the verdict, issue-state,
        transition, and decision for the session.
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
        git_status=git_status,
    )


def build_assessments(
    sessions: list[VSCodeClaudeSession],
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> dict[str, SessionAssessment]:
    """READ-ONLY builder: snapshot once, then gather + assess each session.

    Captures a single :class:`DetectionSnapshot` (R4: all detection caches at
    one instant, no age-skew), then per session: gathers signals, derives frozen
    :class:`IssueFacts` from the cache (with the individual-issue fallback), reads
    the git status, and composes a frozen :class:`SessionAssessment`. The prior
    ``last_active`` baseline is read from the session dict and threaded into the
    transition layer. Performs NO disk writes — every mutation lives in
    :func:`apply_assessments`, so read-only consumers (status) can call this
    safely.

    Args:
        sessions: Sessions to assess (typically ``load_sessions()["sessions"]``).
        cached_issues_by_repo: Optional pre-fetched issues for issue-state facts.

    Returns:
        Mapping of each session's folder path to its :class:`SessionAssessment`.
    """
    snapshot = capture_detection_snapshot()

    ignore_labels = get_ignore_labels()
    try:
        github_username: str | None = get_github_username()
    except ValueError:
        logger.debug("GitHub username not configured, skipping assignment checks")
        github_username = None

    assessments: dict[str, SessionAssessment] = {}
    for session in sessions:
        signals = gather_signals(session, snapshot)

        # Mirror get_stale_sessions: issue-state facts (and the individual-issue
        # API fallback inside _issue_facts) are derived ONLY when a cache is
        # available. Without one, default to an all-clear (eligible) IssueFacts
        # so the read-only liveness projection stays network-free.
        if cached_issues_by_repo:
            repo_issues = cached_issues_by_repo.get(session["repo"], {})
            cached_issue = repo_issues.get(session["issue_number"])
            cached_for_stale_check = repo_issues if cached_issue is not None else None
            issue_facts = _issue_facts(
                session,
                cached_issue,
                github_username=github_username,
                ignore_labels=ignore_labels,
                cached_for_stale_check=cached_for_stale_check,
            )
        else:
            issue_facts = IssueFacts(
                is_closed=False,
                is_stale=False,
                is_blocked=False,
                is_unassigned=False,
                is_ineligible=False,
                stale_target=None,
            )

        git_status = get_folder_git_status(Path(session["folder"]))

        assessment = assess_session(
            folder=session["folder"],
            signals=signals,
            issue_facts=issue_facts,
            git_status=git_status,
            directory_empty=signals.directory_empty,
            prior_last_active=session.get("last_active"),
        )
        assessments[session["folder"]] = assessment
        _log_assessment(session, signals, assessment)
    return assessments


def _log_assessment(
    session: VSCodeClaudeSession,
    signals: DetectionSignals,
    assessment: SessionAssessment,
) -> None:
    """Emit the per-session decision line + per-signal debug + transition log.

    The one-glance post-mortem (#38): a single ``logger.info`` carries the winning
    rule, the resolved action, the destructive bit, and the reason; the per-signal
    breakdown drops to ``logger.debug``. A true active->inactive flip is logged
    once (a ``None`` prior baseline is a blind spot, never a flip).
    """
    logger.info(
        "assess #%s: verdict=%s rule=%s -> action=%s destructive=%s reason=%s",
        session["issue_number"],
        assessment.verdict.active,
        assessment.verdict.rule.value,
        assessment.decision.action.value,
        assessment.decision.destructive,
        assessment.decision.reason,
    )
    logger.debug(
        "assess #%s signals: folder_exists=%s title=%s cmdline=%s pid_alive=%s "
        "found_pid=%s age=%.0fs within_grace=%s directory_empty=%s",
        session["issue_number"],
        signals.folder_exists,
        signals.title_match,
        signals.cmdline_match,
        signals.pid_alive,
        signals.found_pid,
        signals.age_seconds,
        signals.within_grace,
        signals.directory_empty,
    )
    if assessment.transition.flipped_to_inactive:
        logger.info(
            "Session #%s flipped active->inactive (was rule=%s)",
            session["issue_number"],
            session.get("last_active_rule"),
        )


def build_active_session_set(
    sessions: list[VSCodeClaudeSession],
) -> dict[str, bool]:
    """Build active-set snapshot (thin read-only wrapper over build_assessments).

    Computes one ``DetectionSnapshot`` and assesses every session, projecting the
    result onto the legacy ``dict[folder, bool]`` contract that the cleanup,
    restart, and status consumers still read. READ-ONLY: unlike the apply path
    this performs no ``sessions.json`` writes — the PID refresh and ``last_active``
    advance moved into :func:`apply_assessments`.

    Returns:
        Mapping of each session's folder path to its liveness ``active`` bool.
    """
    return {
        folder: assessment.verdict.active
        for folder, assessment in build_assessments(sessions).items()
    }


def render_explain(assessments: dict[str, SessionAssessment]) -> str:
    """Render full per-session explanation blocks (on-demand transparency).

    One block per session, produced by the shared
    :meth:`SessionAssessment.to_explain` serializer (the same source feeding the
    audit trail and the enriched VSCode column, so the three surfaces cannot
    drift). Each block dumps the full ``DetectionSignals``, the winning liveness
    rule, the issue-state, transition flip, and the decision/action.

    Pure and READ-ONLY: it consumes the already-built assessments and performs no
    writes — consistent with status being write-free. It must NOT trigger
    :func:`apply_assessments`.

    Args:
        assessments: Folder -> assessment map from :func:`build_assessments`.

    Returns:
        Newline-separated explanation blocks (empty string when no sessions).
    """
    return "\n\n".join(assessment.to_explain() for assessment in assessments.values())


def apply_assessments(
    assessments: dict[str, SessionAssessment],
    sessions: list[VSCodeClaudeSession],
    *,
    write_audit: bool,
) -> None:
    """Apply-only: refresh stale PIDs, advance ``last_active``, write the audit.

    The single mutation point of the pipeline. Loads the session store once and
    applies each assessment's PID refresh and ``last_active``/``last_active_rule``
    advance over the LIVE post-cleanup store — only surviving sessions are mutated
    (sessions deleted by cleanup/restart are correctly gone from the store), then
    writes the store back in ONE atomic save (no double-write).

    When ``write_audit`` is True, also appends ONE audit run-block. The audit is
    sourced from ``assessments`` — the FULL set assessed at build time, threaded
    with the original ``sessions`` for repo/issue/status context — NOT from the
    reloaded store. This is deliberate: cleanup/restart persist their deletions
    before apply runs, so sourcing the audit from the store would silently drop
    exactly the destructive ``delete``/``remove_missing`` records the trail exists
    to capture. A run is one command invocation across all repos, so the status
    path (which never calls apply) leaves no audit record. Read-only consumers
    (status) must NOT call this.

    Args:
        assessments: Folder -> assessment map from :func:`build_assessments`.
        sessions: The original sessions list assessed at build time (BEFORE
            cleanup/restart removed any). Supplies repo/issue/status for the audit
            records so deleted sessions still appear in the trail.
        write_audit: When True, append one run-block to the audit trail.
    """
    store = load_sessions()
    for session in store["sessions"]:
        assessment = assessments.get(session["folder"])
        if assessment is None:
            continue
        if (
            assessment.pid_needs_refresh
            and assessment.found_pid is not None
            and assessment.found_pid != session.get("vscode_pid")
        ):
            session["vscode_pid"] = assessment.found_pid
            session["vscode_pid_create_time"] = get_pid_create_time(
                assessment.found_pid
            )
        session["last_active"] = assessment.verdict.active
        session["last_active_rule"] = assessment.verdict.rule.value
    save_sessions(store)
    if write_audit:
        sessions_by_folder = {s["folder"]: s for s in sessions}
        audit_records: list[dict[str, Any]] = [
            assessment_to_record(assessment, sessions_by_folder[folder])
            for folder, assessment in assessments.items()
            if folder in sessions_by_folder
        ]
        append_run(audit_records)


def _fetch_issue_individually(
    repo_full_name: str,
    issue_number: int,
) -> dict[int, IssueData] | None:
    """Individual-issue API fallback when a session issue is missing from cache.

    Mirrors ``get_stale_sessions``' fallback (cleanup.py): fetches through the
    caching layer with ``additional_issues=[issue_number]`` so the missing issue
    is populated without a double API round-trip.

    Returns:
        The fetched issues keyed by issue number, or ``None`` when the fetch
        fails.
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

    Returns:
        A frozen :class:`IssueFacts` with the closed/stale/blocked/unassigned/
        ineligible flags and the optional stale target.
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
