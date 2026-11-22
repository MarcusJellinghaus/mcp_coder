"""Auth failures in the CI analysis/fix helpers (workflow_steps/ci.py)."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import LLMAuthError, LLMTimeoutError
from mcp_coder.workflow_steps.ci import CIFixConfig, _run_ci_analysis, _run_ci_fix
from tests.logged_out_capture import AUTH_MESSAGE


def _make_config() -> CIFixConfig:
    """Build a minimal CIFixConfig for exercising the analysis/fix helpers."""
    return CIFixConfig(
        project_dir=Path("/test/project"),
        provider="claude",
        env_vars={},
        mcp_config=None,
        settings_file=None,
    )


def _make_failed_summary() -> dict[str, Any]:
    """Build a minimal failed-jobs summary for _run_ci_analysis."""
    return {
        "job_name": "build",
        "step_name": "pytest",
        "other_failed_jobs": [],
        "log_excerpt": "some failing log",
    }


@patch("mcp_coder.workflow_steps.ci.prompt_llm")
@patch(
    "mcp_coder.workflow_steps.ci.get_prompt_with_substitutions",
    return_value="analysis prompt",
)
def test_analysis_reraises_auth_error(
    _mock_prompt: MagicMock, mock_prompt_llm: MagicMock
) -> None:
    """LLMAuthError from the analysis call propagates unchanged."""
    error = LLMAuthError(AUTH_MESSAGE)
    mock_prompt_llm.side_effect = error

    with pytest.raises(LLMAuthError) as exc_info:
        _run_ci_analysis(_make_config(), _make_failed_summary(), fix_attempt=0)

    assert exc_info.value is error


@patch("mcp_coder.workflow_steps.ci.prompt_llm")
@patch("mcp_coder.workflow_steps.ci.resolve_prompt_slots", return_value={})
@patch("mcp_coder.workflow_steps.ci.get_prompt", return_value="fix prompt")
def test_fix_reraises_auth_error(
    _mock_prompt: MagicMock, _mock_slots: MagicMock, mock_prompt_llm: MagicMock
) -> None:
    """LLMAuthError from the fix call propagates instead of returning False."""
    error = LLMAuthError(AUTH_MESSAGE)
    mock_prompt_llm.side_effect = error

    with pytest.raises(LLMAuthError) as exc_info:
        _run_ci_fix(_make_config(), "problem", fix_attempt=0)

    assert exc_info.value is error


@patch("mcp_coder.workflow_steps.ci.prompt_llm")
@patch("mcp_coder.workflow_steps.ci.resolve_prompt_slots", return_value={})
@patch("mcp_coder.workflow_steps.ci.get_prompt", return_value="fix prompt")
def test_fix_still_absorbs_timeout(
    _mock_prompt: MagicMock, _mock_slots: MagicMock, mock_prompt_llm: MagicMock
) -> None:
    """Decision 10 regression guard: a fix-phase timeout is one failed attempt."""
    mock_prompt_llm.side_effect = LLMTimeoutError("timed out")

    assert _run_ci_fix(_make_config(), "problem", fix_attempt=0) is False
