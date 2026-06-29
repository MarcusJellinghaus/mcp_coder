"""Type definitions and constants for vscodeclaude feature."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, TypedDict


class VSCodeClaudeSession(TypedDict):
    """Single session tracking data."""

    folder: str  # Full path to working folder
    repo: str  # "owner/repo" format
    issue_number: int
    status: str  # e.g., "status-07:code-review"
    vscode_pid: int | None
    vscode_pid_create_time: float | None  # Unix epoch seconds from psutil
    started_at: str  # ISO 8601
    is_intervention: bool
    # Persisted liveness baseline ("never observed" until first apply() run).
    last_active: bool | None
    last_active_rule: str | None


class LivenessRule(str, Enum):
    """Which detection rule decided a session's liveness verdict."""

    TITLE = "title"
    PID = "pid"
    CMDLINE = "cmdline"
    NO_ARTIFACTS = "no_artifacts"
    NO_MATCH = "no_match"


class SessionAction(str, Enum):
    """The next action decided for a session."""

    KEEP_ACTIVE = "keep_active"
    RESTART = "restart"
    DELETE = "delete"
    REMOVE_MISSING = "remove_missing"
    INVESTIGATE_ZOMBIE = "investigate_zombie"
    SKIP = "skip"


@dataclass(frozen=True)
class DetectionSignals:
    """Immutable detection inputs captured at the IO/Windows boundary."""

    folder_exists: bool
    title_match: bool
    cmdline_match: bool
    pid_alive: bool
    found_pid: int | None
    age_seconds: float
    within_grace: bool  # plain bool, computed in gather_signals (Step 4)
    directory_empty: bool  # plain bool, computed in gather_signals (Step 4)


@dataclass(frozen=True)
class LivenessVerdict:
    """Result of the liveness layer."""

    active: bool
    rule: LivenessRule


@dataclass(frozen=True)
class IssueState:
    """Result of the issue-state layer."""

    is_open: bool
    is_stale: bool
    is_blocked: bool
    is_unassigned: bool
    is_eligible: bool
    stale_target: str | None = None


@dataclass(frozen=True)
class Transition:
    """Result of the transition layer."""

    flipped_to_inactive: bool  # active -> inactive flip flag


@dataclass(frozen=True)
class Decision:
    """Result of the decision layer."""

    action: SessionAction
    reason: str
    destructive: bool


@dataclass(frozen=True)
class SessionAssessment:
    """Aggregated, frozen assessment built once per session per run.

    Embeds the four typed sub-results (``verdict``/``issue_state``/
    ``transition``/``decision``); it is not a flattened bag of fields.
    Consumers read ``a.verdict.active``, ``a.decision.action``, etc.
    """

    folder: str
    signals: DetectionSignals
    verdict: LivenessVerdict
    issue_state: IssueState
    transition: Transition
    decision: Decision
    pid_needs_refresh: bool
    found_pid: int | None
    # Git status string computed once at build time ("Clean"/"Dirty"/"Missing"/
    # "No Git"/"Error"). Carried so status display reads the SAME snapshot that
    # fed ``decide`` instead of re-running git (TOCTOU-free determinism).
    git_status: str = ""

    def _flatten(self) -> dict[str, Any]:
        """Flatten signals + the four typed sub-results into a JSON-safe dict.

        Single shared source for ``to_audit_record`` and ``to_explain`` so the
        audit trail, ``--explain`` and the enriched VSCode column cannot drift.

        Returns:
            A JSON-safe dict of the folder, signals, and the four typed
            sub-results.
        """
        return {
            "folder": self.folder,
            "signals": {
                "folder_exists": self.signals.folder_exists,
                "title_match": self.signals.title_match,
                "cmdline_match": self.signals.cmdline_match,
                "pid_alive": self.signals.pid_alive,
                "found_pid": self.signals.found_pid,
                "age_seconds": self.signals.age_seconds,
                "within_grace": self.signals.within_grace,
                "directory_empty": self.signals.directory_empty,
            },
            "verdict": {
                "active": self.verdict.active,
                "rule": self.verdict.rule.value,
            },
            "issue_state": {
                "is_open": self.issue_state.is_open,
                "is_stale": self.issue_state.is_stale,
                "is_blocked": self.issue_state.is_blocked,
                "is_unassigned": self.issue_state.is_unassigned,
                "is_eligible": self.issue_state.is_eligible,
                "stale_target": self.issue_state.stale_target,
            },
            "transition": {
                "flipped_to_inactive": self.transition.flipped_to_inactive,
            },
            "decision": {
                "action": self.decision.action.value,
                "reason": self.decision.reason,
                "destructive": self.decision.destructive,
            },
            "git_status": self.git_status,
            "pid_needs_refresh": self.pid_needs_refresh,
            "found_pid": self.found_pid,
        }

    def to_audit_record(self, session: "VSCodeClaudeSession") -> dict[str, Any]:
        """ONE serializer feeding audit trail, --explain, and the VSCode column.

        Returns:
            The flattened assessment dict enriched with the session's repo,
            issue number, and status.
        """
        record = self._flatten()
        record["repo"] = session["repo"]
        record["issue_number"] = session["issue_number"]
        record["status"] = session["status"]
        return record

    def to_explain(self) -> str:
        """Human-readable single-session dump (delegates to the same flattening).

        Returns:
            A newline-separated text block of the folder, signals, and the four
            typed sub-results.
        """
        data = self._flatten()
        lines = [f"folder: {data['folder']}"]
        for section in ("signals", "verdict", "issue_state", "transition", "decision"):
            lines.append(f"{section}:")
            for key, value in data[section].items():
                lines.append(f"  {key}: {value}")
        lines.append(f"git_status: {data['git_status']}")
        lines.append(f"pid_needs_refresh: {data['pid_needs_refresh']}")
        lines.append(f"found_pid: {data['found_pid']}")
        return "\n".join(lines)


class VSCodeClaudeSessionStore(TypedDict):
    """Session storage file structure."""

    sessions: list[VSCodeClaudeSession]
    last_updated: str  # ISO 8601


class VSCodeClaudeConfig(TypedDict):
    """Configuration for vscodeclaude feature."""

    workspace_base: str
    max_sessions: int


class RepoVSCodeClaudeConfig(TypedDict, total=False):
    """Per-repo vscodeclaude config (extends existing repo config)."""

    setup_commands_windows: list[str]
    setup_commands_linux: list[str]
    setup_commands_macos: list[str]


# Default max sessions
DEFAULT_MAX_SESSIONS: int = 3

# Default timeout for mcp-coder prompt calls in startup scripts (seconds)
DEFAULT_PROMPT_TIMEOUT: int = 300  # 5 minutes
