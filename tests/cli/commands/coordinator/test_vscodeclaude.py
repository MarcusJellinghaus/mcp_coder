"""Test type definitions and constants for VSCode Claude session management."""

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mcp_coder.cli.commands.coordinator.vscodeclaude import (
    DEFAULT_MAX_SESSIONS,
    HUMAN_ACTION_COMMANDS,
    STAGE_DISPLAY_NAMES,
    STATUS_EMOJI,
    VSCODECLAUDE_PRIORITY,
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
    VSCodeClaudeSession,
    VSCodeClaudeSessionStore,
    add_session,
    check_vscode_running,
    create_startup_script,
    create_status_file,
    create_vscode_task,
    create_working_folder,
    create_workspace_file,
    get_active_session_count,
    get_eligible_vscodeclaude_issues,
    get_human_action_labels,
    get_linked_branch_for_issue,
    get_session_for_issue,
    get_sessions_file_path,
    get_stage_display_name,
    get_working_folder_path,
    handle_pr_created_issues,
    launch_vscode,
    load_repo_vscodeclaude_config,
    load_sessions,
    load_vscodeclaude_config,
    prepare_and_launch_session,
    process_eligible_issues,
    remove_session,
    restart_closed_sessions,
    run_setup_commands,
    sanitize_folder_name,
    save_sessions,
    setup_git_repo,
    truncate_title,
    update_gitignore,
    update_session_pid,
    validate_mcp_json,
    validate_setup_commands,
)
from mcp_coder.utils.github_operations.issue_manager import IssueData


class TestTypes:
    """Test type definitions and constants."""

    def test_vscodeclaude_priority_order(self) -> None:
        """Priority list has correct order (later stages first)."""
        assert VSCODECLAUDE_PRIORITY[0] == "status-10:pr-created"
        assert VSCODECLAUDE_PRIORITY[-1] == "status-01:created"

    def test_human_action_commands_coverage(self) -> None:
        """All priority statuses have command mappings."""
        for status in VSCODECLAUDE_PRIORITY:
            assert status in HUMAN_ACTION_COMMANDS

    def test_status_emoji_coverage(self) -> None:
        """All priority statuses have emoji mappings."""
        for status in VSCODECLAUDE_PRIORITY:
            assert status in STATUS_EMOJI

    def test_default_max_sessions(self) -> None:
        """Default max sessions is 3."""
        assert DEFAULT_MAX_SESSIONS == 3

    def test_vscodeclaude_priority_completeness(self) -> None:
        """All expected statuses are in the priority list."""
        expected_statuses = {
            "status-01:created",
            "status-04:plan-review",
            "status-07:code-review",
            "status-10:pr-created",
        }
        assert set(VSCODECLAUDE_PRIORITY) == expected_statuses

    def test_human_action_commands_structure(self) -> None:
        """Human action commands have correct structure."""
        for status, commands in HUMAN_ACTION_COMMANDS.items():
            assert isinstance(commands, tuple)
            assert len(commands) == 2
            # Commands are either strings or None
            assert all(cmd is None or isinstance(cmd, str) for cmd in commands)
            # If command is a string, it should start with "/"
            for cmd in commands:
                if cmd is not None:
                    assert cmd.startswith("/"), f"Command {cmd} should start with '/'"

    def test_status_emoji_structure(self) -> None:
        """Status emoji mappings have correct structure."""
        for status, emoji in STATUS_EMOJI.items():
            assert isinstance(emoji, str)
            assert len(emoji) == 1 or len(emoji) == 2  # Handle unicode emojis


class TestTypeHints:
    """Test TypedDict structure validation."""

    def test_vscodeclaude_session_type_structure(self) -> None:
        """VSCodeClaudeSession has all required fields."""
        # This is a compile-time check, but we can verify the annotations exist
        annotations = VSCodeClaudeSession.__annotations__
        expected_fields = {
            "folder",
            "repo",
            "issue_number",
            "status",
            "vscode_pid",
            "started_at",
            "is_intervention",
        }
        assert set(annotations.keys()) == expected_fields

    def test_vscodeclaude_session_store_type_structure(self) -> None:
        """VSCodeClaudeSessionStore has all required fields."""
        annotations = VSCodeClaudeSessionStore.__annotations__
        expected_fields = {"sessions", "last_updated"}
        assert set(annotations.keys()) == expected_fields

    def test_vscodeclaude_config_type_structure(self) -> None:
        """VSCodeClaudeConfig has all required fields."""
        annotations = VSCodeClaudeConfig.__annotations__
        expected_fields = {"workspace_base", "max_sessions"}
        assert set(annotations.keys()) == expected_fields

    def test_repo_vscodeclaude_config_type_structure(self) -> None:
        """RepoVSCodeClaudeConfig has all expected fields."""
        annotations = RepoVSCodeClaudeConfig.__annotations__
        expected_fields = {"setup_commands_windows", "setup_commands_linux"}
        assert set(annotations.keys()) == expected_fields

    def test_vscodeclaude_session_creation(self) -> None:
        """Can create a valid VSCodeClaudeSession instance."""
        session: VSCodeClaudeSession = {
            "folder": "/path/to/folder",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-01:created",
            "vscode_pid": 1234,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        # Verify all fields are present and correct types
        assert isinstance(session["folder"], str)
        assert isinstance(session["repo"], str)
        assert isinstance(session["issue_number"], int)
        assert isinstance(session["status"], str)
        assert session["vscode_pid"] is None or isinstance(session["vscode_pid"], int)
        assert isinstance(session["started_at"], str)
        assert isinstance(session["is_intervention"], bool)

    def test_vscodeclaude_session_store_creation(self) -> None:
        """Can create a valid VSCodeClaudeSessionStore instance."""
        store: VSCodeClaudeSessionStore = {
            "sessions": [],
            "last_updated": "2024-01-01T00:00:00Z",
        }

        assert isinstance(store["sessions"], list)
        assert isinstance(store["last_updated"], str)

    def test_vscodeclaude_config_creation(self) -> None:
        """Can create a valid VSCodeClaudeConfig instance."""
        config: VSCodeClaudeConfig = {
            "workspace_base": "/path/to/workspace",
            "max_sessions": 5,
        }

        assert isinstance(config["workspace_base"], str)
        assert isinstance(config["max_sessions"], int)

    def test_repo_vscodeclaude_config_creation(self) -> None:
        """Can create a valid RepoVSCodeClaudeConfig instance."""
        config: RepoVSCodeClaudeConfig = {
            "setup_commands_windows": ["cmd1", "cmd2"],
            "setup_commands_linux": ["cmd3", "cmd4"],
        }

        assert isinstance(config["setup_commands_windows"], list)
        assert isinstance(config["setup_commands_linux"], list)
        assert all(isinstance(cmd, str) for cmd in config["setup_commands_windows"])
        assert all(isinstance(cmd, str) for cmd in config["setup_commands_linux"])

    def test_repo_vscodeclaude_config_partial(self) -> None:
        """Can create a partial RepoVSCodeClaudeConfig instance (total=False)."""
        # Should be able to create with only some fields since total=False
        config: RepoVSCodeClaudeConfig = {"setup_commands_windows": ["cmd1"]}

        assert "setup_commands_windows" in config
        assert "setup_commands_linux" not in config


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
        import json

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
            status_emoji="🔄",
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
        assert "⚠️" in INTERVENTION_ROW

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
            emoji="🔄",
            stage_name="Code Review",
            issue_number=123,
            title="Fix authentication bug in login handler",
            repo="owner/repo",
            status="status-07:code-review",
        )

        # Check that the banner contains the formatted content
        assert "🔄 Code Review" in formatted
        assert "#   123" in formatted  # issue_number:6 right-aligns to 6 chars
        assert "Fix authentication bug in login handler" in formatted
        assert "owner/repo" in formatted
        assert "status-07:code-review" in formatted
        # Check for box drawing characters
        assert "╔" in formatted
        assert "╗" in formatted
        assert "╚" in formatted
        assert "╝" in formatted

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


