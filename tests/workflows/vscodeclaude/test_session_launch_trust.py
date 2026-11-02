"""Body trust decides the session mode at launch and restart."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import (
    BodyTrust,
    BodyTrustResult,
    GitHubRateLimitError,
    IssueData,
)
from mcp_coder.workflows.vscodeclaude.session_launch import (
    prepare_and_launch_session,
    process_eligible_issues,
    regenerate_session_files,
)
from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeSession
from tests.github_factories import make_issue_data
from tests.workflows.vscodeclaude.conftest import make_session_at, patch_branch_cache

LAUNCH = "mcp_coder.workflows.vscodeclaude.session_launch"
TITLE = "Real title"


def _result(status: BodyTrust) -> BodyTrustResult:
    return BodyTrustResult(status=status, reason="test")


def _issue() -> IssueData:
    return make_issue_data(
        number=42,
        title=TITLE,
        labels=["status-07:code-review"],
        assignees=["testuser"],
    )


@pytest.fixture
def writers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> SimpleNamespace:
    """Patch every side-effecting step of launch and restart with a MagicMock."""
    mocks = SimpleNamespace(
        create_working_folder=MagicMock(return_value=True),
        setup_git_repo=MagicMock(),
        validate_target_repo=MagicMock(),
        update_gitignore=MagicMock(),
        create_workspace_file=MagicMock(return_value=tmp_path / "w.code-workspace"),
        create_startup_script=MagicMock(return_value=tmp_path / "start.bat"),
        create_vscode_task=MagicMock(),
        create_status_file=MagicMock(),
        launch_vscode=MagicMock(return_value=9999),
        add_session=MagicMock(),
        get_current_branch_name=MagicMock(return_value="feature"),
    )
    for name, mock in vars(mocks).items():
        monkeypatch.setattr(f"{LAUNCH}.{name}", mock)
    return mocks


def _set_trust(monkeypatch: pytest.MonkeyPatch, trust: MagicMock) -> MagicMock:
    monkeypatch.setattr(f"{LAUNCH}.evaluate_body_trust", trust)
    return trust


def _launch(tmp_path: Path) -> None:
    prepare_and_launch_session(
        issue=_issue(),
        repo_config={"repo_url": "https://github.com/owner/repo"},
        vscodeclaude_config={"workspace_base": str(tmp_path), "max_sessions": 3},
        repo_vscodeclaude_config={},
        branch_name="feature",
        issue_manager=MagicMock(),
    )


def _session(tmp_path: Path) -> VSCodeClaudeSession:
    return make_session_at(str(tmp_path / "repo_42"))


def _assert_writers(writers: SimpleNamespace, *, title: str, untrusted: bool) -> None:
    assert writers.create_workspace_file.call_args.kwargs["issue_title"] == title
    for writer in (writers.create_startup_script, writers.create_status_file):
        assert writer.call_args.kwargs["issue_title"] == title
        assert writer.call_args.kwargs["untrusted_body"] is untrusted


class TestLaunchTrust:
    """prepare_and_launch_session passes the trust outcome to the writers."""

    @pytest.mark.parametrize(
        "status", [BodyTrust.UNTRUSTED, BodyTrust.LOOKUP_FAILED], ids=str
    )
    def test_not_trusted_blanks_title(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        writers: SimpleNamespace,
        status: BodyTrust,
    ) -> None:
        _set_trust(monkeypatch, MagicMock(return_value=_result(status)))

        _launch(tmp_path)

        _assert_writers(writers, title="", untrusted=True)

    def test_trusted_keeps_title(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, writers: SimpleNamespace
    ) -> None:
        _set_trust(monkeypatch, MagicMock(return_value=_result(BodyTrust.TRUSTED)))

        _launch(tmp_path)

        _assert_writers(writers, title=TITLE, untrusted=False)

    def test_plain_mock_result_counts_as_untrusted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, writers: SimpleNamespace
    ) -> None:
        _set_trust(monkeypatch, MagicMock())

        _launch(tmp_path)

        _assert_writers(writers, title="", untrusted=True)

    def test_rate_limit_leaves_no_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, writers: SimpleNamespace
    ) -> None:
        _set_trust(monkeypatch, MagicMock(side_effect=GitHubRateLimitError("limited")))

        with pytest.raises(GitHubRateLimitError):
            _launch(tmp_path)

        writers.create_working_folder.assert_not_called()
        assert not [p for p in tmp_path.iterdir() if p.name.endswith("_42")]


class TestRestartTrust:
    """regenerate_session_files re-evaluates trust on every call."""

    def test_rate_limit_writes_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, writers: SimpleNamespace
    ) -> None:
        _set_trust(monkeypatch, MagicMock(side_effect=GitHubRateLimitError("limited")))

        with pytest.raises(GitHubRateLimitError):
            regenerate_session_files(_session(tmp_path), _issue())

        writers.create_startup_script.assert_not_called()
        writers.create_vscode_task.assert_not_called()
        writers.create_status_file.assert_not_called()
        writers.create_workspace_file.assert_not_called()

    def test_each_restart_recomputes_trust(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, writers: SimpleNamespace
    ) -> None:
        trust = _set_trust(
            monkeypatch,
            MagicMock(
                side_effect=[
                    _result(BodyTrust.UNTRUSTED),
                    _result(BodyTrust.TRUSTED),
                ]
            ),
        )
        session = _session(tmp_path)

        regenerate_session_files(session, _issue())
        _assert_writers(writers, title="", untrusted=True)

        regenerate_session_files(session, _issue())
        _assert_writers(writers, title=TITLE, untrusted=False)
        assert trust.call_count == 2

    def test_builds_issue_manager_for_session_repo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, writers: SimpleNamespace
    ) -> None:
        manager_cls = MagicMock()
        monkeypatch.setattr(f"{LAUNCH}.IssueManager", manager_cls)
        trust = _set_trust(
            monkeypatch, MagicMock(return_value=_result(BodyTrust.TRUSTED))
        )

        regenerate_session_files(_session(tmp_path), _issue())

        manager_cls.assert_called_once_with(repo_url="https://github.com/owner/repo")
        assert trust.call_args.args[0] is manager_cls.return_value


class TestProcessEligibleIssuesTrust:
    """process_eligible_issues hands its issue manager to the launch."""

    def test_passes_issue_manager(self, monkeypatch: pytest.MonkeyPatch) -> None:
        issue = make_issue_data(
            number=123,
            title="Test Issue",
            labels=["status-01:created"],
            assignees=["testuser"],
        )
        issue_manager = MagicMock()
        monkeypatch.setattr(f"{LAUNCH}.IssueManager", lambda **_kw: issue_manager)
        patch_branch_cache(monkeypatch, LAUNCH)
        monkeypatch.setattr(
            f"{LAUNCH}._filter_eligible_vscodeclaude_issues", lambda *_a: [issue]
        )
        monkeypatch.setattr(f"{LAUNCH}.get_session_for_issue", lambda *_a, **_kw: None)
        monkeypatch.setattr(f"{LAUNCH}.get_github_username", lambda: "testuser")
        monkeypatch.setattr(f"{LAUNCH}.load_repo_vscodeclaude_config", lambda _n: {})
        launch = MagicMock()
        monkeypatch.setattr(f"{LAUNCH}.prepare_and_launch_session", launch)

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
            all_cached_issues=[issue],
        )

        launch.assert_called_once()
        assert launch.call_args.kwargs["issue_manager"] is issue_manager
