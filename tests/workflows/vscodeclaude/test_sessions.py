"""Test session management functions for VSCode Claude."""

import json
from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.assessment import build_active_session_set
from mcp_coder.workflows.vscodeclaude.detection import check_vscode_running
from mcp_coder.workflows.vscodeclaude.sessions import (
    add_session,
    get_session_for_issue,
    get_sessions_file_path,
    load_sessions,
    remove_session,
    save_sessions,
    session_has_artifacts,
    update_session_pid,
    update_session_status,
)
from mcp_coder.workflows.vscodeclaude.types import (
    Decision,
    DetectionSignals,
    IssueState,
    LivenessRule,
    LivenessVerdict,
    SessionAction,
    SessionAssessment,
    Transition,
    VSCodeClaudeSession,
    VSCodeClaudeSessionStore,
)


def _make_assessment(folder: str, *, active: bool = False) -> SessionAssessment:
    """Build a minimal SessionAssessment for the build_active_session_set wrapper."""
    rule = LivenessRule.TITLE if active else LivenessRule.NO_MATCH
    return SessionAssessment(
        folder=folder,
        signals=DetectionSignals(
            folder_exists=True,
            title_match=active,
            cmdline_match=False,
            pid_alive=False,
            found_pid=None,
            age_seconds=0.0,
            within_grace=False,
            directory_empty=False,
        ),
        verdict=LivenessVerdict(active=active, rule=rule),
        issue_state=IssueState(
            is_open=True,
            is_stale=False,
            is_blocked=False,
            is_unassigned=False,
            is_eligible=True,
        ),
        transition=Transition(flipped_to_inactive=False),
        decision=Decision(action=SessionAction.SKIP, reason="", destructive=False),
        pid_needs_refresh=False,
        found_pid=None,
    )


class TestSessionManagement:
    """Test session load/save/check functions."""

    def test_get_sessions_file_path(self) -> None:
        """Sessions file is in .mcp_coder on all platforms."""
        path = get_sessions_file_path()
        assert ".mcp_coder" in str(path)
        assert "vscodeclaude_sessions.json" in str(path)

    def test_load_sessions_empty_when_no_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns empty store when file doesn't exist."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
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
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        session: VSCodeClaudeSession = {
            "folder": str(tmp_path / "test_123"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
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
        assert check_vscode_running(None, None) is False

    def test_check_vscode_running_nonexistent_pid(self) -> None:
        """Nonexistent PID returns False."""
        # Use a PID that almost certainly doesn't exist
        assert check_vscode_running(999999999, None) is False

    def test_get_session_for_issue_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Finds session by repo and issue number."""
        # Setup session store with test data
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        session = {
            "folder": str(tmp_path / "test_folder"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        found = get_session_for_issue("owner/repo", 123, str(tmp_path))
        assert found is not None
        assert found["issue_number"] == 123  # pylint: disable=unsubscriptable-object

    def test_get_session_for_issue_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns None when no matching session."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        store = {"sessions": [], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        found = get_session_for_issue("owner/repo", 999, str(tmp_path))
        assert found is None

    def test_add_session(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Adds session to store."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        session: VSCodeClaudeSession = {
            "folder": "/test/folder",
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-04:plan-review",
            "vscode_pid": 5678,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
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
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
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
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        store = {"sessions": [], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        result = remove_session("/nonexistent/folder")
        assert result is False

    def test_build_active_session_set(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Thin read-only wrapper: projects verdict.active -> dict[folder, bool], no writes.

        Back-compat invariant — the wrapper preserves the legacy
        ``dict[folder, bool]`` contract (one entry per session) by delegating to
        ``build_assessments`` and projecting each verdict's ``active`` flag. It
        is read-only: the PID refresh moved into ``apply_assessments``, so
        ``save_sessions`` is never called here.
        """
        folder_a = str(tmp_path / "session_a")
        folder_b = str(tmp_path / "session_b")

        # Control the assessment build; the lazy import inside the wrapper
        # resolves this attribute from the assessment module at call time.
        def fake_build_assessments(
            sessions: list[VSCodeClaudeSession],
            cached_issues_by_repo: object = None,
        ) -> dict[str, SessionAssessment]:
            return {
                folder_a: _make_assessment(folder_a, active=True),
                folder_b: _make_assessment(folder_b, active=False),
            }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.assessment.build_assessments",
            fake_build_assessments,
        )

        # The wrapper must perform no disk writes.
        save_calls: list[object] = []
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.save_sessions",
            save_calls.append,
        )

        sessions: list[VSCodeClaudeSession] = [
            {
                "folder": folder_a,
                "repo": "o/r",
                "issue_number": 1,
                "status": "s",
                "vscode_pid": 1111,
                "vscode_pid_create_time": None,
                "last_active": None,
                "last_active_rule": None,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            },
            {
                "folder": folder_b,
                "repo": "o/r",
                "issue_number": 2,
                "status": "s",
                "vscode_pid": 2222,
                "vscode_pid_create_time": None,
                "last_active": None,
                "last_active_rule": None,
                "started_at": "2024-01-01T00:00:00Z",
                "is_intervention": False,
            },
        ]

        result = build_active_session_set(sessions)

        # Legacy dict[folder, bool] contract: one entry per session.
        assert result == {folder_a: True, folder_b: False}
        # Read-only: no sessions.json writes.
        assert save_calls == []

    def test_update_session_pid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Updates VSCode PID for existing session."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
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
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
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
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
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
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        store: VSCodeClaudeSessionStore = {
            "sessions": [],
            "last_updated": "2024-01-22T10:30:00Z",
        }
        save_sessions(store)

        assert sessions_file.exists()
        loaded = json.loads(sessions_file.read_text(encoding="utf-8"))
        assert "sessions" in loaded


