"""create-plan classifies an auth failure under the general label (#33)."""

from mcp_coder.llm.interface import LLMAuthError
from mcp_coder.workflows.create_plan.core import _prompt_failure
from tests.logged_out_capture import AUTH_HINT, AUTH_MESSAGE


def test_auth_failure_uses_the_general_label() -> None:
    """``auth`` has no own label: it falls back to ``planning_failed``."""
    failure = _prompt_failure(1, LLMAuthError(AUTH_MESSAGE))

    assert failure.category == "planning_failed"
    assert failure.stage == "Prompt 1 (auth)"
    assert AUTH_HINT in failure.message
