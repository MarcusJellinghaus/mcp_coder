"""Tests for branch handling integration."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import (
    BranchLookup,
    BranchLookupError,
    GitHubRateLimitError,
    IssueData,
)
from mcp_coder.workflows.vscodeclaude.session_launch import process_eligible_issues
from mcp_coder.workflows.vscodeclaude.session_restart import (
    BranchPrepResult,
    _prepare_restart_branch,
    restart_closed_sessions,
)
from tests.github_factories import make_issue_data
from tests.workflows.vscodeclaude.conftest import make_assessment, patch_branch_cache

RESTART = "mcp_coder.workflows.vscodeclaude.session_restart"


class TestBranchHandlingIntegration:
    """Integration tests for branch handling feature."""

    def test_full_session_lifecycle_status_01_to_04(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test full lifecycle: create at 01, restart when changed to 04."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Phase 1: Mock session at status-01 (no branch required)
        # Session was created on main branch
        working_folder = tmp_path / "repo_100"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_100.code-workspace"
        workspace_file.write_text("{}")

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 100,
            "status": "status-01:created",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Phase 2: Issue status changes to status-04 with linked branch
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock IssueManager and BranchLookupCache to avoid token validation
        mock_issue_manager = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        patch_branch_cache(monkeypatch, RESTART)

        # Track operations in order
        operations: list[str] = []

        def mock_prepare(
            folder_path: Path,
            current_status: str,
            branch_cache: Any,
            issue: IssueData,
        ) -> BranchPrepResult:
            operations.append(f"prepare_branch:{current_status}")
            # Simulate successful branch switch for status-04
            return BranchPrepResult(True, None, "feat-100")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._prepare_restart_branch",
            mock_prepare,
        )

        def mock_regenerate(session: Any, issue: Any) -> Path:
            operations.append("regenerate_files")
            # Call the mocked create_status_file with the branch from prepare_branch
            mock_create_status(branch_name="feat-100")
            return tmp_path / "script.bat"

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.regenerate_session_files",
            mock_regenerate,
        )

        def mock_create_status(**kwargs: Any) -> None:
            operations.append(f"create_status:branch={kwargs.get('branch_name')}")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.create_status_file",
            mock_create_status,
        )

        launch_session_dirs: list[Path | None] = []

        def mock_launch(
            workspace: Path, session_working_dir: Path | None = None
        ) -> int:
            operations.append("launch_vscode")
            launch_session_dirs.append(session_working_dir)
            return 9999

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.launch_vscode",
            mock_launch,
        )

        status_updates: list[str] = []
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.update_session_status",
            lambda folder, status: status_updates.append(status),
        )

        # Issue now at status-04 with linked branch
        cached_issue = make_issue_data(
            number=100,
            title="Test Issue",
            labels=["status-04:plan-review"],
            assignees=["testuser"],
        )
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {100: cached_issue}
        }

        # Actually call restart_closed_sessions to trigger the restart flow
        result = restart_closed_sessions(
            assessments={str(working_folder): make_assessment(str(working_folder))},
            cached_issues_by_repo=cached_issues,
        )

        # Verify full lifecycle
        assert len(result) == 1
        assert result[0]["vscode_pid"] == 9999

        # Verify operations occurred in order
        assert "prepare_branch:status-04:plan-review" in operations
        assert "regenerate_files" in operations
        assert "create_status:branch=feat-100" in operations
        assert "launch_vscode" in operations

        # Restart opens the session's status file along with the window
        assert launch_session_dirs == [working_folder]

        # Verify status was updated
        assert "status-04:plan-review" in status_updates

    def test_status_04_session_without_branch_skips_completely(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: Any
    ) -> None:
        """Status-04 without branch: doesn't create session, shows indicator."""
        import logging

        # Test process_eligible_issues skipping
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )

        mock_issue_manager = type("MockIssueManager", (), {})()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        patch_branch_cache(
            monkeypatch, "mcp_coder.workflows.vscodeclaude.session_launch"
        )

        # Mock issue at status-04
        mock_issues: list[IssueData] = [
            make_issue_data(
                number=200,
                title="Test",
                labels=["status-04:plan-review"],
                assignees=["testuser"],
                url="",
            )
        ]

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: mock_issues,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda issues, user: issues,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda _repo, _num, **_kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda name: {},
        )
        with caplog.at_level(logging.ERROR):
            sessions = process_eligible_issues(
                repo_name="test",
                repo_config={"repo_url": "https://github.com/owner/repo.git"},
                vscodeclaude_config={
                    "workspace_base": str(tmp_path),
                    "max_sessions": 3,
                },
                max_sessions=3,
                current_count=0,
            )

        # No sessions should be started
        assert sessions == []
        # Log should show error about no linked branch
        assert "no linked branch" in caplog.text.lower()

    def test_dirty_repo_blocks_branch_switch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dirty repo prevents branch switch, shows !! Dirty."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock git fetch success, but dirty status
        mock_checkout = MagicMock(return_value=True)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.fetch_remote",
            MagicMock(return_value=True),
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.checkout_branch",
            mock_checkout,
        )
        patch_branch_cache(monkeypatch, RESTART, branch="feat-branch")
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.get_folder_git_status",
            lambda folder: "Dirty",
        )

        working_folder = tmp_path / "repo_300"
        working_folder.mkdir()

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 300,
            "status": "status-04:plan-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        cached_issue = make_issue_data(
            number=300,
            title="Test",
            labels=["status-04:plan-review"],
            url="",
        )
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {300: cached_issue}
        }

        result = restart_closed_sessions(
            assessments={str(working_folder): make_assessment(str(working_folder))},
            cached_issues_by_repo=cached_issues,
        )

        # Should NOT restart due to dirty repo
        assert len(result) == 0
        mock_checkout.assert_not_called()

    def test_git_fetch_runs_on_every_restart(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """git fetch origin runs on every restart regardless of status."""
        fetch_calls: list[str] = []

        def mock_fetch(folder_path: Path) -> bool:
            fetch_calls.append("fetch")
            return True

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.fetch_remote",
            mock_fetch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.checkout_branch",
            MagicMock(return_value=True),
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.pull",
            MagicMock(
                return_value={
                    "success": True,
                    "error": None,
                    "returncode": 0,
                    "stderr": "",
                }
            ),
        )

        branch_cache = MagicMock()
        branch_cache.lookup.return_value = BranchLookup("found", "feat-branch")
        issue = make_issue_data(number=100)

        # Test with status-01
        _ = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-01:created",
            branch_cache=branch_cache,
            issue=issue,
        )
        assert "fetch" in fetch_calls

        fetch_calls.clear()

        # Test with status-04
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.get_folder_git_status",
            lambda folder: "Clean",
        )

        _ = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_cache=branch_cache,
            issue=issue,
        )
        assert "fetch" in fetch_calls

        fetch_calls.clear()

        # Test with status-07
        _ = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-07:code-review",
            branch_cache=branch_cache,
            issue=issue,
        )
        assert "fetch" in fetch_calls

    def test_intervention_session_requires_branch_for_status_04(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: Any
    ) -> None:
        """Intervention sessions follow same branch rules."""
        import logging

        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock the necessary components for restart flow
        # Mock IssueManager and BranchLookupCache to avoid token validation
        mock_issue_manager = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        patch_branch_cache(monkeypatch, RESTART)

        # Return "No branch" skip reason
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._prepare_restart_branch",
            lambda **kwargs: BranchPrepResult(False, "No branch", None),
        )

        working_folder = tmp_path / "repo_intervention"
        working_folder.mkdir()

        # Create intervention session at status-04
        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 500,
            "status": "status-04:plan-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": True,  # This is an intervention session
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        cached_issue = make_issue_data(
            number=500,
            title="Intervention Test",
            labels=["status-04:plan-review"],
            url="",
        )
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {500: cached_issue}
        }

        with caplog.at_level(logging.WARNING):
            result = restart_closed_sessions(
                assessments={str(working_folder): make_assessment(str(working_folder))},
                cached_issues_by_repo=cached_issues,
            )

        # Should skip - intervention flag doesn't bypass branch requirements
        assert len(result) == 0
        assert "No branch" in caplog.text


