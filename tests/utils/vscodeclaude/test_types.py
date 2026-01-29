"""Test type definitions and constants for VSCode Claude session management."""

import pytest

from mcp_coder.utils.vscodeclaude.types import (
    DEFAULT_MAX_SESSIONS,
    HUMAN_ACTION_COMMANDS,
    STAGE_DISPLAY_NAMES,
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

    def test_stage_display_names_coverage(self) -> None:
        """All priority statuses have display names."""
        for status in VSCODECLAUDE_PRIORITY:
            assert status in STAGE_DISPLAY_NAMES
