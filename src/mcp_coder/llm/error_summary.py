"""Short, human-readable exception summaries for logs and issue comments."""

import re

from mcp_coder.utils.subprocess_runner import CalledProcessError

# Trailing "Stream file: <path>" suffix appended by the claude and copilot CLIs.
_STREAM_FILE_RE = re.compile(r"\s*Stream file: .*\Z")
_COMMENT_LIMIT = 300


def summarize_exception(exc: BaseException) -> str:
    """Summarize an exception as ``"Type: message"``.

    For :class:`CalledProcessError` the message is the decoded ``stderr`` (the
    real cause), unless it is empty once the stream-file suffix is ignored.

    Args:
        exc: The exception to summarize.

    Returns:
        The full summary text, stream-file suffix included.
    """
    name = type(exc).__name__
    if isinstance(exc, CalledProcessError):
        raw = exc.stderr
        if isinstance(raw, bytes):
            raw = raw.decode(errors="replace")
        stderr = (raw or "").strip()
        if _STREAM_FILE_RE.sub("", stderr).strip():
            return f"{name}: {stderr}"
    return f"{name}: {exc}"


def comment_safe(text: str) -> str:
    """Make a summary fit a single-line public issue comment field.

    Collapses whitespace runs to single spaces, strips the trailing
    ``Stream file: …`` suffix and caps the length at ``_COMMENT_LIMIT``.

    Args:
        text: The summary text.

    Returns:
        A single line of at most ``_COMMENT_LIMIT`` characters.
    """
    text = " ".join(text.split())
    text = _STREAM_FILE_RE.sub("", text)
    if len(text) <= _COMMENT_LIMIT:
        return text
    return text[: _COMMENT_LIMIT - 1].rstrip() + "…"
