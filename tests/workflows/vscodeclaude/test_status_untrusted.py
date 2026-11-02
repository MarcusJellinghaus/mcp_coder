"""Status table marker and finder for launch rows with an untrusted body."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import BodyTrust, BodyTrustResult, IssueData
from mcp_coder.workflows.vscodeclaude.issues import find_untrusted_launch_keys
from mcp_coder.workflows.vscodeclaude.status import display_status_table
from tests.github_factories import make_issue_data
from tests.workflows.vscodeclaude.conftest import _build_assessment, make_session_at

_ISSUES = "mcp_coder.workflows.vscodeclaude.issues"
_MARKER = "(untrusted body: review-only)"


def _issue(number: int, status: str = "status-01:created") -> IssueData:
    return make_issue_data(
        number=number, labels=[status], assignees=["testuser"], url=""
    )


def _row(output: str, number: int) -> str:
    return next(line for line in output.splitlines() if f"#{number} " in line)


class TestDisplayUntrustedMarker:
    """display_status_table marks only "Create and start" rows."""

    def test_create_and_start_row_marked(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        display_status_table(
            sessions=[],
            eligible_issues=[("owner/repo", _issue(1)), ("owner/repo", _issue(2))],
            workspace_base=str(tmp_path),
            assessments={},
            untrusted_keys={("owner/repo", 1)},
        )

        out = capsys.readouterr().out
        assert f"-> Create and start {_MARKER}" in _row(out, 1)
        assert _MARKER not in _row(out, 2)

    def test_needs_branch_and_awaiting_merge_rows_unmarked(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        display_status_table(
            sessions=[],
            eligible_issues=[
                ("owner/repo", _issue(3, "status-04:plan-review")),
                ("owner/repo", _issue(4, "status-10:pr-created")),
            ],
            workspace_base=str(tmp_path),
            assessments={},
            issues_without_branch={("owner/repo", 3)},
            untrusted_keys={("owner/repo", 3), ("owner/repo", 4)},
        )

        out = capsys.readouterr().out
        assert "-> Needs branch" in _row(out, 3)
        assert "(awaiting merge)" in _row(out, 4)
        assert _MARKER not in out

    def test_session_row_unmarked(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        folder = tmp_path / "issue-42"
        folder.mkdir()
        session = make_session_at(str(folder), issue_number=42)

        display_status_table(
            sessions=[session],
            eligible_issues=[("owner/repo", _issue(42))],
            workspace_base=str(tmp_path),
            assessments={session["folder"]: _build_assessment(session)},
            untrusted_keys={("owner/repo", 42)},
        )

        out = capsys.readouterr().out
        assert "#42" in out
        assert _MARKER not in out


@pytest.fixture
def trust_mocks(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock]:
    """Patch evaluate_body_trust and IssueManager in the issues module."""
    trust = MagicMock(
        return_value=BodyTrustResult(status=BodyTrust.TRUSTED, reason="test")
    )
    manager_cls = MagicMock(side_effect=lambda repo_url: MagicMock(url=repo_url))
    monkeypatch.setattr(f"{_ISSUES}.evaluate_body_trust", trust)
    monkeypatch.setattr(f"{_ISSUES}.IssueManager", manager_cls)
    return trust, manager_cls


class TestFindUntrustedLaunchKeys:
    """find_untrusted_launch_keys looks up only launchable rows."""

    def test_untrusted_and_lookup_failed_included_trusted_excluded(
        self, trust_mocks: tuple[MagicMock, MagicMock]
    ) -> None:
        trust, _ = trust_mocks
        results = {
            1: BodyTrust.TRUSTED,
            2: BodyTrust.UNTRUSTED,
            3: BodyTrust.LOOKUP_FAILED,
        }
        trust.side_effect = lambda _mgr, issue: BodyTrustResult(
            status=results[issue["number"]], reason="test"
        )

        keys = find_untrusted_launch_keys(
            [("owner/repo", _issue(n)) for n in (1, 2, 3)], [], set(), None
        )

        assert keys == {("owner/repo", 2), ("owner/repo", 3)}

    def test_skipped_rows_get_no_lookup(
        self, trust_mocks: tuple[MagicMock, MagicMock]
    ) -> None:
        trust, manager_cls = trust_mocks
        session = make_session_at("C:/work/issue-1", issue_number=1)

        keys = find_untrusted_launch_keys(
            [
                ("owner/repo", _issue(1)),  # has a session
                ("owner/repo", _issue(2, "status-04:plan-review")),  # needs branch
                ("owner/repo", _issue(3, "status-10:pr-created")),  # ineligible
                ("owner/other", _issue(4)),  # filtered repo
                ("owner/repo", _issue(5)),  # looked up
            ],
            [session],
            {("owner/repo", 2)},
            "repo",
        )

        assert keys == set()
        assert trust.call_count == 1
        assert trust.call_args.args[1]["number"] == 5
        manager_cls.assert_called_once_with(repo_url="https://github.com/owner/repo")

    def test_one_issue_manager_per_repo(
        self, trust_mocks: tuple[MagicMock, MagicMock]
    ) -> None:
        trust, manager_cls = trust_mocks

        find_untrusted_launch_keys(
            [
                ("owner/a", _issue(1)),
                ("owner/a", _issue(2)),
                ("owner/b", _issue(3)),
            ],
            [],
            set(),
            None,
        )

        assert trust.call_count == 3
        assert manager_cls.call_count == 2
        managers = [call.args[0] for call in trust.call_args_list]
        assert managers[0] is managers[1]
        assert managers[0] is not managers[2]
