"""Pure failure-message builder for failed Claude CLI runs.

This is the only place that matches auth patterns and adds the login hint.
No I/O, no logging, no imports from ``mcp_coder``.
"""

__all__ = ["build_cli_failure"]

_AUTH_HINT = "Run `claude`, then `/login`."
_AUTH_PATTERNS = (
    "not logged in",  # confirmed by the capture
    "please run /login",  # confirmed by the capture
    "authentication_error",  # #148 repro
    "oauth token has expired",  # #148 repro
    "invalid api key",
)
_STDERR_LIMIT = 500


def build_cli_failure(
    result_text: str | None,
    is_error: bool,
    subtype: str | None,
    stderr: str,
    return_code: int,
) -> tuple[str, str]:
    """Build the error-event (message, reason) for a failed Claude CLI run.

    Call only on failure (non-zero exit or is_error). Auth patterns are
    matched against the ``result`` message text (only when ``is_error``) or
    else the full stderr. Assistant text is never passed in, so it is never
    matched.

    Args:
        result_text: Text of the final ``result`` message, if any.
        is_error: The ``is_error`` flag of the final ``result`` message.
        subtype: The ``subtype`` of the final ``result`` message, if any.
        stderr: Captured stderr of the CLI process.
        return_code: Exit code of the CLI process.

    Returns:
        ``(message, reason)`` where reason is
        ``"auth"`` | ``"nonzero_exit"`` | ``"result_error"``.
    """
    result = (result_text or "").strip() if is_error else ""
    failure_text = result or stderr
    if any(pattern in failure_text.lower() for pattern in _AUTH_PATTERNS):
        text = result or stderr[:_STDERR_LIMIT]
        return f"{_AUTH_HINT} {' '.join(text.split())}", "auth"

    reason = "nonzero_exit" if return_code != 0 else "result_error"
    stderr_part = stderr[:_STDERR_LIMIT]
    if result:
        message = result + (f"; stderr: {stderr_part}" if stderr else "")
    elif is_error:
        message = "CLI reported an error"
        if subtype and subtype != "success":
            message += f" (subtype: {subtype})"
        if stderr:
            message += f": {stderr_part}"
    else:
        message = f"CLI failed with code {return_code}"
        if stderr:
            message += f": {stderr_part}"
    return message, reason
