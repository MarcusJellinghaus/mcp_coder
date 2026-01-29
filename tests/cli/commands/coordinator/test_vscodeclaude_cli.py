"""Test CLI layer for VSCode Claude - templates, CLI parsing, and command handlers."""

import argparse
import json
from pathlib import Path

import pytest


class TestTemplates:
    """Test template strings."""

    def test_startup_script_windows_has_placeholders(self) -> None:
        """Windows script has required placeholders."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            STARTUP_SCRIPT_WINDOWS,
        )

        assert "{emoji}" in STARTUP_SCRIPT_WINDOWS
        assert "{issue_number:" in STARTUP_SCRIPT_WINDOWS
        assert "{automated_section}" in STARTUP_SCRIPT_WINDOWS
        assert "{stage_name:" in STARTUP_SCRIPT_WINDOWS
        assert "{title:" in STARTUP_SCRIPT_WINDOWS
        assert "{repo}" in STARTUP_SCRIPT_WINDOWS
        assert "{status:" in STARTUP_SCRIPT_WINDOWS
        assert "{interactive_section}" in STARTUP_SCRIPT_WINDOWS

    def test_startup_script_linux_has_placeholders(self) -> None:
        """Linux script has required placeholders."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            STARTUP_SCRIPT_LINUX,
        )

        assert "{emoji}" in STARTUP_SCRIPT_LINUX
        assert "{issue_number:" in STARTUP_SCRIPT_LINUX
        assert "{stage_name:" in STARTUP_SCRIPT_LINUX
        assert "{title:" in STARTUP_SCRIPT_LINUX
        assert "{repo}" in STARTUP_SCRIPT_LINUX
        assert "{status:" in STARTUP_SCRIPT_LINUX
        assert "{automated_section}" in STARTUP_SCRIPT_LINUX
        assert "{interactive_section}" in STARTUP_SCRIPT_LINUX

    def test_automated_section_windows_has_placeholders(self) -> None:
        """Windows automated section has required placeholders."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            AUTOMATED_SECTION_WINDOWS,
        )

        assert "{initial_command}" in AUTOMATED_SECTION_WINDOWS
        assert "claude -p" in AUTOMATED_SECTION_WINDOWS
        assert ".vscodeclaude_analysis.json" in AUTOMATED_SECTION_WINDOWS

    def test_automated_section_linux_has_placeholders(self) -> None:
        """Linux automated section has required placeholders."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            AUTOMATED_SECTION_LINUX,
        )

        assert "{initial_command}" in AUTOMATED_SECTION_LINUX
        assert "claude -p" in AUTOMATED_SECTION_LINUX
        assert ".vscodeclaude_analysis.json" in AUTOMATED_SECTION_LINUX

    def test_interactive_section_windows_has_placeholders(self) -> None:
        """Windows interactive section has required placeholders."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            INTERACTIVE_SECTION_WINDOWS,
        )

        assert "{followup_command}" in INTERACTIVE_SECTION_WINDOWS
        assert "claude --resume" in INTERACTIVE_SECTION_WINDOWS

    def test_interactive_section_linux_has_placeholders(self) -> None:
        """Linux interactive section has required placeholders."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            INTERACTIVE_SECTION_LINUX,
        )

        assert "{followup_command}" in INTERACTIVE_SECTION_LINUX
        assert "claude --resume" in INTERACTIVE_SECTION_LINUX

    def test_intervention_section_windows_content(self) -> None:
        """Windows intervention section has intervention warning."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            INTERVENTION_SECTION_WINDOWS,
        )

        assert "INTERVENTION MODE" in INTERVENTION_SECTION_WINDOWS
        assert "No automated analysis will run" in INTERVENTION_SECTION_WINDOWS
        assert "claude" in INTERVENTION_SECTION_WINDOWS

    def test_intervention_section_linux_content(self) -> None:
        """Linux intervention section has intervention warning."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            INTERVENTION_SECTION_LINUX,
        )

        assert "INTERVENTION MODE" in INTERVENTION_SECTION_LINUX
        assert "No automated analysis will run" in INTERVENTION_SECTION_LINUX
        assert "claude" in INTERVENTION_SECTION_LINUX

    def test_workspace_file_is_valid_json_template(self) -> None:
        """Workspace template produces valid JSON when formatted."""

        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
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
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            TASKS_JSON_TEMPLATE,
        )

        formatted = TASKS_JSON_TEMPLATE.format(script_path="test.bat")
        parsed = json.loads(formatted)
        assert "tasks" in parsed
        assert len(parsed["tasks"]) == 1
        task = parsed["tasks"][0]
        assert task["label"] == "VSCodeClaude Startup"
        assert task["command"] == "test.bat"
        assert task["runOptions"]["runOn"] == "folderOpen"
        assert task["presentation"]["reveal"] == "always"

    def test_status_file_template_has_placeholders(self) -> None:
        """Status file template has required placeholders."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            STATUS_FILE_TEMPLATE,
        )

        assert "{issue_number}" in STATUS_FILE_TEMPLATE
        assert "{title}" in STATUS_FILE_TEMPLATE
        assert "{status_emoji}" in STATUS_FILE_TEMPLATE
        assert "{status_name}" in STATUS_FILE_TEMPLATE
        assert "{repo}" in STATUS_FILE_TEMPLATE
        assert "{branch}" in STATUS_FILE_TEMPLATE
        assert "{started_at}" in STATUS_FILE_TEMPLATE
        assert "{intervention_row}" in STATUS_FILE_TEMPLATE
        assert "{issue_url}" in STATUS_FILE_TEMPLATE

    def test_status_file_template_formatting(self) -> None:
        """Status file template formats correctly."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
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
            intervention_row="",
            issue_url="https://github.com/owner/repo/issues/123",
        )

        assert "# VSCodeClaude Session" in formatted
        assert "| **Issue** | #123 |" in formatted
        assert "| **Title** | Test Issue |" in formatted
        assert (
            "[View Issue on GitHub](https://github.com/owner/repo/issues/123)"
            in formatted
        )

    def test_intervention_row_content(self) -> None:
        """Intervention row has correct content."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            INTERVENTION_ROW,
        )

        assert "INTERVENTION" in INTERVENTION_ROW

    def test_banner_template_has_placeholders(self) -> None:
        """Banner template has required placeholders."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            BANNER_TEMPLATE,
        )

        assert "{emoji}" in BANNER_TEMPLATE
        assert "{stage_name:" in BANNER_TEMPLATE
        assert "{issue_number:" in BANNER_TEMPLATE
        assert "{title:" in BANNER_TEMPLATE
        assert "{repo}" in BANNER_TEMPLATE
        assert "{status:" in BANNER_TEMPLATE

    def test_banner_template_formatting(self) -> None:
        """Banner template formats correctly with padding."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            BANNER_TEMPLATE,
        )

        formatted = BANNER_TEMPLATE.format(
            emoji="U+1F504",
            stage_name="Code Review",
            issue_number=123,
            title="Fix authentication bug in login handler",
            repo="owner/repo",
            status="status-07:code-review",
        )

        # Check that the banner contains the formatted content
        assert "Code Review" in formatted
        assert "#   123" in formatted  # issue_number:6 right-aligns to 6 chars
        assert "Fix authentication bug in login handler" in formatted
        assert "owner/repo" in formatted
        assert "status-07:code-review" in formatted
        # Check for box drawing characters
        assert "+" in formatted or "=" in formatted

    def test_gitignore_entry_has_session_files(self) -> None:
        """Gitignore entry includes all generated files."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            GITIGNORE_ENTRY,
        )

        assert ".vscodeclaude_status.md" in GITIGNORE_ENTRY
        assert ".vscodeclaude_analysis.json" in GITIGNORE_ENTRY
        assert ".vscodeclaude_start.bat" in GITIGNORE_ENTRY
        assert ".vscodeclaude_start.sh" in GITIGNORE_ENTRY
        assert "# VSCodeClaude session files" in GITIGNORE_ENTRY


