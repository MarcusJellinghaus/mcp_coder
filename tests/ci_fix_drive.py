"""Drive the real ``check_and_fix_ci`` through one fix attempt, offline.

Shared by entry-point tests (fix-ci, ``check_branch_status --fix``) that must
reach the fix phase's real ``run_formatters`` call. Everything external to the
formatting call is patched: CI status (one failed run that never gets a
successor, so the loop exits gracefully after one push), the LLM, session
storage, commit/push and sleeps. ``workflow_steps.ci.run_formatters`` is left
untouched.
"""

from unittest.mock import MagicMock

import pytest

from mcp_coder.workflow_steps import ci

_FAILED_STATUS = {
    "run": {"run_ids": [1], "status": "completed", "conclusion": "failure"},
    "jobs": [
        {
            "name": "test",
            "conclusion": "failure",
            "run_id": 1,
            "steps": [{"number": 1, "name": "Run tests", "conclusion": "failure"}],
        }
    ],
}

_LLM_RESPONSE = {
    "text": "Analysis complete",
    "session_id": "test-session",
    "version": "1.0",
    "timestamp": "2025-01-01T00:00:00",
    "provider": "claude",
    "raw_response": {},
}


def patch_ci_fix_externals(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch ``check_and_fix_ci``'s externals; return the ``commit_changes`` mock."""
    manager = MagicMock()
    manager.get_latest_ci_status.return_value = _FAILED_STATUS
    manager.get_run_logs.return_value = {"test/1_Run tests.txt": "Error"}
    monkeypatch.setattr(ci, "CIResultsManager", MagicMock(return_value=manager))
    monkeypatch.setattr(ci, "prompt_llm", MagicMock(return_value=_LLM_RESPONSE))
    monkeypatch.setattr(ci, "store_session", MagicMock())
    monkeypatch.setattr(ci, "prepare_llm_environment", MagicMock(return_value={}))
    monkeypatch.setattr(ci, "get_latest_commit_sha", MagicMock(return_value="SHA"))
    monkeypatch.setattr(
        ci, "get_branch_name_for_logging", MagicMock(return_value="feature")
    )
    monkeypatch.setattr("mcp_coder.workflow_steps.ci.time.sleep", MagicMock())
    commit_changes = MagicMock(return_value=True)
    monkeypatch.setattr(ci, "commit_changes", commit_changes)
    monkeypatch.setattr(ci, "push_changes", MagicMock(return_value=True))
    return commit_changes