class TestIntegration:
    """Integration tests for end-to-end workflow."""

    def test_complete_session_workflow(
        self, tmp_path: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test complete session creation and launch workflow."""
        # This is a placeholder for future integration tests
        # Will test the full flow from config loading to VSCode launch
        pass

    def test_session_cleanup_workflow(
        self, tmp_path: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test session stale detection and cleanup workflow."""
        # This is a placeholder for future integration tests
        # Will test stale session detection and cleanup
        pass


class TestSessionManagement:
    """Test session load/save/check functions."""

    def test_get_sessions_file_path_windows(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sessions file is in .mcp_coder on Windows."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.platform.system",
            lambda: "Windows",
        )
        path = get_sessions_file_path()
        assert ".mcp_coder" in str(path)
        assert "vscodeclaude_sessions.json" in str(path)

    def test_get_sessions_file_path_linux(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sessions file is in .config/mcp_coder on Linux."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.platform.system",
            lambda: "Linux",
        )
        path = get_sessions_file_path()
        # Check for either forward or back slashes
        path_str = str(path)
        assert ".config" in path_str
        assert "mcp_coder" in path_str

    def test_load_sessions_empty_when_no_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns empty store when file doesn't exist."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: tmp_path / "nonexistent.json",
        )
        store = load_sessions()
        assert store["sessions"] == []

    def test_save_and_load_roundtrip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sessions survive save/load cycle."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )

        session: VSCodeClaudeSession = {
            "folder": str(tmp_path / "test_123"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }

        store: VSCodeClaudeSessionStore = {
            "sessions": [session],
            "last_updated": "2024-01-22T10:30:00Z",
        }

        save_sessions(store)
        loaded = load_sessions()

        assert len(loaded["sessions"]) == 1
        assert loaded["sessions"][0]["issue_number"] == 123

    def test_check_vscode_running_none_pid(self) -> None:
        """None PID returns False."""
        assert check_vscode_running(None) is False

    def test_check_vscode_running_nonexistent_pid(self) -> None:
        """Nonexistent PID returns False."""
        # Use a PID that almost certainly doesn't exist
        assert check_vscode_running(999999999) is False

    def test_get_session_for_issue_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Finds session by repo and issue number."""
        # Setup session store with test data
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )

        session = {
            "folder": "/test/folder",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        found = get_session_for_issue("owner/repo", 123)
        assert found is not None
        assert found["issue_number"] == 123

    def test_get_session_for_issue_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns None when no matching session."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )
        store = {"sessions": [], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        found = get_session_for_issue("owner/repo", 999)
        assert found is None

    def test_add_session(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Adds session to store."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )

        session: VSCodeClaudeSession = {
            "folder": "/test/folder",
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-04:plan-review",
            "vscode_pid": 5678,
            "started_at": "2024-01-22T11:00:00Z",
            "is_intervention": False,
        }

        add_session(session)

        loaded = load_sessions()
        assert len(loaded["sessions"]) == 1
        assert loaded["sessions"][0]["issue_number"] == 456

    def test_remove_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Removes session by folder path."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )

        session = {
            "folder": "/test/folder",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        result = remove_session("/test/folder")
        assert result is True

        loaded = load_sessions()
        assert len(loaded["sessions"]) == 0

    def test_remove_session_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Remove returns False when session not found."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )
        store = {"sessions": [], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        result = remove_session("/nonexistent/folder")
        assert result is False

    def test_get_active_session_count_with_mocked_pid_check(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Counts only sessions with running PIDs."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock check_vscode_running to return True for specific PID
        def mock_check(pid: int | None) -> bool:
            return pid == 1111

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.check_vscode_running",
            mock_check,
        )

        sessions = [
            {
                "folder": "/a",
                "repo": "o/r",
                "issue_number": 1,
                "status": "s",
                "vscode_pid": 1111,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            },
            {
                "folder": "/b",
                "repo": "o/r",
                "issue_number": 2,
                "status": "s",
                "vscode_pid": 2222,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            },
        ]
        store = {"sessions": sessions, "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        count = get_active_session_count()
        assert count == 1  # Only PID 1111 is "running"

    def test_update_session_pid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Updates VSCode PID for existing session."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )

        session = {
            "folder": "/test/folder",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        update_session_pid("/test/folder", 9999)

        loaded = load_sessions()
        assert loaded["sessions"][0]["vscode_pid"] == 9999

    def test_load_sessions_with_invalid_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns empty store when JSON is invalid."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )
        sessions_file.write_text("not valid json")

        store = load_sessions()
        assert store["sessions"] == []

    def test_load_sessions_with_missing_fields(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns store with default fields when JSON is partial."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )
        sessions_file.write_text(json.dumps({}))

        store = load_sessions()
        assert store["sessions"] == []
        assert store["last_updated"] == ""

    def test_save_sessions_creates_directories(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Save creates parent directories if they don't exist."""
        sessions_file = tmp_path / "nested" / "dirs" / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )

        store: VSCodeClaudeSessionStore = {
            "sessions": [],
            "last_updated": "2024-01-22T10:30:00Z",
        }
        save_sessions(store)

        assert sessions_file.exists()
        loaded = json.loads(sessions_file.read_text())
        assert "sessions" in loaded


