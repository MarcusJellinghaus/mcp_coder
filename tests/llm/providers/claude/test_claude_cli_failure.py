"""Tests for the pure Claude CLI failure-message builder."""

import pytest

from mcp_coder.llm.providers.claude.claude_cli_failure import build_cli_failure

_HINT = "Run `claude`, then `/login`."
_TRUST_WARNING = "Warning: workspace trust not accepted for this folder"
_ISSUE_148_TEXT = (
    'API Error: 401 {"type":"error","error":{"type":"authentication_error",'
    '"message":"OAuth token has expired. Please obtain a new token or refresh '
    'your existing token."}} · Please run /login'
)


def test_auth_from_result_text_ignores_stderr() -> None:
    message, reason = build_cli_failure(
        "Not logged in · Please run /login",
        is_error=True,
        subtype="success",
        stderr=_TRUST_WARNING,
        return_code=1,
    )
    assert reason == "auth"
    assert message == f"{_HINT} Not logged in · Please run /login"
    assert "stderr" not in message
    assert _TRUST_WARNING not in message


def test_auth_from_issue_148_text() -> None:
    message, reason = build_cli_failure(
        _ISSUE_148_TEXT, is_error=True, subtype="success", stderr="", return_code=1
    )
    assert reason == "auth"
    assert message.startswith(f"{_HINT} ")
    assert "OAuth token has expired" in message


@pytest.mark.parametrize(
    ("result_text", "is_error"),
    [
        (None, False),
        ("", True),
        ("   ", True),
    ],
)
def test_auth_from_stderr(result_text: str | None, is_error: bool) -> None:
    message, reason = build_cli_failure(
        result_text,
        is_error=is_error,
        subtype=None,
        stderr="Invalid API key · Please run /login",
        return_code=1,
    )
    assert reason == "auth"
    assert message == f"{_HINT} Invalid API key · Please run /login"


@pytest.mark.parametrize("text", ["NOT LOGGED IN", "invalid API KEY"])
def test_auth_patterns_case_insensitive(text: str) -> None:
    message, reason = build_cli_failure(
        text, is_error=True, subtype="success", stderr="", return_code=1
    )
    assert reason == "auth"
    assert message == f"{_HINT} {text}"


def test_generic_auth_word_is_not_auth() -> None:
    assert build_cli_failure(
        None, is_error=False, subtype=None, stderr="auth failed", return_code=1
    ) == ("CLI failed with code 1: auth failed", "nonzero_exit")


def test_result_text_ignored_without_is_error() -> None:
    message, reason = build_cli_failure(
        "Please run /login", is_error=False, subtype=None, stderr="", return_code=1
    )
    assert reason == "nonzero_exit"
    assert message == "CLI failed with code 1"


@pytest.mark.parametrize(
    ("return_code", "expected_reason"),
    [(0, "result_error"), (2, "nonzero_exit")],
)
def test_is_error_with_result_text_and_stderr(
    return_code: int, expected_reason: str
) -> None:
    message, reason = build_cli_failure(
        "Something broke",
        is_error=True,
        subtype="success",
        stderr="trace",
        return_code=return_code,
    )
    assert reason == expected_reason
    assert message == "Something broke; stderr: trace"


def test_is_error_with_result_text_without_stderr() -> None:
    message, reason = build_cli_failure(
        "Something broke", is_error=True, subtype=None, stderr="", return_code=0
    )
    assert (message, reason) == ("Something broke", "result_error")


def test_is_error_empty_result_shows_subtype() -> None:
    message, reason = build_cli_failure(
        "",
        is_error=True,
        subtype="error_during_execution",
        stderr="",
        return_code=0,
    )
    assert reason == "result_error"
    assert message == "CLI reported an error (subtype: error_during_execution)"


@pytest.mark.parametrize("subtype", ["success", None])
def test_is_error_empty_result_hides_success_subtype(subtype: str | None) -> None:
    message, _ = build_cli_failure(
        None, is_error=True, subtype=subtype, stderr="", return_code=0
    )
    assert message == "CLI reported an error"


def test_is_error_empty_result_appends_stderr() -> None:
    message, reason = build_cli_failure(
        None, is_error=True, subtype="error_max_turns", stderr="boom", return_code=3
    )
    assert reason == "nonzero_exit"
    assert message == "CLI reported an error (subtype: error_max_turns): boom"


@pytest.mark.parametrize(
    ("result_text", "subtype", "stderr"),
    [
        ("Something broke", "success", ""),
        ("Something broke", "success", "trace"),
        (None, "success", ""),
        (None, "error_during_execution", "trace"),
    ],
)
def test_return_code_zero_never_reports_code_0(
    result_text: str | None, subtype: str, stderr: str
) -> None:
    message, _ = build_cli_failure(
        result_text, is_error=True, subtype=subtype, stderr=stderr, return_code=0
    )
    assert "code 0" not in message


def test_nonzero_exit_without_stderr() -> None:
    assert build_cli_failure(
        None, is_error=False, subtype=None, stderr="", return_code=1
    ) == ("CLI failed with code 1", "nonzero_exit")


def test_stderr_truncated_to_500_chars() -> None:
    stderr = "x" * 600
    message, reason = build_cli_failure(
        None, is_error=False, subtype=None, stderr=stderr, return_code=1
    )
    assert reason == "nonzero_exit"
    assert message == f"CLI failed with code 1: {'x' * 500}"


def test_auth_pattern_beyond_truncation_limit_detected() -> None:
    stderr = "x" * 550 + "not logged in"
    _, reason = build_cli_failure(
        None, is_error=False, subtype=None, stderr=stderr, return_code=1
    )
    assert reason == "auth"


def test_auth_message_from_multiline_stderr_is_one_line() -> None:
    stderr = "Error:\n  Not logged in\r\n  Please run /login\n"
    message, reason = build_cli_failure(
        None, is_error=False, subtype=None, stderr=stderr, return_code=1
    )
    assert reason == "auth"
    assert "\n" not in message
    assert "\r" not in message
    assert message == f"{_HINT} Error: Not logged in Please run /login"
