"""Real logged-out Claude CLI capture (issue #33) and its expected messages.

Shared by the streaming, blocking and display auth-error tests. Lives at the
``tests`` root so test packages can share it without cross-importing.
"""

from pathlib import Path

FIXTURE = (
    Path(__file__).parent
    / "llm"
    / "providers"
    / "claude"
    / "fixtures"
    / "logged_out_stream.ndjson"
)
LOGGED_OUT_RC = 1
LOGGED_OUT_STDERR = (
    "Ignoring 78 permissions.allow entries from .claude/settings.local.json: "
    "this workspace has not been trusted. Run Claude Code interactively here "
    "once and accept the trust dialog, or set "
    'projects["C:/project"].hasTrustDialogAccepted: true in '
    "C:\\project\\.scratch\\claude_empty_config\\.claude.json.\n"
)
AUTH_HINT = "Run `claude`, then `/login`."
CLI_TEXT = "Not logged in \u00b7 Please run /login"
AUTH_MESSAGE = f"{AUTH_HINT} {CLI_TEXT}"


def load_logged_out_lines() -> list[str]:
    """Return the fixture's NDJSON lines (CRLF-safe)."""
    return FIXTURE.read_text(encoding="utf-8").splitlines()
