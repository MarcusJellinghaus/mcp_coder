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


# Default max sessions
DEFAULT_MAX_SESSIONS: int = 3

# Default timeout for mcp-coder prompt calls in startup scripts (seconds)
DEFAULT_PROMPT_TIMEOUT: int = 300  # 5 minutes
