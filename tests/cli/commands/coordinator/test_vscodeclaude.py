"""Test type definitions and constants for VSCode Claude session management."""

import pytest

from mcp_coder.cli.commands.coordinator.vscodeclaude import (
    DEFAULT_MAX_SESSIONS,
    HUMAN_ACTION_COMMANDS,
    STATUS_EMOJI,
    VSCODECLAUDE_PRIORITY,
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
    VSCodeClaudeSession,
    VSCodeClaudeSessionStore,
)


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
        assert "{issue_number}" in STARTUP_SCRIPT_WINDOWS
        assert "{automated_section}" in STARTUP_SCRIPT_WINDOWS
        assert "{stage_name}" in STARTUP_SCRIPT_WINDOWS
        assert "{title}" in STARTUP_SCRIPT_WINDOWS
        assert "{repo}" in STARTUP_SCRIPT_WINDOWS
        assert "{status}" in STARTUP_SCRIPT_WINDOWS
        assert "{interactive_section}" in STARTUP_SCRIPT_WINDOWS

    def test_startup_script_linux_has_placeholders(self) -> None:
        """Linux script has required placeholders."""
        from mcp_coder.cli.commands.coordinator.vscodeclaude_templates import (
            STARTUP_SCRIPT_LINUX,
        )

        assert "{emoji}" in STARTUP_SCRIPT_LINUX
        assert "{issue_number}" in STARTUP_SCRIPT_LINUX
        assert "{stage_name}" in STARTUP_SCRIPT_LINUX
        assert "{title}" in STARTUP_SCRIPT_LINUX
        assert "{repo}" in STARTUP_SCRIPT_LINUX
        assert "{status}" in STARTUP_SCRIPT_LINUX
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
        import json

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
        assert "{stage_name}" in BANNER_TEMPLATE
        assert "{issue_number}" in BANNER_TEMPLATE
        assert "{title}" in BANNER_TEMPLATE
        assert "{repo}" in BANNER_TEMPLATE
        assert "{status}" in BANNER_TEMPLATE

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
        assert "#123" in formatted
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
