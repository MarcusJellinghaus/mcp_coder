"""Test type definitions and constants for VSCode Claude session management."""

import dataclasses
import json
from importlib import resources
from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.types import (
    DEFAULT_MAX_SESSIONS,
    Decision,
    DetectionSignals,
    IssueState,
    LivenessRule,
    LivenessVerdict,
    RepoVSCodeClaudeConfig,
    SessionAction,
    SessionAssessment,
    Transition,
    VSCodeClaudeConfig,
    VSCodeClaudeSession,
    VSCodeClaudeSessionStore,
)


class TestTypes:
    """Test type definitions and constants."""

    def test_default_max_sessions(self) -> None:
        """Default max sessions is 3."""
        assert DEFAULT_MAX_SESSIONS == 3


class TestTypeHints:
    """Test TypedDict structure validation."""

    def test_vscodeclaude_session_type_structure(self) -> None:
        """VSCodeClaudeSession has all required fields."""
        annotations = VSCodeClaudeSession.__annotations__
        expected_fields = {
            "folder",
            "repo",
            "issue_number",
            "status",
            "vscode_pid",
            "vscode_pid_create_time",
            "started_at",
            "is_intervention",
            "last_active",
            "last_active_rule",
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
        expected_fields = {
            "setup_commands_windows",
            "setup_commands_linux",
            "setup_commands_macos",
        }
        assert set(annotations.keys()) == expected_fields

    def test_vscodeclaude_session_creation(self) -> None:
        """Can create a valid VSCodeClaudeSession instance."""
        session: VSCodeClaudeSession = {
            "folder": "/path/to/folder",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-01:created",
            "vscode_pid": 1234,
            "vscode_pid_create_time": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
            "last_active": None,
            "last_active_rule": None,
        }
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
            "setup_commands_macos": ["cmd5", "cmd6"],
        }
        assert isinstance(config["setup_commands_windows"], list)
        assert isinstance(config["setup_commands_linux"], list)
        assert isinstance(config["setup_commands_macos"], list)

    def test_repo_vscodeclaude_config_partial(self) -> None:
        """Can create a partial RepoVSCodeClaudeConfig instance."""
        config: RepoVSCodeClaudeConfig = {"setup_commands_windows": ["cmd1"]}
        assert "setup_commands_windows" in config
        assert "setup_commands_linux" not in config
        assert "setup_commands_macos" not in config

    def test_repo_vscodeclaude_config_macos_only(self) -> None:
        """Can create RepoVSCodeClaudeConfig with only setup_commands_macos."""
        config: RepoVSCodeClaudeConfig = {"setup_commands_macos": ["brew install foo"]}
        assert config["setup_commands_macos"] == ["brew install foo"]
        assert "setup_commands_windows" not in config
        assert "setup_commands_linux" not in config


def _make_signals() -> DetectionSignals:
    return DetectionSignals(
        folder_exists=True,
        title_match=True,
        cmdline_match=False,
        pid_alive=True,
        found_pid=1234,
        age_seconds=12.5,
        within_grace=False,
        directory_empty=False,
    )


def _make_assessment() -> SessionAssessment:
    return SessionAssessment(
        folder="/path/to/folder",
        signals=_make_signals(),
        verdict=LivenessVerdict(active=True, rule=LivenessRule.TITLE),
        issue_state=IssueState(
            is_open=True,
            is_stale=False,
            is_blocked=False,
            is_unassigned=False,
            is_eligible=True,
            stale_target=None,
        ),
        transition=Transition(flipped_to_inactive=False),
        decision=Decision(
            action=SessionAction.KEEP_ACTIVE,
            reason="vscode running",
            destructive=False,
        ),
        pid_needs_refresh=False,
        found_pid=1234,
    )


class TestAssessmentEnums:
    """Enums carry stable string values."""

    def test_liveness_rule_values(self) -> None:
        assert LivenessRule.TITLE.value == "title"
        assert LivenessRule.PID.value == "pid"
        assert LivenessRule.CMDLINE.value == "cmdline"
        assert LivenessRule.NO_ARTIFACTS.value == "no_artifacts"
        assert LivenessRule.NO_MATCH.value == "no_match"

    def test_session_action_values(self) -> None:
        assert SessionAction.KEEP_ACTIVE.value == "keep_active"
        assert SessionAction.RESTART.value == "restart"
        assert SessionAction.DELETE.value == "delete"
        assert SessionAction.REMOVE_MISSING.value == "remove_missing"
        assert SessionAction.INVESTIGATE_ZOMBIE.value == "investigate_zombie"
        assert SessionAction.SKIP.value == "skip"


