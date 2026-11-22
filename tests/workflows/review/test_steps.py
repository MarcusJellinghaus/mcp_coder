"""Rebase- and CI-gate tests for :func:`steps._after_steps`, called directly.

The shared ``env`` fixture in ``conftest`` mocks the rebase and CI steps.
"""

import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcp_coder.llm.interface import LLMAuthError
from mcp_coder.workflow_steps.rebase import RebaseOutcome
from mcp_coder.workflows.review import steps
from mcp_coder.workflows.review.config import REVIEW_IMPLEMENTATION
from tests.logged_out_capture import AUTH_HINT, AUTH_MESSAGE


def test_failed_rebase_gate_returns_outcome_and_warns(
    env: SimpleNamespace, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A non-ok outcome returns ``("rebase", outcome, None)`` and logs its reason."""
    outcome = RebaseOutcome("dirty_tree", files=("a.py",))
    env.attempt_rebase_and_push.return_value = outcome

    with caplog.at_level(logging.WARNING, logger=steps.__name__):
        result = steps._after_steps(
            REVIEW_IMPLEMENTATION,
            tmp_path,
            "claude",
            None,
            None,
            is_dismiss=True,
        )

    assert result == ("rebase", outcome, None)
    env.check_and_fix_ci.assert_not_called()
    warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert any("dirty_tree" in message for message in warnings)


def test_ci_gate_auth_error_returns_auth_reason(
    env: SimpleNamespace, tmp_path: Path
) -> None:
    """An auth failure in the CI step is terminal ``"auth"``, not a CI finding."""
    env.check_and_fix_ci.side_effect = LLMAuthError(AUTH_MESSAGE)

    reason, _outcome, detail = steps._after_steps(
        REVIEW_IMPLEMENTATION,
        tmp_path,
        "claude",
        None,
        None,
        is_dismiss=False,
    )

    assert reason == "auth"
    assert detail is not None
    assert detail.startswith(f"LLMAuthError: {AUTH_HINT}")
