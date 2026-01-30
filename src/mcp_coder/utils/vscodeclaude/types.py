"""Type definitions and constants for vscodeclaude feature."""

from typing import TypedDict


class VSCodeClaudeSession(TypedDict):
    """Single session tracking data."""

    folder: str  # Full path to working folder
    repo: str  # "owner/repo" format
    issue_number: int
    status: str  # e.g., "status-07:code-review"
    vscode_pid: int | None
    started_at: str  # ISO 8601
    is_intervention: bool


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


# Priority order for human_action statuses (later stages first)
VSCODECLAUDE_PRIORITY: list[str] = [
    "status-10:pr-created",
    "status-07:code-review",
    "status-04:plan-review",
    "status-01:created",
]

# Mapping of status to slash commands
HUMAN_ACTION_COMMANDS: dict[str, tuple[str | None, str | None]] = {
    # status: (initial_command, followup_command)
    "status-01:created": ("/issue_analyse", "/discuss"),
    "status-04:plan-review": ("/plan_review", "/discuss"),
    "status-07:code-review": ("/implementation_review", "/discuss"),
    "status-10:pr-created": (None, None),  # Show PR URL only
}

# Status emoji mapping for banners
STATUS_EMOJI: dict[str, str] = {
    "status-01:created": "📝",
    "status-04:plan-review": "📋",
    "status-07:code-review": "🔍",
    "status-10:pr-created": "🎉",
}

# Stage display name mapping
STAGE_DISPLAY_NAMES: dict[str, str] = {
    "status-01:created": "ISSUE ANALYSIS",
    "status-04:plan-review": "PLAN REVIEW",
    "status-07:code-review": "CODE REVIEW",
    "status-10:pr-created": "PR CREATED",
}

# Default max sessions
DEFAULT_MAX_SESSIONS: int = 3

# Default timeout for mcp-coder prompt calls in startup scripts (seconds)
DEFAULT_PROMPT_TIMEOUT: int = 300  # 5 minutes
