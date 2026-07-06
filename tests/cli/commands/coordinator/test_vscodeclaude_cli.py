"""Test CLI layer for VSCode Claude - templates, CLI parsing, and command handlers."""

import argparse
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeConfig


class TestTemplates:
    """Test template strings."""

    def test_workspace_file_is_valid_json_template(self) -> None:
        """Workspace template produces valid JSON when formatted."""

        from mcp_coder.workflows.vscodeclaude.templates import (
            WORKSPACE_FILE_TEMPLATE,
        )

        formatted = WORKSPACE_FILE_TEMPLATE.format(
            folder_path="./test",
            issue_number=123,
            stage_short="review",
            title_short="Test title",
            repo_name="test-repo",
        )
        parsed = json.loads(formatted)
        assert "folders" in parsed
        assert "settings" in parsed
        assert parsed["folders"][0]["path"] == "./test"
        assert (
            "[#123 review] Test title - test-repo" in parsed["settings"]["window.title"]
        )

    def test_tasks_json_is_valid_json_template(self) -> None:
        """Tasks template produces valid JSON when formatted."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            TASKS_JSON_TEMPLATE,
        )

        formatted = TASKS_JSON_TEMPLATE.format(script_path="test.bat")
        parsed = json.loads(formatted)
        assert "tasks" in parsed
        assert len(parsed["tasks"]) == 2
        task = parsed["tasks"][0]
        assert task["label"] == "VSCodeClaude Startup"
        assert task["command"] == "test.bat"
        assert task["runOptions"]["runOn"] == "folderOpen"
        assert task["presentation"]["reveal"] == "always"

    def test_status_file_template_has_placeholders(self) -> None:
        """Status file template has required placeholders."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            STATUS_FILE_TEMPLATE,
        )

        assert "{issue_number}" in STATUS_FILE_TEMPLATE
        assert "{title}" in STATUS_FILE_TEMPLATE
        assert "{status_emoji}" in STATUS_FILE_TEMPLATE
        assert "{status_name}" in STATUS_FILE_TEMPLATE
        assert "{repo}" in STATUS_FILE_TEMPLATE
        assert "{branch}" in STATUS_FILE_TEMPLATE
        assert "{started_at}" in STATUS_FILE_TEMPLATE
        assert "{intervention_line}" in STATUS_FILE_TEMPLATE
        assert "{issue_url}" in STATUS_FILE_TEMPLATE

    def test_status_file_template_formatting(self) -> None:
        """Status file template formats correctly."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            STATUS_FILE_TEMPLATE,
        )

        formatted = STATUS_FILE_TEMPLATE.format(
            issue_number=123,
            title="Test Issue",
            status_emoji="U+1F504",
            status_name="in-progress",
            repo="owner/repo",
            branch="main",
            started_at="2024-01-01T00:00:00Z",
            intervention_line="",
            issue_url="https://github.com/owner/repo/issues/123",
        )

        assert "Issue #123" in formatted
        assert "Test Issue" in formatted
        assert "https://github.com/owner/repo/issues/123" in formatted

    def test_intervention_line_content(self) -> None:
        """Intervention line has correct content."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            INTERVENTION_LINE,
        )

        assert "INTERVENTION" in INTERVENTION_LINE

    def test_banner_template_has_placeholders(self) -> None:
        """Banner template has required placeholders."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            BANNER_TEMPLATE,
        )

        assert "{emoji}" in BANNER_TEMPLATE
        assert "{issue_number}" in BANNER_TEMPLATE
        assert "{title}" in BANNER_TEMPLATE
        assert "{repo}" in BANNER_TEMPLATE
        assert "{status}" in BANNER_TEMPLATE
        assert "{issue_url}" in BANNER_TEMPLATE

    def test_banner_template_formatting(self) -> None:
        """Banner template formats correctly."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            BANNER_TEMPLATE,
        )

        formatted = BANNER_TEMPLATE.format(
            emoji="\U0001f504",
            issue_number=123,
            title="Fix authentication bug in login handler",
            repo="owner/repo",
            status="status-07:code-review",
            issue_url="https://github.com/owner/repo/issues/123",
        )

        # Check that the banner contains the formatted content
        assert "Issue #123" in formatted
        assert "Fix authentication bug in login handler" in formatted
        assert "owner/repo" in formatted
        assert "status-07:code-review" in formatted
        assert "https://github.com/owner/repo/issues/123" in formatted
        # Check for separator characters
        assert "=" in formatted

    def test_gitignore_entry_has_session_files(self) -> None:
        """Gitignore entry includes all generated files."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            GITIGNORE_ENTRY,
        )

        assert ".vscodeclaude_status.txt" in GITIGNORE_ENTRY
        assert ".vscodeclaude_analysis.json" in GITIGNORE_ENTRY
        assert ".vscodeclaude_start.bat" in GITIGNORE_ENTRY
        assert ".vscodeclaude_start.sh" in GITIGNORE_ENTRY
        assert "# VSCodeClaude session files" in GITIGNORE_ENTRY


class TestCLI:
    """Test CLI argument parsing and routing."""

    def test_vscodeclaude_parser_exists(self) -> None:
        """vscodeclaude top-level command is registered."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(["vscodeclaude", "launch"])
        assert args.vscodeclaude_subcommand == "launch"

    def test_vscodeclaude_repo_argument(self) -> None:
        """--repo argument is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(["vscodeclaude", "launch", "--repo", "test"])
        assert args.repo == "test"

    def test_vscodeclaude_max_sessions_argument(self) -> None:
        """--max-sessions argument is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(["vscodeclaude", "launch", "--max-sessions", "5"])
        assert args.max_sessions == 5

    def test_vscodeclaude_cleanup_flag(self) -> None:
        """--cleanup flag is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(["vscodeclaude", "launch", "--cleanup"])
        assert args.cleanup is True

    def test_vscodeclaude_intervene_with_issue(self) -> None:
        """--intervene with --issue is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(
            ["vscodeclaude", "launch", "--intervene", "--issue", "123"]
        )
        assert args.intervene is True
        assert args.issue == 123

    def test_vscodeclaude_status_subcommand(self) -> None:
        """status subcommand is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(["vscodeclaude", "status"])
        assert args.vscodeclaude_subcommand == "status"

    def test_vscodeclaude_status_with_repo(self) -> None:
        """status --repo argument is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(["vscodeclaude", "status", "--repo", "myrepo"])
        assert args.vscodeclaude_subcommand == "status"
        assert args.repo == "myrepo"

    def test_vscodeclaude_launch_no_install_from_github_flag(self) -> None:
        """--no-install-from-github flag sets no_install_from_github to True."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(["vscodeclaude", "launch", "--no-install-from-github"])
        assert args.no_install_from_github is True

    def test_vscodeclaude_launch_default_no_install_from_github(self) -> None:
        """Default no_install_from_github is False when flag not provided."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(["vscodeclaude", "launch"])
        assert args.no_install_from_github is False

    def test_vscodeclaude_launch_no_install_from_github_with_repo(self) -> None:
        """--no-install-from-github works together with --repo."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(
            [
                "vscodeclaude",
                "launch",
                "--no-install-from-github",
                "--repo",
                "mcp_coder",
            ]
        )
        assert args.no_install_from_github is True
        assert args.repo == "mcp_coder"


class TestCommandHandlers:
    """Test command handler functions."""

    def test_execute_vscodeclaude_status_success(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Status command prints message when no sessions."""
        from mcp_coder.cli.commands.coordinator.commands_vscodeclaude import (
            execute_coordinator_vscodeclaude_status,
        )

        # Mock load_sessions to return empty
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_sessions",
            lambda: {"sessions": [], "last_updated": "2024-01-01T00:00:00Z"},
        )
        # Mock build_eligible_issues to return empty list (no eligible issues)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.build_eligible_issues_with_branch_check",
            lambda repo_names, cached_issues_by_repo=None: ([], set()),
        )

        # Mock load_config to return empty repos
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_config",
            lambda: {"coordinator": {"repos": {}}},
        )

        # Mock load_vscodeclaude_config for workspace_base
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_vscodeclaude_config",
            lambda: {"workspace_base": "/tmp/test", "max_sessions": 3},
        )

        # Mock build_eligible_issues_with_branch_check to return empty
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.build_eligible_issues_with_branch_check",
            lambda repo_names, cached_issues_by_repo=None: ([], set()),
        )

        args = argparse.Namespace(repo=None)

        result = execute_coordinator_vscodeclaude_status(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "No sessions or eligible issues found." in captured.out

    def test_execute_vscodeclaude_intervene_requires_issue(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Intervention mode requires --issue."""
        from mcp_coder.cli.commands.coordinator.commands_vscodeclaude import (
            execute_coordinator_vscodeclaude,
        )

        # Mock create_default_config to not create config
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.create_default_config",
            lambda: False,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_vscodeclaude_config",
            lambda: {"workspace_base": "/tmp", "max_sessions": 3},
        )

        args = argparse.Namespace(
            repo=None,
            max_sessions=None,
            cleanup=False,
            intervene=True,
            issue=None,  # Missing issue
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_vscodeclaude(args)

        assert result == 1
        assert "--issue" in caplog.text

    def test_execute_vscodeclaude_creates_config(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Creates config file on first run."""
        from mcp_coder.cli.commands.coordinator.commands_vscodeclaude import (
            execute_coordinator_vscodeclaude,
        )

        # Mock create_default_config to indicate config was created
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.create_default_config",
            lambda: True,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.get_config_file_path",
            lambda: Path("/fake/config.toml"),
        )

        args = argparse.Namespace(
            repo=None, max_sessions=None, cleanup=False, intervene=False, issue=None
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_vscodeclaude(args)

        assert result == 1  # Exit to let user configure
        assert "config" in caplog.text.lower()


def _assessment_stub(active: bool) -> SimpleNamespace:
    """Minimal assessment stand-in exposing the ``verdict.active`` the launch.

    path reads when projecting ``build_assessments`` output onto the legacy
    active_set shape.
    """
    return SimpleNamespace(verdict=SimpleNamespace(active=active))


class TestSkipGithubInstallWiring:
    """Tests for --no-install-from-github flag wiring through commands."""

    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.process_eligible_issues"
    )
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.restart_closed_sessions"
    )
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.cleanup_stale_sessions"
    )
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude._build_cached_issues_by_repo"
    )
    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_sessions")
    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_config")
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_vscodeclaude_config"
    )
    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_repo_config")
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.create_default_config"
    )
    def test_execute_coordinator_vscodeclaude_passes_skip_github_install(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_load_vsc_config: MagicMock,
        mock_load_config: MagicMock,
        mock_load_sessions: MagicMock,
        mock_build_cache: MagicMock,
        mock_cleanup: MagicMock,
        mock_restart: MagicMock,
        mock_process: MagicMock,
    ) -> None:
        """execute_coordinator_vscodeclaude passes skip_github_install to process_eligible_issues."""
        mock_create_config.return_value = False
        mock_load_vsc_config.return_value = {
            "workspace_base": "/tmp",
            "max_sessions": 3,
        }
        mock_load_config.return_value = {"coordinator": {"repos": {"mcp_coder": {}}}}
        mock_load_sessions.return_value = {"sessions": [], "last_updated": ""}
        mock_build_cache.return_value = (
            {"owner/mcp_coder": {1: MagicMock()}},
            set(),
        )
        mock_restart.return_value = []
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/owner/mcp_coder.git",
        }
        mock_process.return_value = []

        args = argparse.Namespace(
            repo=None,
            max_sessions=None,
            cleanup=False,
            intervene=False,
            issue=None,
            no_install_from_github=True,
        )

        from mcp_coder.cli.commands.coordinator.commands_vscodeclaude import (
            execute_coordinator_vscodeclaude,
        )

        execute_coordinator_vscodeclaude(args)

        mock_process.assert_called_once()
        call_kwargs = mock_process.call_args[1]
        assert call_kwargs["skip_github_install"] is True

    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.prepare_and_launch_session"
    )
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_repo_vscodeclaude_config"
    )
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.IssueBranchManager"
    )
    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_repo_config")
    def test_handle_intervention_mode_passes_skip_github_install(
        self,
        mock_load_repo: MagicMock,
        mock_issue_mgr_cls: MagicMock,
        mock_branch_mgr_cls: MagicMock,
        mock_load_repo_vsc: MagicMock,
        mock_prepare: MagicMock,
    ) -> None:
        """_handle_intervention_mode passes skip_github_install to prepare_and_launch_session."""
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/owner/repo.git",
        }
        mock_issue_mgr = MagicMock()
        mock_issue_mgr.get_issue.return_value = {
            "number": 42,
            "title": "Test",
            "labels": [],
            "state": "open",
            "url": "",
        }
        mock_issue_mgr_cls.return_value = mock_issue_mgr

        mock_branch_mgr = MagicMock()
        mock_branch_mgr.get_branch_with_pr_fallback.return_value = "feature-branch"
        mock_branch_mgr_cls.return_value = mock_branch_mgr

        mock_load_repo_vsc.return_value = {}
        mock_prepare.return_value = {
            "issue_number": 42,
            "repo": "owner/repo",
            "folder": "/tmp/test",
            "status": "open",
            "vscode_pid": 1234,
            "is_intervention": True,
            "started_at": "2024-01-01",
        }

        args = argparse.Namespace(
            repo="mcp_coder",
            issue=42,
            intervene=True,
            no_install_from_github=True,
        )
        vscodeclaude_config: VSCodeClaudeConfig = {
            "workspace_base": "/tmp",
            "max_sessions": 3,
        }

        from mcp_coder.cli.commands.coordinator.commands_vscodeclaude import (
            _handle_intervention_mode,
        )

        _handle_intervention_mode(args, vscodeclaude_config)

        mock_prepare.assert_called_once()
        call_kwargs = mock_prepare.call_args[1]
        assert call_kwargs["skip_github_install"] is True