class TestConfiguration:
    """Test configuration loading."""

    def test_load_vscodeclaude_config_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Loads config with valid workspace_base."""
        # Create a mock coordinator module
        mock_config = {
            ("coordinator.vscodeclaude", "workspace_base"): str(tmp_path),
            ("coordinator.vscodeclaude", "max_sessions"): "5",
        }

        def mock_get_config_values(
            self: Any, keys: list[tuple[str, str, str | None]]
        ) -> dict[tuple[str, str], str | None]:
            return {(k[0], k[1]): mock_config.get((k[0], k[1])) for k in keys}

        mock_coordinator = type(
            "MockCoordinator", (), {"get_config_values": mock_get_config_values}
        )()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: mock_coordinator,
        )

        config = load_vscodeclaude_config()
        assert config["workspace_base"] == str(tmp_path)
        assert config["max_sessions"] == 5

    def test_load_vscodeclaude_config_missing_workspace_base(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises ValueError when workspace_base missing."""
        mock_config: dict[tuple[str, str], str | None] = {
            ("coordinator.vscodeclaude", "workspace_base"): None,
            ("coordinator.vscodeclaude", "max_sessions"): None,
        }

        def mock_get_config_values(
            self: Any, keys: list[tuple[str, str, str | None]]
        ) -> dict[tuple[str, str], str | None]:
            return {(k[0], k[1]): mock_config.get((k[0], k[1])) for k in keys}

        mock_coordinator = type(
            "MockCoordinator", (), {"get_config_values": mock_get_config_values}
        )()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: mock_coordinator,
        )

        with pytest.raises(ValueError, match="workspace_base"):
            load_vscodeclaude_config()

    def test_load_vscodeclaude_config_default_max_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Uses default when max_sessions not set."""
        mock_config: dict[tuple[str, str], str | None] = {
            ("coordinator.vscodeclaude", "workspace_base"): str(tmp_path),
            ("coordinator.vscodeclaude", "max_sessions"): None,
        }

        def mock_get_config_values(
            self: Any, keys: list[tuple[str, str, str | None]]
        ) -> dict[tuple[str, str], str | None]:
            return {(k[0], k[1]): mock_config.get((k[0], k[1])) for k in keys}

        mock_coordinator = type(
            "MockCoordinator", (), {"get_config_values": mock_get_config_values}
        )()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: mock_coordinator,
        )

        config = load_vscodeclaude_config()
        assert config["max_sessions"] == DEFAULT_MAX_SESSIONS

    def test_load_vscodeclaude_config_workspace_not_exists(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises ValueError when workspace_base path doesn't exist."""
        mock_config: dict[tuple[str, str], str | None] = {
            ("coordinator.vscodeclaude", "workspace_base"): "/nonexistent/path",
            ("coordinator.vscodeclaude", "max_sessions"): None,
        }

        def mock_get_config_values(
            self: Any, keys: list[tuple[str, str, str | None]]
        ) -> dict[tuple[str, str], str | None]:
            return {(k[0], k[1]): mock_config.get((k[0], k[1])) for k in keys}

        mock_coordinator = type(
            "MockCoordinator", (), {"get_config_values": mock_get_config_values}
        )()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: mock_coordinator,
        )

        with pytest.raises(ValueError, match="does not exist"):
            load_vscodeclaude_config()

    def test_load_repo_vscodeclaude_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Loads repo-specific setup commands."""
        mock_config: dict[tuple[str, str], str | None] = {
            (
                "coordinator.repos.mcp_coder",
                "setup_commands_windows",
            ): '["uv venv", "uv sync"]',
            ("coordinator.repos.mcp_coder", "setup_commands_linux"): '["make setup"]',
        }

        def mock_get_config_values(
            self: Any, keys: list[tuple[str, str, str | None]]
        ) -> dict[tuple[str, str], str | None]:
            return {(k[0], k[1]): mock_config.get((k[0], k[1])) for k in keys}

        mock_coordinator = type(
            "MockCoordinator", (), {"get_config_values": mock_get_config_values}
        )()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: mock_coordinator,
        )

        config = load_repo_vscodeclaude_config("mcp_coder")
        assert config["setup_commands_windows"] == ["uv venv", "uv sync"]
        assert config["setup_commands_linux"] == ["make setup"]

    def test_sanitize_folder_name(self) -> None:
        """Removes invalid characters from folder names."""
        assert sanitize_folder_name("mcp-coder") == "mcp-coder"
        assert sanitize_folder_name("my repo!@#$") == "my-repo"
        assert sanitize_folder_name("test_project") == "test_project"
        assert sanitize_folder_name("a/b\\c:d") == "a-b-c-d"


class TestIssueSelection:
    """Test issue filtering for vscodeclaude."""

    def test_get_human_action_labels(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Extracts human_action labels from config."""
        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-01:created", "category": "human_action"},
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-04:plan-review", "category": "human_action"},
            ],
            "ignore_labels": ["Overview"],
        }

        def mock_load_labels_config(self: Any, config_path: Path) -> dict[str, Any]:
            return mock_labels_config

        mock_coordinator = type(
            "MockCoordinator", (), {"load_labels_config": mock_load_labels_config}
        )()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: mock_coordinator,
        )

        labels = get_human_action_labels()
        assert "status-01:created" in labels
        assert "status-04:plan-review" in labels
        assert "status-02:awaiting-planning" not in labels

    def test_get_eligible_issues_filters_by_assignment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Only returns issues assigned to user."""
        mock_issues = [
            {
                "number": 1,
                "title": "Issue 1",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": ["testuser"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/1",
                "locked": False,
            },
            {
                "number": 2,
                "title": "Issue 2",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": ["otheruser"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/2",
                "locked": False,
            },
            {
                "number": 3,
                "title": "Issue 3",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": [],  # Unassigned
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/3",
                "locked": False,
            },
        ]

        mock_issue_manager = Mock()
        mock_issue_manager.list_issues.return_value = mock_issues

        # Mock labels config
        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": [],
        }

        def mock_load_labels_config(self: Any, config_path: Path) -> dict[str, Any]:
            return mock_labels_config

        mock_coordinator = type(
            "MockCoordinator", (), {"load_labels_config": mock_load_labels_config}
        )()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: mock_coordinator,
        )

        eligible = get_eligible_vscodeclaude_issues(mock_issue_manager, "testuser")

        assert len(eligible) == 1
        assert eligible[0]["number"] == 1

    def test_get_eligible_issues_priority_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Issues sorted by priority (later stages first)."""
        mock_issues = [
            {
                "number": 1,
                "title": "Issue 1",
                "body": "",
                "state": "open",
                "labels": ["status-01:created"],
                "assignees": ["user"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/1",
                "locked": False,
            },
            {
                "number": 2,
                "title": "Issue 2",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": ["user"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/2",
                "locked": False,
            },
            {
                "number": 3,
                "title": "Issue 3",
                "body": "",
                "state": "open",
                "labels": ["status-04:plan-review"],
                "assignees": ["user"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/3",
                "locked": False,
            },
        ]

        mock_issue_manager = Mock()
        mock_issue_manager.list_issues.return_value = mock_issues

        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-01:created", "category": "human_action"},
                {"name": "status-04:plan-review", "category": "human_action"},
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": [],
        }

        def mock_load_labels_config(self: Any, config_path: Path) -> dict[str, Any]:
            return mock_labels_config

        mock_coordinator = type(
            "MockCoordinator", (), {"load_labels_config": mock_load_labels_config}
        )()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: mock_coordinator,
        )

        eligible = get_eligible_vscodeclaude_issues(mock_issue_manager, "user")

        # Should be: code-review, plan-review, created (index 0, 1, 3 in priority)
        assert len(eligible) == 3
        assert eligible[0]["number"] == 2  # code-review
        assert eligible[1]["number"] == 3  # plan-review
        assert eligible[2]["number"] == 1  # created

    def test_get_eligible_issues_excludes_ignore_labels(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips issues with ignore_labels."""
        mock_issues = [
            {
                "number": 1,
                "title": "Issue 1",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review", "Overview"],
                "assignees": ["user"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/1",
                "locked": False,
            },
            {
                "number": 2,
                "title": "Issue 2",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": ["user"],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/2",
                "locked": False,
            },
        ]

        mock_issue_manager = Mock()
        mock_issue_manager.list_issues.return_value = mock_issues

        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": ["Overview"],
        }

        def mock_load_labels_config(self: Any, config_path: Path) -> dict[str, Any]:
            return mock_labels_config

        mock_coordinator = type(
            "MockCoordinator", (), {"load_labels_config": mock_load_labels_config}
        )()
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: mock_coordinator,
        )

        eligible = get_eligible_vscodeclaude_issues(mock_issue_manager, "user")

        assert len(eligible) == 1
        assert eligible[0]["number"] == 2

    def test_get_linked_branch_single(self) -> None:
        """Returns branch when exactly one linked."""
        mock_branch_manager = Mock()
        mock_branch_manager.get_linked_branches.return_value = ["feature-123"]

        branch = get_linked_branch_for_issue(mock_branch_manager, 123)
        assert branch == "feature-123"

    def test_get_linked_branch_none(self) -> None:
        """Returns None when no branches linked."""
        mock_branch_manager = Mock()
        mock_branch_manager.get_linked_branches.return_value = []

        branch = get_linked_branch_for_issue(mock_branch_manager, 123)
        assert branch is None

    def test_get_linked_branch_multiple_raises(self) -> None:
        """Raises ValueError when multiple branches linked."""
        mock_branch_manager = Mock()
        mock_branch_manager.get_linked_branches.return_value = ["branch-a", "branch-b"]

        with pytest.raises(ValueError, match="multiple branches"):
            get_linked_branch_for_issue(mock_branch_manager, 123)


class TestWorkspaceSetup:
    """Test workspace creation and setup."""

    def test_get_working_folder_path(self) -> None:
        """Constructs correct folder path."""
        path = get_working_folder_path(
            workspace_base="/home/user/projects",
            repo_name="mcp-coder",
            issue_number=123,
        )
        assert str(path).endswith("mcp-coder_123")

    def test_get_working_folder_path_sanitizes_repo_name(self) -> None:
        """Sanitizes repo name in folder path."""
        path = get_working_folder_path(
            workspace_base="/home/user/projects",
            repo_name="my repo!@#$",
            issue_number=456,
        )
        # Should sanitize to 'my-repo'
        assert "my-repo_456" in str(path)

    def test_create_working_folder_new(self, tmp_path: Path) -> None:
        """Creates folder when doesn't exist."""
        folder = tmp_path / "new_folder"
        result = create_working_folder(folder)
        assert result is True
        assert folder.exists()

    def test_create_working_folder_exists(self, tmp_path: Path) -> None:
        """Returns False when folder exists."""
        folder = tmp_path / "existing"
        folder.mkdir()
        result = create_working_folder(folder)
        assert result is False

    def test_create_working_folder_nested(self, tmp_path: Path) -> None:
        """Creates nested directories."""
        folder = tmp_path / "a" / "b" / "c"
        result = create_working_folder(folder)
        assert result is True
        assert folder.exists()

    def test_validate_mcp_json_exists(self, tmp_path: Path) -> None:
        """Passes when .mcp.json exists."""
        (tmp_path / ".mcp.json").write_text("{}")
        validate_mcp_json(tmp_path)  # Should not raise

    def test_validate_mcp_json_missing(self, tmp_path: Path) -> None:
        """Raises when .mcp.json missing."""
        with pytest.raises(FileNotFoundError, match=".mcp.json"):
            validate_mcp_json(tmp_path)

    def test_validate_setup_commands_valid(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Passes when all commands exist in PATH."""

        # Mock shutil.which to return a path for known commands
        def mock_which(cmd: str) -> str | None:
            if cmd in ["python", "git", "echo"]:
                return f"/usr/bin/{cmd}"
            return None

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.shutil.which", mock_which
        )

        validate_setup_commands(["python --version", "git status"])

    def test_validate_setup_commands_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises when command not found in PATH."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.shutil.which",
            lambda cmd: None,
        )

        with pytest.raises(FileNotFoundError, match="not found in PATH"):
            validate_setup_commands(["nonexistent_command"])

    def test_run_setup_commands_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Runs commands in correct directory."""
        import subprocess

        commands_run: list[tuple[Any, Any]] = []

        def mock_run(cmd: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            commands_run.append((cmd, kwargs.get("cwd")))
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.subprocess.run", mock_run
        )

        run_setup_commands(tmp_path, ["echo hello", "echo world"])

        assert len(commands_run) == 2
        assert all(cwd == tmp_path for _, cwd in commands_run)

    def test_run_setup_commands_failure_aborts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises on command failure."""
        import subprocess

        def mock_run(cmd: Any, **kwargs: Any) -> None:
            raise subprocess.CalledProcessError(1, cmd)

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.subprocess.run", mock_run
        )

        with pytest.raises(subprocess.CalledProcessError):
            run_setup_commands(tmp_path, ["failing_command"])

    def test_update_gitignore_adds_entry(self, tmp_path: Path) -> None:
        """Adds vscodeclaude entry to .gitignore."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")

        update_gitignore(tmp_path)

        content = gitignore.read_text()
        assert ".vscodeclaude_status.md" in content
        assert "*.pyc" in content  # Preserves existing

    def test_update_gitignore_creates_file(self, tmp_path: Path) -> None:
        """Creates .gitignore when doesn't exist."""
        update_gitignore(tmp_path)

        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        assert ".vscodeclaude_status.md" in gitignore.read_text()

    def test_update_gitignore_idempotent(self, tmp_path: Path) -> None:
        """Doesn't duplicate entry on second call."""
        update_gitignore(tmp_path)
        update_gitignore(tmp_path)

        gitignore = tmp_path / ".gitignore"
        content = gitignore.read_text()
        assert content.count(".vscodeclaude_status.md") == 1

    def test_create_workspace_file(self, tmp_path: Path) -> None:
        """Creates valid workspace JSON file."""
        workspace_path = create_workspace_file(
            workspace_base=str(tmp_path),
            folder_name="mcp-coder_123",
            issue_number=123,
            issue_title="Add feature",
            status="status-07:code-review",
            repo_name="mcp-coder",
        )

        assert workspace_path.exists()
        assert workspace_path.suffix == ".code-workspace"

        content = json.loads(workspace_path.read_text())
        assert "folders" in content
        assert "settings" in content
        assert "#123" in content["settings"]["window.title"]

    def test_create_workspace_file_truncates_long_title(self, tmp_path: Path) -> None:
        """Truncates long issue titles."""
        long_title = "A" * 50  # More than 30 chars
        workspace_path = create_workspace_file(
            workspace_base=str(tmp_path),
            folder_name="test_1",
            issue_number=1,
            issue_title=long_title,
            status="status-01:created",
            repo_name="test",
        )

        content = json.loads(workspace_path.read_text())
        # Title should be truncated with ...
        assert "..." in content["settings"]["window.title"]

    def test_create_startup_script_windows(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Creates .bat script on Windows."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            is_intervention=False,
        )

        assert script_path.suffix == ".bat"
        assert script_path.exists()
        content = script_path.read_text()
        assert "claude" in content
        assert "/implementation_review" in content

    def test_create_startup_script_linux(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Creates .sh script on Linux."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.platform.system",
            lambda: "Linux",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            is_intervention=False,
        )

        assert script_path.suffix == ".sh"
        assert script_path.exists()

    def test_create_startup_script_intervention(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Intervention mode uses plain claude command."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-06:implementing",  # bot_busy status
            repo_name="test-repo",
            is_intervention=True,
        )

        content = script_path.read_text()
        assert "INTERVENTION" in content
        assert "/implementation_review" not in content

    def test_create_vscode_task(self, tmp_path: Path) -> None:
        """Creates tasks.json with runOn: folderOpen."""
        script_path = tmp_path / ".vscodeclaude_start.bat"
        script_path.touch()

        create_vscode_task(tmp_path, script_path)

        tasks_file = tmp_path / ".vscode" / "tasks.json"
        assert tasks_file.exists()

        content = json.loads(tasks_file.read_text())
        assert content["tasks"][0]["runOptions"]["runOn"] == "folderOpen"

    def test_create_status_file(self, tmp_path: Path) -> None:
        """Creates status markdown file."""
        create_status_file(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Add feature",
            status="status-07:code-review",
            repo_full_name="owner/repo",
            branch_name="feature-123",
            issue_url="https://github.com/owner/repo/issues/123",
            is_intervention=False,
        )

        status_file = tmp_path / ".vscodeclaude_status.md"
        assert status_file.exists()

        content = status_file.read_text()
        assert "#123" in content
        assert "Add feature" in content
        assert "code-review" in content

    def test_create_status_file_intervention(self, tmp_path: Path) -> None:
        """Status file includes intervention warning when set."""
        create_status_file(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test",
            status="status-07:code-review",
            repo_full_name="owner/repo",
            branch_name="main",
            issue_url="https://github.com/owner/repo/issues/123",
            is_intervention=True,
        )

        status_file = tmp_path / ".vscodeclaude_status.md"
        content = status_file.read_text()
        assert "INTERVENTION" in content


class TestGitOperations:
    """Test git clone/checkout/pull operations."""

    def test_setup_git_repo_clone_new(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Clones when folder is empty."""
        import subprocess

        commands: list[Any] = []

        def mock_run(cmd: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            commands.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.subprocess.run", mock_run
        )

        folder = tmp_path / "new_repo"
        folder.mkdir()

        setup_git_repo(folder, "https://github.com/owner/repo.git", "main")

        # Should have clone, checkout, pull
        assert any("clone" in str(c) for c in commands)

    def test_setup_git_repo_existing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Checkout and pull when .git exists."""
        import subprocess

        commands: list[Any] = []

        def mock_run(cmd: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            commands.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.subprocess.run", mock_run
        )

        # Create folder with .git
        folder = tmp_path / "existing_repo"
        folder.mkdir()
        (folder / ".git").mkdir()

        setup_git_repo(folder, "https://github.com/owner/repo.git", "feature-branch")

        # Should NOT clone, but should checkout and pull
        assert not any("clone" in str(c) for c in commands)
        assert any("checkout" in str(c) for c in commands)
        assert any("pull" in str(c) for c in commands)

    def test_setup_git_repo_uses_main_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Uses main branch when branch_name is None."""
        import subprocess

        commands: list[Any] = []

        def mock_run(cmd: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            commands.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.subprocess.run", mock_run
        )

        folder = tmp_path / "repo"
        folder.mkdir()
        (folder / ".git").mkdir()

        setup_git_repo(folder, "https://github.com/owner/repo.git", None)

        checkout_cmd = [c for c in commands if "checkout" in str(c)][0]
        assert "main" in checkout_cmd

    def test_setup_git_repo_folder_with_content_no_git(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises error when folder has content but no .git."""
        import subprocess

        def mock_run(cmd: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.subprocess.run", mock_run
        )

        folder = tmp_path / "has_content"
        folder.mkdir()
        (folder / "somefile.txt").write_text("content")

        with pytest.raises(ValueError, match="not a git repository"):
            setup_git_repo(folder, "https://github.com/owner/repo.git", "main")


class TestLaunch:
    """Test VSCode launch functions."""

    def test_launch_vscode_returns_pid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns PID from Popen."""
        mock_process = Mock()
        mock_process.pid = 12345

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.subprocess.Popen",
            lambda *args, **kwargs: mock_process,
        )

        workspace = tmp_path / "test.code-workspace"
        workspace.touch()

        pid = launch_vscode(workspace)
        assert pid == 12345

    def test_launch_vscode_uses_code_command(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Calls 'code' with workspace path."""
        called_args: list[Any] = []

        def mock_popen(args: Any, **kwargs: Any) -> Mock:
            called_args.extend(args)
            return Mock(pid=1)

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.subprocess.Popen",
            mock_popen,
        )

        workspace = tmp_path / "test.code-workspace"
        workspace.touch()

        launch_vscode(workspace)

        assert "code" in called_args
        assert str(workspace) in called_args

    def test_get_stage_display_name_known_statuses(self) -> None:
        """Returns human-readable stage names."""
        assert get_stage_display_name("status-07:code-review") == "CODE REVIEW"
        assert get_stage_display_name("status-04:plan-review") == "PLAN REVIEW"
        assert get_stage_display_name("status-01:created") == "ISSUE ANALYSIS"
        assert get_stage_display_name("status-10:pr-created") == "PR CREATED"

    def test_get_stage_display_name_unknown_status(self) -> None:
        """Returns uppercased status for unknown statuses."""
        result = get_stage_display_name("unknown-status")
        assert result == "UNKNOWN-STATUS"

    def test_truncate_title_short(self) -> None:
        """Returns unchanged if under max length."""
        assert truncate_title("Short title", 50) == "Short title"

    def test_truncate_title_exact_length(self) -> None:
        """Returns unchanged if exactly at max length."""
        title = "A" * 50
        result = truncate_title(title, 50)
        assert result == title
        assert len(result) == 50

    def test_truncate_title_long(self) -> None:
        """Truncates with ellipsis if over max."""
        long_title = "A" * 100
        result = truncate_title(long_title, 50)
        assert len(result) == 50
        assert result.endswith("...")
        # Should have 47 'A's followed by '...'
        assert result == "A" * 47 + "..."

    def test_stage_display_names_coverage(self) -> None:
        """All priority statuses have display names."""
        for status in VSCODECLAUDE_PRIORITY:
            assert status in STAGE_DISPLAY_NAMES


class TestOrchestration:
    """Test main orchestration functions."""

    def test_prepare_and_launch_session_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Creates session with all components."""
        # Mock all dependencies
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.create_working_folder",
            lambda p: True,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.setup_git_repo",
            lambda *args: None,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.validate_mcp_json",
            lambda p: None,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.update_gitignore",
            lambda p: None,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.create_workspace_file",
            lambda *args, **kwargs: tmp_path / "test.code-workspace",
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.create_startup_script",
            lambda *args, **kwargs: tmp_path / ".vscodeclaude_start.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.create_vscode_task",
            lambda *args: None,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.create_status_file",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.launch_vscode",
            lambda p: 9999,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.add_session",
            lambda s: None,
        )

        issue: IssueData = {
            "number": 123,
            "title": "Test issue",
            "body": "",
            "state": "open",
            "labels": ["status-07:code-review"],
            "assignees": ["testuser"],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/123",
            "locked": False,
        }

        repo_config = {
            "repo_url": "https://github.com/owner/repo.git",
        }

        vscodeclaude_config: VSCodeClaudeConfig = {
            "workspace_base": str(tmp_path),
            "max_sessions": 3,
        }

        session = prepare_and_launch_session(
            issue=issue,
            repo_config=repo_config,
            vscodeclaude_config=vscodeclaude_config,
            repo_vscodeclaude_config={},
            branch_name="main",
            is_intervention=False,
        )

        assert session["issue_number"] == 123
        assert session["vscode_pid"] == 9999
        assert session["is_intervention"] is False
        assert session["repo"] == "owner/repo"
        assert session["status"] == "status-07:code-review"

    def test_prepare_and_launch_aborts_on_git_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Aborts session and cleans up folder if git fails."""
        import subprocess

        # Create the folder that will be cleaned up
        folder_path = tmp_path / "repo_123"

        def mock_create_folder(p: Path) -> bool:
            p.mkdir(parents=True, exist_ok=True)
            return True

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.create_working_folder",
            mock_create_folder,
        )

        def failing_git(*args: Any, **kwargs: Any) -> None:
            raise subprocess.CalledProcessError(1, "git clone")

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.setup_git_repo",
            failing_git,
        )

        issue: IssueData = {
            "number": 123,
            "title": "Test",
            "body": "",
            "state": "open",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "...",
            "locked": False,
        }
        repo_config = {"repo_url": "https://github.com/owner/repo.git"}
        vscodeclaude_config: VSCodeClaudeConfig = {
            "workspace_base": str(tmp_path),
            "max_sessions": 3,
        }

        with pytest.raises(subprocess.CalledProcessError):
            prepare_and_launch_session(
                issue=issue,
                repo_config=repo_config,
                vscodeclaude_config=vscodeclaude_config,
                repo_vscodeclaude_config={},
                branch_name="main",
                is_intervention=False,
            )

        # Folder should be cleaned up on failure
        assert not folder_path.exists()

    def test_prepare_and_launch_aborts_on_setup_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Aborts session and cleans up folder if setup commands fail."""
        import subprocess

        folder_path = tmp_path / "repo_123"

        def mock_create_folder(p: Path) -> bool:
            p.mkdir(parents=True, exist_ok=True)
            return True

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.create_working_folder",
            mock_create_folder,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.setup_git_repo",
            lambda *args: None,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.validate_mcp_json",
            lambda p: None,
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.validate_setup_commands",
            lambda c: None,
        )

        def failing_setup(*args: Any, **kwargs: Any) -> None:
            raise subprocess.CalledProcessError(1, "uv sync")

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.run_setup_commands",
            failing_setup,
        )

        issue: IssueData = {
            "number": 123,
            "title": "Test",
            "body": "",
            "state": "open",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "...",
            "locked": False,
        }
        repo_config = {"repo_url": "https://github.com/owner/repo.git"}
        vscodeclaude_config: VSCodeClaudeConfig = {
            "workspace_base": str(tmp_path),
            "max_sessions": 3,
        }
        repo_vscodeclaude_config: RepoVSCodeClaudeConfig = {
            "setup_commands_windows": ["uv sync"],
        }

        # Mock platform to Windows to trigger setup commands
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.platform.system",
            lambda: "Windows",
        )

        with pytest.raises(subprocess.CalledProcessError):
            prepare_and_launch_session(
                issue=issue,
                repo_config=repo_config,
                vscodeclaude_config=vscodeclaude_config,
                repo_vscodeclaude_config=repo_vscodeclaude_config,
                branch_name="main",
                is_intervention=False,
            )

        # Folder should be cleaned up on failure
        assert not folder_path.exists()

    def test_process_eligible_issues_respects_max_sessions(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Doesn't start sessions beyond max."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_active_session_count",
            lambda: 2,
        )

        # Should return empty since already at/above max
        sessions = process_eligible_issues(
            repo_name="test",
            repo_config={"repo_url": "https://github.com/owner/repo.git"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 2},
            max_sessions=2,
        )

        assert sessions == []

    def test_process_eligible_issues_applies_repo_filter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips when repo_filter doesn't match."""
        sessions = process_eligible_issues(
            repo_name="test",
            repo_config={"repo_url": "https://github.com/owner/repo.git"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            repo_filter="other_repo",
        )

        assert sessions == []

    def test_restart_closed_sessions_removes_orphans(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Removes sessions with missing folders."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock vscode not running
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.check_vscode_running",
            lambda pid: False,
        )

        # Create session with non-existent folder
        session = {
            "folder": str(tmp_path / "nonexistent"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        restarted = restart_closed_sessions()

        # No sessions restarted
        assert restarted == []

        # Session should be removed
        loaded = load_sessions()
        assert len(loaded["sessions"]) == 0

    def test_restart_closed_sessions_relaunches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Relaunches VSCode for valid sessions."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock vscode not running
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.check_vscode_running",
            lambda pid: False,
        )

        # Create working folder and workspace file
        working_folder = tmp_path / "repo_123"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_123.code-workspace"
        workspace_file.write_text("{}")

        # Mock launch_vscode
        new_pid = 9999
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.launch_vscode",
            lambda w: new_pid,
        )

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        restarted = restart_closed_sessions()

        assert len(restarted) == 1
        assert restarted[0]["vscode_pid"] == new_pid

        # PID should be updated in store
        loaded = load_sessions()
        assert loaded["sessions"][0]["vscode_pid"] == new_pid

    def test_restart_closed_sessions_skips_running(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips sessions with running VSCode."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock vscode running
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.check_vscode_running",
            lambda pid: True,
        )

        session = {
            "folder": str(tmp_path / "existing"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        restarted = restart_closed_sessions()

        # No sessions restarted since vscode is running
        assert restarted == []

    def test_handle_pr_created_issues_prints_url(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Prints issue URL for pr-created issues."""
        mock_issue_manager = Mock()

        issue: IssueData = {
            "number": 123,
            "title": "Test issue",
            "body": "",
            "state": "open",
            "labels": ["status-10:pr-created"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/123",
            "locked": False,
        }
        issues: list[IssueData] = [issue]

        handle_pr_created_issues(issues)

        captured = capsys.readouterr()
        assert "#123" in captured.out
        assert "https://github.com/owner/repo/issues/123" in captured.out

    def test_handle_pr_created_issues_empty_list(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Does nothing for empty list."""
        mock_issue_manager = Mock()
        handle_pr_created_issues([])

        captured = capsys.readouterr()
        assert captured.out == ""


# =============================================================================
# CLI Integration Tests (Step 7)
# =============================================================================


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

        import argparse

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

        import argparse

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
        from pathlib import Path

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

        import argparse

        args = argparse.Namespace(
            repo=None, max_sessions=None, cleanup=False, intervene=False, issue=None
        )

        result = execute_coordinator_vscodeclaude(args)

        assert result == 1  # Exit to let user configure
        captured = capsys.readouterr()
        assert "config" in captured.out.lower()


# =============================================================================
# Status Display Tests (Step 8)
# =============================================================================


class TestStatusDisplay:
    """Test status table and display functions."""

    def test_get_issue_current_status_returns_status(self) -> None:
        """Returns status label when found."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import (
            get_issue_current_status,
        )

        mock_manager = Mock()
        mock_manager.get_issue.return_value = {
            "labels": ["status-07:code-review", "other-label"],
        }

        result = get_issue_current_status(mock_manager, 123)

        assert result == "status-07:code-review"
        mock_manager.get_issue.assert_called_once_with(123)

    def test_get_issue_current_status_returns_none_no_status(self) -> None:
        """Returns None when no status label found."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import (
            get_issue_current_status,
        )

        mock_manager = Mock()
        mock_manager.get_issue.return_value = {"labels": ["other-label"]}

        result = get_issue_current_status(mock_manager, 123)

        assert result is None

    def test_get_issue_current_status_returns_none_on_error(self) -> None:
        """Returns None on API error."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import (
            get_issue_current_status,
        )

        mock_manager = Mock()
        mock_manager.get_issue.side_effect = Exception("API error")

        result = get_issue_current_status(mock_manager, 123)

        assert result is None

    def test_get_issue_current_status_returns_none_issue_not_found(self) -> None:
        """Returns None when issue not found."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import (
            get_issue_current_status,
        )

        mock_manager = Mock()
        mock_manager.get_issue.return_value = None

        result = get_issue_current_status(mock_manager, 123)

        assert result is None

    def test_is_session_stale_same_status(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns False when status unchanged."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import is_session_stale

        mock_issue = {"labels": ["status-07:code-review"]}
        mock_manager = Mock()
        mock_manager.get_issue.return_value = mock_issue

        mock_coordinator = Mock()
        mock_coordinator.IssueManager.return_value = mock_manager

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: mock_coordinator,
        )

        session: VSCodeClaudeSession = {
            "folder": "/test",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        assert is_session_stale(session) is False

    def test_is_session_stale_status_changed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns True when status changed."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import is_session_stale

        mock_issue = {"labels": ["status-08:ready-pr"]}  # Changed
        mock_manager = Mock()
        mock_manager.get_issue.return_value = mock_issue

        mock_coordinator = Mock()
        mock_coordinator.IssueManager.return_value = mock_manager

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: mock_coordinator,
        )

        session: VSCodeClaudeSession = {
            "folder": "/test",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",  # Original
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        assert is_session_stale(session) is True

    def test_is_session_stale_returns_true_on_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns True (conservative) when status cannot be retrieved."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import is_session_stale

        mock_manager = Mock()
        mock_manager.get_issue.return_value = None  # Issue not found

        mock_coordinator = Mock()
        mock_coordinator.IssueManager.return_value = mock_manager

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: mock_coordinator,
        )

        session: VSCodeClaudeSession = {
            "folder": "/test",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        assert is_session_stale(session) is True

    def test_check_folder_dirty_clean(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns False for clean git repo."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import check_folder_dirty

        def mock_run(cmd: list[str], **kwargs: Any) -> Mock:
            result = Mock()
            result.stdout = ""  # Empty = clean
            result.returncode = 0
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        assert check_folder_dirty(tmp_path) is False

    def test_check_folder_dirty_with_changes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns True when uncommitted changes exist."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import check_folder_dirty

        def mock_run(cmd: list[str], **kwargs: Any) -> Mock:
            result = Mock()
            result.stdout = "M  file.py\n"  # Modified file
            result.returncode = 0
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        assert check_folder_dirty(tmp_path) is True

    def test_check_folder_dirty_returns_true_on_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns True (conservative) when git command fails."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import check_folder_dirty

        def mock_run(cmd: list[str], **kwargs: Any) -> Mock:
            raise subprocess.CalledProcessError(1, cmd)

        monkeypatch.setattr("subprocess.run", mock_run)

        assert check_folder_dirty(tmp_path) is True

    def test_get_next_action_active(self) -> None:
        """Returns (active) when VSCode running."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import get_next_action

        session: VSCodeClaudeSession = {
            "folder": "/test",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        action = get_next_action(
            session, is_stale=False, is_dirty=False, is_vscode_running=True
        )
        assert action == "(active)"

    def test_get_next_action_restart(self) -> None:
        """Returns Restart when closed but not stale."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import get_next_action

        session: VSCodeClaudeSession = {
            "folder": "/test",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        action = get_next_action(
            session, is_stale=False, is_dirty=False, is_vscode_running=False
        )
        assert "Restart" in action

    def test_get_next_action_delete(self) -> None:
        """Returns Delete when stale and clean."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import get_next_action

        session: VSCodeClaudeSession = {
            "folder": "/test",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        action = get_next_action(
            session, is_stale=True, is_dirty=False, is_vscode_running=False
        )
        assert "Delete" in action

    def test_get_next_action_manual(self) -> None:
        """Returns Manual cleanup when stale and dirty."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import get_next_action

        session: VSCodeClaudeSession = {
            "folder": "/test",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        action = get_next_action(
            session, is_stale=True, is_dirty=True, is_vscode_running=False
        )
        assert "Manual" in action

    def test_display_status_table_empty(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Handles empty sessions and issues."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import display_status_table

        display_status_table(sessions=[], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        assert "No sessions" in captured.out or "Folder" in captured.out

    def test_display_status_table_with_session(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Displays session information."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import display_status_table

        # Mock check_vscode_running
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.check_vscode_running",
            lambda pid: False,
        )

        # Mock check_folder_dirty
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.check_folder_dirty",
            lambda path: False,
        )

        # Mock is_session_stale
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.is_session_stale",
            lambda s: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(tmp_path / "test_folder"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        assert "#123" in captured.out
        assert "owner/repo".split("/")[-1] in captured.out  # "repo"

    def test_display_status_table_with_eligible_issue(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Displays eligible issues not yet in sessions."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import display_status_table

        issue: IssueData = {
            "number": 456,
            "title": "New issue",
            "body": "",
            "state": "open",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/456",
            "locked": False,
        }

        eligible_issues: list[tuple[str, IssueData]] = [("myrepo", issue)]

        display_status_table(
            sessions=[], eligible_issues=eligible_issues, repo_filter=None
        )

        captured = capsys.readouterr()
        assert "#456" in captured.out
        assert "Create and start" in captured.out


# =============================================================================
# Cleanup Tests (Step 8)
# =============================================================================


class TestCleanup:
    """Test cleanup functions."""

    def test_get_stale_sessions_returns_stale(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns stale sessions with dirty status."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import get_stale_sessions

        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock VSCode not running
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.check_vscode_running",
            lambda pid: False,
        )

        # Mock session is stale
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.is_session_stale",
            lambda s: True,
        )

        # Mock folder not dirty
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.check_folder_dirty",
            lambda path: False,
        )

        stale_folder = tmp_path / "stale_folder"
        stale_folder.mkdir()

        session = {
            "folder": str(stale_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-01T00:00:00Z"}
        sessions_file.write_text(json.dumps(store))

        result = get_stale_sessions()

        assert len(result) == 1
        assert result[0][0]["folder"] == str(stale_folder)
        assert result[0][1] is False  # Not dirty

    def test_get_stale_sessions_skips_running(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips sessions with running VSCode."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import get_stale_sessions

        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock VSCode running
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.check_vscode_running",
            lambda pid: True,
        )

        session = {
            "folder": str(tmp_path / "folder"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-01T00:00:00Z"}
        sessions_file.write_text(json.dumps(store))

        result = get_stale_sessions()

        assert len(result) == 0

    def test_cleanup_stale_sessions_dry_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dry run reports but doesn't delete."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import (
            cleanup_stale_sessions,
        )

        stale_session = {
            "folder": str(tmp_path / "stale_folder"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        # Create the folder
        (tmp_path / "stale_folder").mkdir()

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_stale_sessions",
            lambda: [(stale_session, False)],  # Not dirty
        )

        result = cleanup_stale_sessions(dry_run=True)

        # Folder should still exist
        assert (tmp_path / "stale_folder").exists()
        # Dry run doesn't add to deleted list
        assert len(result.get("deleted", [])) == 0

    def test_cleanup_stale_sessions_skips_dirty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips dirty folders with warning."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import (
            cleanup_stale_sessions,
        )

        dirty_session = {
            "folder": str(tmp_path / "dirty_folder"),
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        (tmp_path / "dirty_folder").mkdir()

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_stale_sessions",
            lambda: [(dirty_session, True)],  # Dirty
        )

        result = cleanup_stale_sessions(dry_run=False)

        # Folder should still exist (dirty)
        assert (tmp_path / "dirty_folder").exists()
        assert str(tmp_path / "dirty_folder") in result.get("skipped", [])

    def test_cleanup_stale_sessions_deletes_clean(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Deletes clean stale folders."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import (
            cleanup_stale_sessions,
        )

        clean_session = {
            "folder": str(tmp_path / "clean_folder"),
            "repo": "owner/repo",
            "issue_number": 789,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        (tmp_path / "clean_folder").mkdir()

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_stale_sessions",
            lambda: [(clean_session, False)],  # Clean
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.delete_session_folder",
            lambda s: True,
        )

        result = cleanup_stale_sessions(dry_run=False)

        assert str(tmp_path / "clean_folder") in result.get("deleted", [])

    def test_delete_session_folder_removes_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Deletes folder and removes session."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import (
            delete_session_folder,
        )

        folder = tmp_path / "to_delete"
        folder.mkdir()
        (folder / "file.txt").write_text("test")

        # Create workspace file
        workspace_file = tmp_path / "to_delete.code-workspace"
        workspace_file.write_text("{}")

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.remove_session",
            lambda f: True,
        )

        result = delete_session_folder(session)

        assert result is True
        assert not folder.exists()
        assert not workspace_file.exists()

    def test_delete_session_folder_handles_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Handles already-deleted folder gracefully."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import (
            delete_session_folder,
        )

        # Folder doesn't exist
        session: VSCodeClaudeSession = {
            "folder": str(tmp_path / "nonexistent"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.remove_session",
            lambda f: True,
        )

        result = delete_session_folder(session)

        assert result is True  # Still succeeds - removes session from store

    def test_cleanup_stale_sessions_empty(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Reports when no stale sessions."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude import (
            cleanup_stale_sessions,
        )

        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.get_stale_sessions",
            lambda: [],
        )

        result = cleanup_stale_sessions(dry_run=True)

        assert result == {"deleted": [], "skipped": []}
        captured = capsys.readouterr()
        assert "No stale sessions" in captured.out
