"""Tests for GitHub-related exit code logic in verify."""

from typing import Any

from mcp_coder.cli.commands.verify_exit_code import _compute_exit_code


def _claude_ok() -> dict[str, Any]:
    return {
        "cli_found": {"ok": True, "value": "YES"},
        "cli_works": {"ok": True, "value": "YES"},
        "api_integration": {"ok": True, "value": "OK", "error": None},
        "overall_ok": True,
    }


def _langchain_ok() -> dict[str, Any]:
    return {
        "backend": {"ok": True, "value": "openai"},
        "model": {"ok": True, "value": "gpt-4"},
        "api_key": {"ok": True, "value": "sk-ab...7x2f", "source": "env var"},
        "langchain_core": {"ok": True, "value": "installed"},
        "backend_package": {"ok": True, "value": "langchain-openai installed"},
        "overall_ok": True,
    }


def _mlflow_not_installed() -> dict[str, Any]:
    return {
        "installed": {"ok": False, "value": "not installed"},
        "overall_ok": True,
    }


class TestGitHubExitCode:
    """Tests for GitHub-related exit code logic in _compute_exit_code."""

    def test_github_failure_returns_exit_1(self) -> None:
        """Exit 1 when github_result overall_ok is False."""
        assert (
            _compute_exit_code(
                "claude",
                _claude_ok(),
                None,
                _mlflow_not_installed(),
                github_result={"overall_ok": False},
            )
            == 1
        )

    def test_github_ok_does_not_affect_exit(self) -> None:
        """Exit 0 when github_result overall_ok is True."""
        assert (
            _compute_exit_code(
                "claude",
                _claude_ok(),
                None,
                _mlflow_not_installed(),
                github_result={"overall_ok": True},
            )
            == 0
        )

    def test_github_none_does_not_affect_exit(self) -> None:
        """Exit 0 when github_result is None (default)."""
        assert (
            _compute_exit_code(
                "claude",
                _claude_ok(),
                None,
                _mlflow_not_installed(),
                github_result=None,
            )
            == 0
        )

    def test_github_failure_exit_1_regardless_of_provider(self) -> None:
        """Exit 1 when github_result fails for both claude and langchain."""
        github_fail = {"overall_ok": False}
        assert (
            _compute_exit_code(
                "claude",
                _claude_ok(),
                None,
                _mlflow_not_installed(),
                github_result=github_fail,
            )
            == 1
        )
        assert (
            _compute_exit_code(
                "langchain",
                _claude_ok(),
                _langchain_ok(),
                _mlflow_not_installed(),
                github_result=github_fail,
            )
            == 1
        )

    def test_unverifiable_branch_protection_does_not_affect_exit(self) -> None:
        """Exit 0 when branch-protection rows are unverifiable (ok=None).

        Every branch-protection row is severity="warning", overall_ok counts
        only error-severity checks, and _compute_exit_code reads only
        github_result["overall_ok"].
        """
        row = {
            "ok": None,
            "value": "not verifiable — token lacks Administration: Read",
            "error": (
                "get_protection failed: HTTP 403: "
                "Resource not accessible by personal access token"
            ),
            "severity": "warning",
        }
        payload = {
            "token_configured": {
                "ok": True,
                "value": "configured (scopes: unknown)",
                "severity": "error",
            },
            "repo_accessible": {
                "ok": True,
                "value": "accessible",
                "severity": "error",
            },
            "branch_protection": dict(row),
            "ci_checks_required": dict(row),
            "strict_mode": dict(row),
            "force_push": dict(row),
            "branch_deletion": dict(row),
            "overall_ok": True,
        }
        assert (
            _compute_exit_code(
                "claude",
                _claude_ok(),
                None,
                _mlflow_not_installed(),
                github_result=payload,
            )
            == 0
        )
