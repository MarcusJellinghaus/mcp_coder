"""Tests for git-related exit code logic in verify."""

from typing import Any

from mcp_coder.cli.commands.verify_exit_code import _compute_exit_code


def _claude_ok() -> dict[str, Any]:
    return {
        "cli_found": {"ok": True, "value": "YES"},
        "cli_works": {"ok": True, "value": "YES"},
        "api_integration": {"ok": True, "value": "OK", "error": None},
        "overall_ok": True,
    }


def _mlflow_not_installed() -> dict[str, Any]:
    return {
        "installed": {"ok": False, "value": "not installed"},
        "overall_ok": True,
    }


class TestGitExitCode:
    """Tests for git-related exit code logic in _compute_exit_code."""

    def test_git_failure_returns_exit_1(self) -> None:
        """Exit 1 when git_result overall_ok is False."""
        assert (
            _compute_exit_code(
                "claude",
                _claude_ok(),
                None,
                _mlflow_not_installed(),
                git_result={"overall_ok": False},
            )
            == 1
        )

    def test_git_ok_does_not_affect_exit(self) -> None:
        """Exit 0 when git_result overall_ok is True."""
        assert (
            _compute_exit_code(
                "claude",
                _claude_ok(),
                None,
                _mlflow_not_installed(),
                git_result={"overall_ok": True},
            )
            == 0
        )

    def test_git_none_does_not_affect_exit(self) -> None:
        """Exit 0 when git_result is None (default)."""
        assert (
            _compute_exit_code(
                "claude",
                _claude_ok(),
                None,
                _mlflow_not_installed(),
                git_result=None,
            )
            == 0
        )