class TestSessionHasArtifacts:
    """Tests for session_has_artifacts function."""

    def test_returns_true_when_folder_exists(self, tmp_path: Path) -> None:
        """Returns True when the session folder exists."""
        folder = tmp_path / "mcp_coder_123"
        folder.mkdir()
        assert session_has_artifacts(str(folder)) is True

    def test_returns_false_when_only_workspace_file_exists(
        self, tmp_path: Path
    ) -> None:
        """Returns False when folder is gone but workspace file lingers (orphan).

        The workspace file is a launcher pointing at the folder; without the
        folder it points at nothing. Treating the orphan as a live artifact
        was the bug that produced false-active sessions and blocked cleanup.
        """
        folder = tmp_path / "mcp_coder_123"
        # Don't create the folder, but create the workspace file
        workspace = tmp_path / "mcp_coder_123.code-workspace"
        workspace.write_text("{}")
        assert session_has_artifacts(str(folder)) is False

    def test_returns_false_when_neither_exists(self, tmp_path: Path) -> None:
        """Returns False when neither folder nor workspace file exists (zombie session)."""
        folder = tmp_path / "mcp_coder_123"
        # Neither folder nor workspace file created
        assert session_has_artifacts(str(folder)) is False

    def test_returns_true_when_both_exist(self, tmp_path: Path) -> None:
        """Returns True when both folder and workspace file exist."""
        folder = tmp_path / "mcp_coder_123"
        folder.mkdir()
        workspace = tmp_path / "mcp_coder_123.code-workspace"
        workspace.write_text("{}")
        assert session_has_artifacts(str(folder)) is True


class TestUpdateSessionStatus:
    """Tests for update_session_status function."""

    def test_updates_existing_session_status(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should update status for existing session."""
        # Setup: Create session store with one session
        sessions_file = tmp_path / "sessions.json"
        initial_store = {
            "sessions": [
                {
                    "folder": "/workspace/repo_123",
                    "repo": "owner/repo",
                    "issue_number": 123,
                    "status": "status-01:created",
                    "vscode_pid": 1234,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(initial_store))

        # Patch get_sessions_file_path to use tmp_path
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Act
        result = update_session_status("/workspace/repo_123", "status-04:plan-review")

        # Assert
        assert result is True
        updated_store = json.loads(sessions_file.read_text())
        assert updated_store["sessions"][0]["status"] == "status-04:plan-review"

    def test_returns_false_for_nonexistent_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return False when session not found."""
        sessions_file = tmp_path / "sessions.json"
        initial_store = {"sessions": [], "last_updated": ""}
        sessions_file.write_text(json.dumps(initial_store))

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        result = update_session_status("/nonexistent/path", "status-04:plan-review")

        assert result is False

    def test_does_not_modify_other_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should only update the matching session."""
        sessions_file = tmp_path / "sessions.json"
        initial_store = {
            "sessions": [
                {
                    "folder": "/workspace/repo_123",
                    "repo": "owner/repo",
                    "issue_number": 123,
                    "status": "status-01:created",
                    "vscode_pid": 1234,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                },
                {
                    "folder": "/workspace/repo_456",
                    "repo": "owner/repo",
                    "issue_number": 456,
                    "status": "status-01:created",
                    "vscode_pid": 5678,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                },
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(initial_store))

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        update_session_status("/workspace/repo_123", "status-04:plan-review")

        updated_store = json.loads(sessions_file.read_text())
        # First session updated
        assert updated_store["sessions"][0]["status"] == "status-04:plan-review"
        # Second session unchanged
        assert updated_store["sessions"][1]["status"] == "status-01:created"

    def test_updates_last_updated_timestamp(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should update the last_updated timestamp."""
        sessions_file = tmp_path / "sessions.json"
        initial_store = {
            "sessions": [
                {
                    "folder": "/workspace/repo_123",
                    "repo": "owner/repo",
                    "issue_number": 123,
                    "status": "status-01:created",
                    "vscode_pid": 1234,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "old-timestamp",
        }
        sessions_file.write_text(json.dumps(initial_store))

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        update_session_status("/workspace/repo_123", "status-04:plan-review")

        updated_store = json.loads(sessions_file.read_text())
        assert updated_store["last_updated"] != "old-timestamp"