class TestCLI:
    """Test CLI argument parsing and routing."""

    def test_vscodeclaude_parser_exists(self) -> None:
        """vscodeclaude subcommand is registered."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        # Parse valid command
        args = parser.parse_args(["coordinator", "vscodeclaude"])
        assert args.coordinator_subcommand == "vscodeclaude"

    def test_vscodeclaude_repo_argument(self) -> None:
        """--repo argument is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(["coordinator", "vscodeclaude", "--repo", "test"])
        assert args.repo == "test"

    def test_vscodeclaude_max_sessions_argument(self) -> None:
        """--max-sessions argument is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(["coordinator", "vscodeclaude", "--max-sessions", "5"])
        assert args.max_sessions == 5

    def test_vscodeclaude_cleanup_flag(self) -> None:
        """--cleanup flag is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(["coordinator", "vscodeclaude", "--cleanup"])
        assert args.cleanup is True

    def test_vscodeclaude_intervene_with_issue(self) -> None:
        """--intervene with --issue is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(
            ["coordinator", "vscodeclaude", "--intervene", "--issue", "123"]
        )
        assert args.intervene is True
        assert args.issue == 123

    def test_vscodeclaude_status_subcommand(self) -> None:
        """status subcommand is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(["coordinator", "vscodeclaude", "status"])
        assert args.vscodeclaude_subcommand == "status"

    def test_vscodeclaude_status_with_repo(self) -> None:
        """status --repo argument is parsed."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        args = parser.parse_args(
            ["coordinator", "vscodeclaude", "status", "--repo", "myrepo"]
        )
        assert args.vscodeclaude_subcommand == "status"
        assert args.repo == "myrepo"


class TestCommandHandlers:
    """Test command handler functions."""

    def test_execute_vscodeclaude_status_success(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Status command prints table."""
        from mcp_coder.cli.commands.coordinator.commands import (
            execute_coordinator_vscodeclaude_status,
        )

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.load_sessions",
            lambda: {"sessions": [], "last_updated": "2024-01-01T00:00:00Z"},
        )

        args = argparse.Namespace(repo=None)

        result = execute_coordinator_vscodeclaude_status(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "VSCODECLAUDE SESSIONS" in captured.out

    def test_execute_vscodeclaude_intervene_requires_issue(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Intervention mode requires --issue."""
        from mcp_coder.cli.commands.coordinator.commands import (
            execute_coordinator_vscodeclaude,
        )

        # Mock _get_coordinator to return a mock that doesn't create config
        mock_coordinator = type(
            "MockCoordinator", (), {"create_default_config": lambda self: False}
        )()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands._get_coordinator",
            lambda: mock_coordinator,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.load_vscodeclaude_config",
            lambda: {"workspace_base": "/tmp", "max_sessions": 3},
        )

        args = argparse.Namespace(
            repo=None,
            max_sessions=None,
            cleanup=False,
            intervene=True,
            issue=None,  # Missing issue
        )

        result = execute_coordinator_vscodeclaude(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "--issue" in captured.err

    def test_execute_vscodeclaude_creates_config(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Creates config file on first run."""
        from mcp_coder.cli.commands.coordinator.commands import (
            execute_coordinator_vscodeclaude,
        )

        mock_coordinator = type(
            "MockCoordinator", (), {"create_default_config": lambda self: True}
        )()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands._get_coordinator",
            lambda: mock_coordinator,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.get_config_file_path",
            lambda: Path("/fake/config.toml"),
        )

        args = argparse.Namespace(
            repo=None, max_sessions=None, cleanup=False, intervene=False, issue=None
        )

        result = execute_coordinator_vscodeclaude(args)

        assert result == 1  # Exit to let user configure
        captured = capsys.readouterr()
        assert "config" in captured.out.lower()
