"""Test CLI layer for VSCode Claude - templates, CLI parsing, and command handlers."""

import argparse
import json
from pathlib import Path

import pytest


class TestTemplates:
    """Test template strings."""

    def test_startup_script_linux_has_placeholders(self) -> None:
        """Linux script has required placeholders."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            STARTUP_SCRIPT_LINUX,
        )

        assert "{emoji}" in STARTUP_SCRIPT_LINUX
        assert "{issue_number}" in STARTUP_SCRIPT_LINUX
        assert "{title}" in STARTUP_SCRIPT_LINUX
        assert "{repo}" in STARTUP_SCRIPT_LINUX
        assert "{status}" in STARTUP_SCRIPT_LINUX
        assert "{issue_url}" in STARTUP_SCRIPT_LINUX
        assert "{automated_section}" in STARTUP_SCRIPT_LINUX
        assert "{interactive_section}" in STARTUP_SCRIPT_LINUX

    def test_automated_section_linux_has_placeholders(self) -> None:
        """Linux automated section has required placeholders."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            AUTOMATED_SECTION_LINUX,
        )

        assert "{initial_command}" in AUTOMATED_SECTION_LINUX
        assert "claude -p" in AUTOMATED_SECTION_LINUX
        assert ".vscodeclaude_analysis.json" in AUTOMATED_SECTION_LINUX

    def test_interactive_section_linux_has_placeholders(self) -> None:
        """Linux interactive section has required placeholders."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            INTERACTIVE_SECTION_LINUX,
        )

        assert "{followup_command}" in INTERACTIVE_SECTION_LINUX
        assert "claude --resume" in INTERACTIVE_SECTION_LINUX

    def test_intervention_section_linux_content(self) -> None:
        """Linux intervention section has intervention warning."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            INTERVENTION_SECTION_LINUX,
        )

        assert "INTERVENTION MODE" in INTERVENTION_SECTION_LINUX
        assert "No automated analysis will run" in INTERVENTION_SECTION_LINUX
        assert "claude" in INTERVENTION_SECTION_LINUX

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


class TestWindowsTemplates:
    """Test Windows template strings with venv and mcp-coder."""

    def test_venv_section_creates_venv_if_missing(self) -> None:
        """VENV_SECTION_WINDOWS creates venv when not present."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            VENV_SECTION_WINDOWS,
        )

        assert "if not exist .venv" in VENV_SECTION_WINDOWS
        assert "uv venv" in VENV_SECTION_WINDOWS
        assert "uv sync" in VENV_SECTION_WINDOWS

    def test_venv_section_activates_existing_venv(self) -> None:
        """VENV_SECTION_WINDOWS activates existing venv."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            VENV_SECTION_WINDOWS,
        )

        assert "call .venv\\Scripts\\activate.bat" in VENV_SECTION_WINDOWS

    def test_automated_section_uses_mcp_coder_prompt(self) -> None:
        """AUTOMATED_SECTION_WINDOWS uses mcp-coder prompt."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            AUTOMATED_SECTION_WINDOWS,
        )

        assert "mcp-coder prompt" in AUTOMATED_SECTION_WINDOWS
        assert "--output-format session-id" in AUTOMATED_SECTION_WINDOWS
        assert "--mcp-config .mcp.json" in AUTOMATED_SECTION_WINDOWS

    def test_automated_section_captures_session_id(self) -> None:
        """AUTOMATED_SECTION_WINDOWS captures SESSION_ID."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            AUTOMATED_SECTION_WINDOWS,
        )

        assert "set SESSION_ID=" in AUTOMATED_SECTION_WINDOWS
        assert 'if "%SESSION_ID%"==""' in AUTOMATED_SECTION_WINDOWS

    def test_discussion_section_uses_session_id(self) -> None:
        """DISCUSSION_SECTION_WINDOWS passes session-id."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            DISCUSSION_SECTION_WINDOWS,
        )

        assert "mcp-coder prompt" in DISCUSSION_SECTION_WINDOWS
        assert "--session-id %SESSION_ID%" in DISCUSSION_SECTION_WINDOWS

    def test_interactive_section_uses_claude_resume(self) -> None:
        """INTERACTIVE_SECTION_WINDOWS uses claude --resume."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            INTERACTIVE_SECTION_WINDOWS,
        )

        assert "claude --resume %SESSION_ID%" in INTERACTIVE_SECTION_WINDOWS

    def test_startup_script_has_all_sections(self) -> None:
        """STARTUP_SCRIPT_WINDOWS includes all section placeholders."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            STARTUP_SCRIPT_WINDOWS,
        )

        assert "{venv_section}" in STARTUP_SCRIPT_WINDOWS
        assert "{automated_section}" in STARTUP_SCRIPT_WINDOWS
        assert "{discussion_section}" in STARTUP_SCRIPT_WINDOWS
        assert "{interactive_section}" in STARTUP_SCRIPT_WINDOWS

    def test_intervention_script_has_warning(self) -> None:
        """INTERVENTION_SCRIPT_WINDOWS shows intervention warning."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            INTERVENTION_SCRIPT_WINDOWS,
        )

        assert "INTERVENTION MODE" in INTERVENTION_SCRIPT_WINDOWS
        assert "{venv_section}" in INTERVENTION_SCRIPT_WINDOWS
        assert "claude" in INTERVENTION_SCRIPT_WINDOWS

    def test_templates_include_timeout_placeholder(self) -> None:
        """Templates include {timeout} placeholder."""
        from mcp_coder.workflows.vscodeclaude.templates import (
            AUTOMATED_SECTION_WINDOWS,
            DISCUSSION_SECTION_WINDOWS,
        )

        assert "{timeout}" in AUTOMATED_SECTION_WINDOWS
        assert "{timeout}" in DISCUSSION_SECTION_WINDOWS


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
        """Status command prints message when no sessions."""
        from mcp_coder.cli.commands.coordinator.commands import (
            execute_coordinator_vscodeclaude_status,
        )

        # Mock load_sessions to return empty
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.load_sessions",
            lambda: {"sessions": [], "last_updated": "2024-01-01T00:00:00Z"},
        )
        # Mock build_eligible_issues to return empty list (no eligible issues)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.build_eligible_issues_with_branch_check",
            lambda repo_names: ([], set()),
        )

        # Mock load_config to return empty repos
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.load_config",
            lambda: {"coordinator": {"repos": {}}},
        )

        # Mock build_eligible_issues_with_branch_check to return empty
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.issues.build_eligible_issues_with_branch_check",
            lambda repo_names: ([], set()),
        )

        args = argparse.Namespace(repo=None)

        result = execute_coordinator_vscodeclaude_status(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "No sessions or eligible issues found." in captured.out

    def test_execute_vscodeclaude_intervene_requires_issue(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Intervention mode requires --issue."""
        from mcp_coder.cli.commands.coordinator.commands import (
            execute_coordinator_vscodeclaude,
        )

        # Mock create_default_config to not create config
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.create_default_config",
            lambda: False,
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

        # Mock create_default_config to indicate config was created
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.create_default_config",
            lambda: True,
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