class TestAssessmentFrozen:
    """Every assessment dataclass is frozen (apply() cannot mutate it)."""

    def test_detection_signals_frozen(self) -> None:
        signals = _make_signals()
        with pytest.raises(dataclasses.FrozenInstanceError):
            signals.title_match = False  # type: ignore[misc]

    def test_liveness_verdict_frozen(self) -> None:
        verdict = LivenessVerdict(active=True, rule=LivenessRule.TITLE)
        with pytest.raises(dataclasses.FrozenInstanceError):
            verdict.active = False  # type: ignore[misc]

    def test_issue_state_frozen(self) -> None:
        state = IssueState(
            is_open=True,
            is_stale=False,
            is_blocked=False,
            is_unassigned=False,
            is_eligible=True,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            state.is_open = False  # type: ignore[misc]

    def test_transition_frozen(self) -> None:
        transition = Transition(flipped_to_inactive=False)
        with pytest.raises(dataclasses.FrozenInstanceError):
            transition.flipped_to_inactive = True  # type: ignore[misc]

    def test_decision_frozen(self) -> None:
        decision = Decision(action=SessionAction.SKIP, reason="x", destructive=False)
        with pytest.raises(dataclasses.FrozenInstanceError):
            decision.destructive = True  # type: ignore[misc]

    def test_session_assessment_frozen(self) -> None:
        assessment = _make_assessment()
        with pytest.raises(dataclasses.FrozenInstanceError):
            assessment.folder = "other"  # type: ignore[misc]


class TestSessionAssessmentEmbedding:
    """SessionAssessment embeds the four typed sub-results, not flattened fields."""

    def test_embeds_sub_results(self) -> None:
        assessment = _make_assessment()
        assert assessment.verdict.active is True
        assert assessment.verdict.rule is LivenessRule.TITLE
        assert assessment.decision.action is SessionAction.KEEP_ACTIVE
        assert assessment.transition.flipped_to_inactive is False
        assert assessment.issue_state.is_eligible is True

    def test_issue_state_stale_target_defaults_none(self) -> None:
        state = IssueState(
            is_open=True,
            is_stale=False,
            is_blocked=False,
            is_unassigned=False,
            is_eligible=True,
        )
        assert state.stale_target is None


class TestSessionAssessmentSerializer:
    """The single serializer flattens signals + four sub-results."""

    def test_to_audit_record_includes_session_metadata(self) -> None:
        assessment = _make_assessment()
        session: VSCodeClaudeSession = {
            "folder": "/path/to/folder",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "vscode_pid_create_time": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
            "last_active": None,
            "last_active_rule": None,
        }
        record = assessment.to_audit_record(session)
        assert record["repo"] == "owner/repo"
        assert record["issue_number"] == 123
        assert record["status"] == "status-07:code-review"
        assert record["verdict"]["rule"] == "title"
        assert record["decision"]["action"] == "keep_active"
        assert record["signals"]["title_match"] is True

    def test_to_explain_returns_string(self) -> None:
        assessment = _make_assessment()
        text = assessment.to_explain()
        assert isinstance(text, str)
        assert "folder: /path/to/folder" in text
        assert "verdict:" in text


class TestLabelsJsonVscodeclaudeMetadata:
    """Test that labels.json has required vscodeclaude metadata."""

    def test_human_action_labels_have_vscodeclaude_metadata(self) -> None:
        """All human_action labels have required vscodeclaude fields."""
        config_resource = resources.files("mcp_coder.config") / "labels.json"
        config_path = Path(str(config_resource))
        labels_config = json.loads(config_path.read_text(encoding="utf-8"))

        human_action_labels = [
            label
            for label in labels_config["workflow_labels"]
            if label["category"] == "human_action"
        ]

        assert len(human_action_labels) == 14

        base_fields = {"emoji", "display_name", "stage_short"}

        for label in human_action_labels:
            assert "vscodeclaude" in label, f"Missing vscodeclaude in {label['name']}"
            vscodeclaude = label["vscodeclaude"]
            assert base_fields.issubset(
                set(vscodeclaude.keys())
            ), f"Missing base fields in {label['name']}"
            if "commands" in vscodeclaude:
                assert isinstance(
                    vscodeclaude["commands"], list
                ), f"commands must be a list in {label['name']}"
                assert all(
                    isinstance(cmd, str) for cmd in vscodeclaude["commands"]
                ), f"All commands must be strings in {label['name']}"

    def test_pr_created_has_no_commands(self) -> None:
        """status-10:pr-created should have no commands key."""
        config_resource = resources.files("mcp_coder.config") / "labels.json"
        config_path = Path(str(config_resource))
        labels_config = json.loads(config_path.read_text(encoding="utf-8"))

        pr_created = next(
            label
            for label in labels_config["workflow_labels"]
            if label["name"] == "status-10:pr-created"
        )

        assert "commands" not in pr_created["vscodeclaude"]