class TestRestartBranchCache:
    """restart_closed_sessions uses one BranchLookupCache per repo."""

    @staticmethod
    def _setup(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        sessions: list[tuple[str, int]],
        lookup: Any = None,
    ) -> tuple[dict[str, MagicMock], MagicMock, dict[str, Any]]:
        """Create sessions at status-04 and patch git, launch and the caches.

        Args:
            tmp_path: Workspace base for the session folders.
            monkeypatch: Pytest monkeypatch.
            sessions: ``(repo_full_name, issue_number)`` per session.
            lookup: Optional ``(repo_url, issue) -> BranchLookup`` side effect;
                by default every lookup finds branch ``feat``.

        Returns:
            ``(caches_by_repo_url, launch_mock, restart_kwargs)``.
        """
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        repos = {repo for repo, _ in sessions}
        monkeypatch.setattr(f"{RESTART}._get_configured_repos", lambda: repos)
        monkeypatch.setattr(f"{RESTART}.fetch_remote", MagicMock(return_value=True))
        monkeypatch.setattr(f"{RESTART}.checkout_branch", MagicMock(return_value=True))
        monkeypatch.setattr(
            f"{RESTART}.pull",
            MagicMock(return_value={"success": True, "error": None, "stderr": ""}),
        )
        monkeypatch.setattr(f"{RESTART}.get_folder_git_status", lambda folder: "Clean")
        monkeypatch.setattr(f"{RESTART}.regenerate_session_files", MagicMock())
        launch = MagicMock(return_value=9999)
        monkeypatch.setattr(f"{RESTART}.launch_vscode", launch)

        caches: dict[str, MagicMock] = {}

        def _load(repo_url: str) -> MagicMock:
            cache = MagicMock()
            cache.lookup.return_value = BranchLookup("found", "feat")
            if lookup is not None:
                cache.lookup.side_effect = lambda issue: lookup(repo_url, issue)
            caches[repo_url] = cache
            return cache

        cache_cls = MagicMock()
        cache_cls.load.side_effect = _load
        monkeypatch.setattr(f"{RESTART}.BranchLookupCache", cache_cls)
        monkeypatch.setattr(f"{RESTART}.IssueBranchManager", lambda repo_url: repo_url)

        stored = []
        assessments = {}
        cached: dict[str, dict[int, IssueData]] = {}
        for repo, number in sessions:
            folder = tmp_path / f"{repo.replace('/', '_')}_{number}"
            folder.mkdir()
            (tmp_path / f"{folder.name}.code-workspace").write_text("{}")
            stored.append(
                {
                    "folder": str(folder),
                    "repo": repo,
                    "issue_number": number,
                    "status": "status-04:plan-review",
                    "vscode_pid": None,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            )
            assessments[str(folder)] = make_assessment(str(folder))
            cached.setdefault(repo, {})[number] = make_issue_data(
                number=number, labels=["status-04:plan-review"]
            )
        sessions_file.write_text(json.dumps({"sessions": stored, "last_updated": ""}))
        kwargs = {"assessments": assessments, "cached_issues_by_repo": cached}
        return caches, launch, kwargs

    def test_one_load_and_one_save_per_repo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        caches, launch, kwargs = self._setup(
            tmp_path, monkeypatch, [("owner/a", 1), ("owner/a", 2), ("owner/b", 3)]
        )

        restart_closed_sessions(**kwargs)

        assert set(caches) == {
            "https://github.com/owner/a",
            "https://github.com/owner/b",
        }
        assert caches["https://github.com/owner/a"].lookup.call_count == 2
        for cache in caches.values():
            cache.save.assert_called_once_with()
        assert launch.call_count == 3

    def test_lookup_error_skips_session_and_continues(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _first_fails(_repo_url: str, issue: IssueData) -> BranchLookup:
            if issue["number"] == 1:
                raise BranchLookupError("boom")
            return BranchLookup("found", "feat")

        caches, launch, kwargs = self._setup(
            tmp_path, monkeypatch, [("owner/a", 1), ("owner/a", 2)], _first_fails
        )

        result = restart_closed_sessions(**kwargs)

        assert [s["issue_number"] for s in result] == [2]
        assert launch.call_count == 1
        caches["https://github.com/owner/a"].save.assert_called_once_with()

    def test_rate_limit_in_repo_b_saves_repo_a_cache(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _limit_in_b(repo_url: str, _issue: IssueData) -> BranchLookup:
            if repo_url.endswith("/b"):
                raise GitHubRateLimitError("limited")
            return BranchLookup("found", "feat")

        caches, _, kwargs = self._setup(
            tmp_path, monkeypatch, [("owner/a", 1), ("owner/b", 2)], _limit_in_b
        )

        with pytest.raises(GitHubRateLimitError):
            restart_closed_sessions(**kwargs)

        caches["https://github.com/owner/a"].save.assert_called_once_with()
        caches["https://github.com/owner/b"].save.assert_called_once_with()
