"""GITHUB SECURITY section tests that call the real ``verify_github_security``.

Only mcp-workspace's ``BaseGitHubManager`` is patched, so these tests pin the
upstream probe's value strings and the no-token outcome that
``_map_security_row`` relies on. No live calls.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify_formatting import STATUS_SYMBOLS
from mcp_coder.cli.commands.verify_sections import _print_github_security_section
from mcp_coder.mcp_workspace_github import GithubException, verify_github_security

_SECTIONS = "mcp_coder.cli.commands.verify_sections"
_PROBES = "mcp_workspace.github_operations._security_probes"


def _render(
    project_dir: Path, repo: MagicMock | None, capsys: pytest.CaptureFixture[str]
) -> str:
    """Run the GITHUB SECURITY section through the real probe; return stdout."""
    with (
        patch(f"{_SECTIONS}.verify_github_security", verify_github_security),
        patch(f"{_PROBES}.BaseGitHubManager") as mock_cls,
    ):
        if repo is None:
            mock_cls.side_effect = ValueError("no token")
        else:
            mock_cls.return_value._get_repository.return_value = repo
        _print_github_security_section(project_dir, STATUS_SYMBOLS)
    return capsys.readouterr().out


def _row(output: str, label: str) -> str:
    """Return the single output line whose label column is ``label``."""
    rows = [
        line for line in output.splitlines() if line.lstrip().startswith(f"{label} ")
    ]
    assert len(rows) == 1, f"expected one {label!r} row, got {rows}"
    return rows[0]


def _make_repo(code_scanning_effect: BaseException | None) -> MagicMock:
    repo = MagicMock()
    repo.url = "https://api.github.com/repos/o/r"
    repo.requester.requestJson.return_value = (204, {}, None)
    repo.security_and_analysis = None
    repo.requester.requestJsonAndCheck.side_effect = code_scanning_effect
    return repo


class TestRealProbeCodeScanning:
    """The code-scanning row for each probe outcome."""

    @pytest.mark.parametrize(
        ("side_effect", "marker", "value"),
        [
            pytest.param(None, "[OK]", "scope present", id="200"),
            pytest.param(
                GithubException(403, {"message": "x"}, None),
                "[ERR]",
                "scope missing or Advanced Security not enabled",
                id="403",
            ),
            pytest.param(
                GithubException(404, {"message": "x"}, None),
                "[WARN]",
                "scope missing or not configured",
                id="404",
            ),
            pytest.param(
                ConnectionError("boom"),
                "[WARN]",
                "not accessible (network error: boom)",
                id="error",
            ),
        ],
    )
    def test_code_scanning_row(
        self,
        side_effect: BaseException | None,
        marker: str,
        value: str,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The probe's result maps to the expected marker and value."""
        output = _render(tmp_path, _make_repo(side_effect), capsys)

        line = _row(output, "Code scanning alerts")
        assert marker in line
        assert value in line


class TestRealProbeRepoUnresolvable:
    """All API-backed rows when the repository cannot be resolved."""

    def test_all_api_rows_not_accessible(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Each of the five API-backed rows renders as not accessible."""
        output = _render(tmp_path, None, capsys)

        for label in (
            "Dependabot alerts",
            "Dependabot security",
            "Secret scanning",
            "Secret push protection",
            "Code scanning alerts",
        ):
            line = _row(output, label)
            assert "[WARN]" in line
            assert "not accessible (repository not accessible)" in line
