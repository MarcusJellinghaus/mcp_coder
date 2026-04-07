"""Tests for branch handling integration."""

import json
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.utils.github_operations.issues import IssueData
from mcp_coder.workflows.vscodeclaude.session_launch import process_eligible_issues
from mcp_coder.workflows.vscodeclaude.session_restart import (
    BranchPrepResult,
    _prepare_restart_branch,
    restart_closed_sessions,
)


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
            "install_from_github": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Phase 2: Issue status changes to status-04 with linked branch
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock IssueManager and IssueBranchManager to avoid token validation
        from unittest.mock import MagicMock

        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # Track operations in order
        operations: list[str] = []

        def mock_prepare(
            folder_path: Path,
            current_status: str,
            branch_manager: Any,
            issue_number: int,
            repo_owner: str,
            repo_name: str,
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

        def mock_launch(workspace: Path) -> int:
            operations.append("launch_vscode")
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
        cached_issue: IssueData = {
            "number": 100,
            "title": "Test Issue",
            "state": "open",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/100",
            "body": "",
            "locked": False,
        }
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {100: cached_issue}
        }

        # Actually call restart_closed_sessions to trigger the restart flow
        result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Verify full lifecycle
        assert len(result) == 1
        assert result[0]["vscode_pid"] == 9999

        # Verify operations occurred in order
        assert "prepare_branch:status-04:plan-review" in operations
        assert "regenerate_files" in operations
        assert "create_status:branch=feat-100" in operations
        assert "launch_vscode" in operations

        # Verify status was updated
        assert "status-04:plan-review" in status_updates

    def test_status_04_session_without_branch_skips_completely(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: Any
    ) -> None:
        """Status-04 without branch: doesn't create session, shows indicator."""
        import logging

        # Test process_eligible_issues skipping
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_active_session_count",
            lambda: 0,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )

        mock_issue_manager = type("MockIssueManager", (), {})()
        mock_branch_manager = type(
            "MockBranchManager",
            (),
            {
                "get_branch_with_pr_fallback": lambda self, issue_number, repo_owner, repo_name: None,
            },
        )()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # Mock issue at status-04
        mock_issues: list[IssueData] = [
            {
                "number": 200,
                "title": "Test",
                "state": "open",
                "labels": ["status-04:plan-review"],
                "assignees": ["testuser"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "body": "",
                "locked": False,
            }
        ]

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda **kwargs: mock_issues,
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
            "mcp_coder.workflows.vscodeclaude.session_restart.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock git fetch success, but dirty status
        def mock_execute(cmd: list[str], options: Any) -> Any:
            return type("Result", (), {"stdout": "", "stderr": "", "return_code": 0})()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.execute_subprocess",
            mock_execute,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueBranchManager",
            lambda **kwargs: type(
                "MockBranchManager",
                (),
                {
                    "get_branch_with_pr_fallback": lambda self, issue_number, repo_owner, repo_name: "feat-branch",
                },
            )(),
        )
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
            "install_from_github": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        cached_issue: IssueData = {
            "number": 300,
            "title": "Test",
            "state": "open",
            "labels": ["status-04:plan-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {300: cached_issue}
        }

        result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Should NOT restart due to dirty repo
        assert len(result) == 0

    def test_git_fetch_runs_on_every_restart(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """git fetch origin runs on every restart regardless of status."""
        fetch_calls: list[str] = []

        def mock_execute(cmd: list[str], options: Any) -> Any:
            if "fetch" in cmd:
                fetch_calls.append("fetch")
            return type("Result", (), {"stdout": "", "stderr": "", "return_code": 0})()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.execute_subprocess",
            mock_execute,
        )

        mock_branch_manager = type(
            "MockBranchManager",
            (),
            {
                "get_branch_with_pr_fallback": lambda self, issue_number, repo_owner, repo_name: "feat-branch",
            },
        )()

        # Test with status-01
        _ = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-01:created",
            branch_manager=mock_branch_manager,
            issue_number=100,
            repo_owner="test-owner",
            repo_name="test-repo",
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
            branch_manager=mock_branch_manager,
            issue_number=100,
            repo_owner="owner",
            repo_name="repo",
        )
        assert "fetch" in fetch_calls

        fetch_calls.clear()

        # Test with status-07
        _ = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-07:code-review",
            branch_manager=mock_branch_manager,
            issue_number=100,
            repo_owner="owner",
            repo_name="repo",
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
            "mcp_coder.workflows.vscodeclaude.session_restart.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock the necessary components for restart flow
        # Mock IssueManager and IssueBranchManager to avoid token validation
        from unittest.mock import MagicMock

        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

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
            "install_from_github": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        cached_issue: IssueData = {
            "number": 500,
            "title": "Intervention Test",
            "state": "open",
            "labels": ["status-04:plan-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {500: cached_issue}
        }

        with caplog.at_level(logging.WARNING):
            result = restart_closed_sessions(cached_issues_by_repo=cached_issues)

        # Should skip - intervention flag doesn't bypass branch requirements
        assert len(result) == 0
        assert "No branch" in caplog.text
