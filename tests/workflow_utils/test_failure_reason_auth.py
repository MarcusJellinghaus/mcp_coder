"""Auth failures map to the ``auth`` reason and keep the hint in comments (#33)."""

import pytest

from mcp_coder.llm.error_summary import comment_safe
from mcp_coder.llm.interface import LLMAuthError
from mcp_coder.llm.providers.langchain import _exceptions as langchain_exceptions
from mcp_coder.workflow_utils.failure_handling import (
    exception_summary,
    llm_failure_reason,
)
from tests.logged_out_capture import AUTH_HINT, AUTH_MESSAGE

# Issue #148: the CLI text for an expired OAuth token, prefixed by the hint.
_EXPIRED_TOKEN_MESSAGE = (
    f"{AUTH_HINT} API Error: 401 "
    '{"type":"error","error":{"type":"authentication_error",'
    '"message":"OAuth token has expired. Please obtain a new token or refresh '
    'your existing token."},"request_id":"req_011CVabcdefghijklmnopqrs"} '
    "· Please run /login"
)


def test_claude_auth_error_maps_to_auth() -> None:
    """The Claude-style ``LLMAuthError`` is classified as ``auth``."""
    assert llm_failure_reason(LLMAuthError("x")) == "auth"


def test_langchain_auth_error_maps_to_auth() -> None:
    """The langchain ``raise_auth_error`` path is classified as ``auth``."""
    with pytest.raises(langchain_exceptions.LLMAuthError) as excinfo:
        langchain_exceptions.raise_auth_error(
            "OpenAI", "OPENAI_API_KEY", ValueError("bad key")
        )

    assert llm_failure_reason(excinfo.value) == "auth"


def test_hint_survives_comment_safe() -> None:
    """The comment-safe summary starts with the type name and the hint."""
    text = comment_safe(exception_summary(LLMAuthError(AUTH_MESSAGE)))

    assert text.startswith(f"LLMAuthError: {AUTH_HINT}")


def test_long_cli_text_is_capped_and_keeps_the_hint() -> None:
    """#148's long 401 text fits the 300-char cap and still leads with the hint."""
    text = comment_safe(exception_summary(LLMAuthError(_EXPIRED_TOKEN_MESSAGE)))

    assert len(text) <= 300
    assert text.startswith(f"LLMAuthError: {AUTH_HINT}")