class TestAtCapacityDiagnosticLog:
    """Tests for the at-capacity diagnostic log line in execute_coordinator_vscodeclaude."""

    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.apply_assessments")
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.process_eligible_issues"
    )
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.restart_closed_sessions"
    )
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.cleanup_stale_sessions"
    )
    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.build_assessments")
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude._build_cached_issues_by_repo"
    )
    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_sessions")
    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_config")
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_vscodeclaude_config"
    )
    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_repo_config")
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.create_default_config"
    )
    def test_at_capacity_log_includes_folder_basenames(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_load_vsc_config: MagicMock,
        mock_load_config: MagicMock,
        mock_load_sessions: MagicMock,
        mock_build_cache: MagicMock,
        mock_build_assess: MagicMock,
        mock_cleanup: MagicMock,
        mock_restart: MagicMock,
        mock_process: MagicMock,
        mock_apply: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """At capacity, the tail log line names the folders consuming the slots."""
        mock_create_config.return_value = False
        mock_load_vsc_config.return_value = {
            "workspace_base": "/tmp",
            "max_sessions": 2,
        }
        mock_load_config.return_value = {"coordinator": {"repos": {"mcp_coder": {}}}}
        mock_load_sessions.return_value = {"sessions": [], "last_updated": ""}
        mock_build_cache.return_value = (
            {"owner/mcp_coder": {1: MagicMock()}},
            set(),
        )
        # Two active folders => at capacity for max_sessions=2.
        mock_build_assess.return_value = {
            "/tmp/repo_111": _assessment_stub(active=True),
            "/tmp/repo_222": _assessment_stub(active=True),
        }
        mock_restart.return_value = []
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/owner/mcp_coder.git",
        }
        mock_process.return_value = []  # No new sessions started

        args = argparse.Namespace(
            repo=None,
            max_sessions=None,
            cleanup=False,
            intervene=False,
            issue=None,
            no_install_from_github=False,
        )

        from mcp_coder.cli.commands.coordinator.commands_vscodeclaude import (
            execute_coordinator_vscodeclaude,
        )

        with caplog.at_level(logging.INFO):
            execute_coordinator_vscodeclaude(args)

        assert "at capacity (2/2)" in caplog.text
        assert "repo_111" in caplog.text
        assert "repo_222" in caplog.text

    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.apply_assessments")
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.process_eligible_issues"
    )
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.restart_closed_sessions"
    )
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.cleanup_stale_sessions"
    )
    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.build_assessments")
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude._build_cached_issues_by_repo"
    )
    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_sessions")
    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_config")
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_vscodeclaude_config"
    )
    @patch("mcp_coder.cli.commands.coordinator.commands_vscodeclaude.load_repo_config")
    @patch(
        "mcp_coder.cli.commands.coordinator.commands_vscodeclaude.create_default_config"
    )
    def test_below_capacity_message_unchanged(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_load_vsc_config: MagicMock,
        mock_load_config: MagicMock,
        mock_load_sessions: MagicMock,
        mock_build_cache: MagicMock,
        mock_build_assess: MagicMock,
        mock_cleanup: MagicMock,
        mock_restart: MagicMock,
        mock_process: MagicMock,
        mock_apply: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Below capacity with no started sessions preserves the legacy tail format."""
        mock_create_config.return_value = False
        mock_load_vsc_config.return_value = {
            "workspace_base": "/tmp",
            "max_sessions": 3,
        }
        mock_load_config.return_value = {"coordinator": {"repos": {"mcp_coder": {}}}}
        mock_load_sessions.return_value = {"sessions": [], "last_updated": ""}
        mock_build_cache.return_value = (
            {"owner/mcp_coder": {1: MagicMock()}},
            set(),
        )
        mock_build_assess.return_value = {}  # No active sessions
        mock_restart.return_value = []
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/owner/mcp_coder.git",
        }
        mock_process.return_value = []

        args = argparse.Namespace(
            repo=None,
            max_sessions=None,
            cleanup=False,
            intervene=False,
            issue=None,
            no_install_from_github=False,
        )

        from mcp_coder.cli.commands.coordinator.commands_vscodeclaude import (
            execute_coordinator_vscodeclaude,
        )

        with caplog.at_level(logging.INFO):
            execute_coordinator_vscodeclaude(args)

        assert "No new sessions started (active: 0/3)" in caplog.text
        assert "at capacity" not in caplog.text

    def test_process_eligible_issues_at_capacity_log_is_debug(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The per-repo 'Already at max sessions' log is emitted at DEBUG, not INFO."""
        from mcp_coder.workflows.vscodeclaude.session_launch import (
            process_eligible_issues,
        )

        with caplog.at_level(logging.INFO):
            result = process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 2},
                max_sessions=2,
                current_count=2,
            )

        assert result == []
        # At INFO level, the message must NOT appear (downgraded to DEBUG).
        assert "Already at max sessions" not in caplog.text

        # At DEBUG level, the message should still be present.
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 2},
                max_sessions=2,
                current_count=2,
            )

        assert "Already at max sessions" in caplog.text
