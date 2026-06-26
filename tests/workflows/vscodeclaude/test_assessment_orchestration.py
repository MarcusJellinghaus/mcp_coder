"""Tests for the assessment orchestration (build / apply / audit / logging).

``build_assessments`` is the READ-ONLY builder (snapshot once, no disk writes);
``apply_assessments`` is the single mutation point (PID refresh + last_active
advance + one atomic save, plus one audit run-block when write_audit=True).
"""

from unittest.mock import Mock, patch

from mcp_coder.workflows.vscodeclaude.assessment import (
    apply_assessments,
    assess_session,
    build_assessments,
)
from tests.workflows.vscodeclaude.conftest import (
    make_issue_facts,
    make_session_at,
    make_signals,
)

_SNAP = "mcp_coder.workflows.vscodeclaude.assessment.capture_detection_snapshot"
_GATHER = "mcp_coder.workflows.vscodeclaude.assessment.gather_signals"
_GIT_STATUS = "mcp_coder.workflows.vscodeclaude.assessment.get_folder_git_status"
_IGNORE = "mcp_coder.workflows.vscodeclaude.assessment.get_ignore_labels"
_USERNAME = "mcp_coder.workflows.vscodeclaude.assessment.get_github_username"
_LOAD = "mcp_coder.workflows.vscodeclaude.assessment.load_sessions"
_SAVE = "mcp_coder.workflows.vscodeclaude.assessment.save_sessions"
_CREATE_TIME = "mcp_coder.workflows.vscodeclaude.assessment.get_pid_create_time"
_AUDIT_PATH = "mcp_coder.workflows.vscodeclaude.audit.get_audit_file_path"


class TestBuildAssessments:
    """READ-ONLY builder: snapshot once, no disk writes, one entry per session."""

    @patch(_SAVE)
    @patch(_GIT_STATUS, return_value="Clean")
    @patch(_GATHER)
    @patch(_SNAP)
    @patch(_USERNAME, return_value="testuser")
    @patch(_IGNORE, return_value=set())
    def test_build_assessments_performs_no_disk_writes(
        self,
        mock_ignore: object,
        mock_username: object,
        mock_snap: object,
        mock_gather: Mock,
        mock_git: object,
        mock_save: Mock,
    ) -> None:
        """build_assessments never writes sessions.json (save_sessions untouched)."""
        mock_gather.return_value = make_signals(title_match=True, found_pid=7)
        sessions = [make_session_at("C:/work/a", 1)]

        result = build_assessments(sessions, cached_issues_by_repo=None)

        assert set(result) == {"C:/work/a"}
        assert result["C:/work/a"].verdict.active is True
        mock_save.assert_not_called()

    @patch(_SAVE)
    @patch(_GIT_STATUS, return_value="Clean")
    @patch(_GATHER)
    @patch(_SNAP)
    @patch(_USERNAME, return_value="testuser")
    @patch(_IGNORE, return_value=set())
    def test_snapshot_captured_exactly_once_per_call(
        self,
        mock_ignore: object,
        mock_username: object,
        mock_snap: Mock,
        mock_gather: Mock,
        mock_git: object,
        mock_save: object,
    ) -> None:
        """One DetectionSnapshot per build (R4), gathered once per session."""
        mock_gather.return_value = make_signals()
        sessions = [
            make_session_at("C:/work/a", 1),
            make_session_at("C:/work/b", 2),
            make_session_at("C:/work/c", 3),
        ]

        result = build_assessments(sessions)

        assert mock_snap.call_count == 1
        assert mock_gather.call_count == len(sessions)
        assert set(result) == {"C:/work/a", "C:/work/b", "C:/work/c"}


class TestApplyAssessments:
    """Apply-only mutation point: PID refresh + last_active advance, single save."""

    @patch(_CREATE_TIME, return_value=123.5)
    @patch(_SAVE)
    @patch(_LOAD)
    def test_apply_advances_last_active_and_refreshes_pid_once(
        self,
        mock_load: Mock,
        mock_save: Mock,
        mock_ct: Mock,
    ) -> None:
        """An active session refreshes the stale PID and advances last_active."""
        session = make_session_at("C:/work/a", 1)
        session["vscode_pid"] = 100
        mock_load.return_value = {"sessions": [session], "last_updated": ""}

        assessment = assess_session(
            folder="C:/work/a",
            signals=make_signals(title_match=True, found_pid=200),
            issue_facts=make_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )

        apply_assessments({"C:/work/a": assessment}, write_audit=False)

        saved_store = mock_save.call_args[0][0]
        saved = saved_store["sessions"][0]
        assert saved["vscode_pid"] == 200
        assert saved["vscode_pid_create_time"] == 123.5
        assert saved["last_active"] is True
        assert saved["last_active_rule"] == "title"
        mock_ct.assert_called_once_with(200)
        mock_save.assert_called_once()

    @patch(_CREATE_TIME)
    @patch(_SAVE)
    @patch(_LOAD)
    def test_apply_inactive_skips_pid_refresh(
        self,
        mock_load: Mock,
        mock_save: Mock,
        mock_ct: Mock,
    ) -> None:
        """An inactive session advances last_active to False without touching PID."""
        session = make_session_at("C:/work/a", 1)
        session["vscode_pid"] = 100
        mock_load.return_value = {"sessions": [session], "last_updated": ""}

        assessment = assess_session(
            folder="C:/work/a",
            signals=make_signals(folder_exists=True),  # all miss -> INACTIVE(NO_MATCH)
            issue_facts=make_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=True,
        )

        apply_assessments({"C:/work/a": assessment}, write_audit=False)

        saved = mock_save.call_args[0][0]["sessions"][0]
        assert saved["vscode_pid"] == 100  # unchanged
        assert saved["last_active"] is False
        assert saved["last_active_rule"] == "no_match"
        mock_ct.assert_not_called()
        mock_save.assert_called_once()


class TestApplyAssessmentsAudit:
    """apply_assessments writes ONE run-block per invocation when write_audit=True."""

    @patch(_CREATE_TIME)
    @patch(_SAVE)
    @patch(_LOAD)
    def test_apply_writes_one_record_per_session(
        self,
        mock_load: Mock,
        mock_save: Mock,
        mock_ct: Mock,
        tmp_path: object,
        monkeypatch: object,
    ) -> None:
        """write_audit=True appends one run-block with one record per session."""
        import json as _json
        from pathlib import Path as _Path

        audit_file = _Path(str(tmp_path)) / "vscodeclaude_audit.json"
        monkeypatch.setattr(_AUDIT_PATH, lambda: audit_file)  # type: ignore[attr-defined]

        session_a = make_session_at("C:/work/a", 1)
        session_b = make_session_at("C:/work/b", 38)
        mock_load.return_value = {
            "sessions": [session_a, session_b],
            "last_updated": "",
        }

        active = assess_session(
            folder="C:/work/a",
            signals=make_signals(title_match=True),
            issue_facts=make_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )
        # #38-shaped: inactive + stale + clean -> destructive DELETE.
        deleting = assess_session(
            folder="C:/work/b",
            signals=make_signals(folder_exists=True),
            issue_facts=make_issue_facts(
                is_stale=True, stale_target="status-05:bot-pickup"
            ),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )

        apply_assessments(
            {"C:/work/a": active, "C:/work/b": deleting}, write_audit=True
        )

        data = _json.loads(audit_file.read_text(encoding="utf-8"))
        assert len(data["runs"]) == 1
        records = data["runs"][0]["records"]
        assert len(records) == 2
        # The #38-shaped record is greppable as a one-glance post-mortem.
        deletes = [r for r in records if r["decision"]["action"] == "delete"]
        assert len(deletes) == 1
        assert deletes[0]["verdict"]["rule"] == "no_match"
        assert deletes[0]["decision"]["destructive"] is True
        assert deletes[0]["issue_number"] == 38

    @patch(_CREATE_TIME)
    @patch(_SAVE)
    @patch(_LOAD)
    def test_status_path_writes_no_audit_record(
        self,
        mock_load: Mock,
        mock_save: Mock,
        mock_ct: Mock,
        tmp_path: object,
        monkeypatch: object,
    ) -> None:
        """write_audit=False (the status path never calls apply) leaves no file."""
        from pathlib import Path as _Path

        audit_file = _Path(str(tmp_path)) / "vscodeclaude_audit.json"
        monkeypatch.setattr(_AUDIT_PATH, lambda: audit_file)  # type: ignore[attr-defined]

        session = make_session_at("C:/work/a", 1)
        mock_load.return_value = {"sessions": [session], "last_updated": ""}

        assessment = assess_session(
            folder="C:/work/a",
            signals=make_signals(title_match=True),
            issue_facts=make_issue_facts(),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )

        apply_assessments({"C:/work/a": assessment}, write_audit=False)

        assert not audit_file.exists()

    @patch(_CREATE_TIME)
    @patch(_SAVE)
    @patch(_LOAD)
    def test_locked_folder_retry_recurs_across_runs(
        self,
        mock_load: Mock,
        mock_save: Mock,
        mock_ct: Mock,
        tmp_path: object,
        monkeypatch: object,
    ) -> None:
        """A still-stale session recurs as a delete record across consecutive runs."""
        import json as _json
        from pathlib import Path as _Path

        audit_file = _Path(str(tmp_path)) / "vscodeclaude_audit.json"
        monkeypatch.setattr(_AUDIT_PATH, lambda: audit_file)  # type: ignore[attr-defined]

        session = make_session_at("C:/work/b", 38)
        mock_load.return_value = {"sessions": [session], "last_updated": ""}

        deleting = assess_session(
            folder="C:/work/b",
            signals=make_signals(folder_exists=True),
            issue_facts=make_issue_facts(
                is_stale=True, stale_target="status-05:bot-pickup"
            ),
            git_status="Clean",
            directory_empty=False,
            prior_last_active=None,
        )

        apply_assessments({"C:/work/b": deleting}, write_audit=True)
        apply_assessments({"C:/work/b": deleting}, write_audit=True)

        data = _json.loads(audit_file.read_text(encoding="utf-8"))
        assert len(data["runs"]) == 2
        for run in data["runs"]:
            assert run["records"][0]["decision"]["action"] == "delete"
            assert run["records"][0]["issue_number"] == 38


class TestBuildAssessmentsLogging:
    """Decision + transition logging emitted by build_assessments."""

    @patch(_SAVE)
    @patch(_GIT_STATUS, return_value="Clean")
    @patch(_GATHER)
    @patch(_SNAP)
    @patch(_USERNAME, return_value="testuser")
    @patch(_IGNORE, return_value=set())
    def test_transition_log_on_true_flip(
        self,
        mock_ignore: object,
        mock_username: object,
        mock_snap: object,
        mock_gather: Mock,
        mock_git: object,
        mock_save: object,
        caplog: object,
    ) -> None:
        """A prior-active session now inactive logs the active->inactive flip."""
        import logging as _logging

        mock_gather.return_value = make_signals(folder_exists=True)  # miss -> inactive
        session = make_session_at("C:/work/a", 1)
        session["last_active"] = True
        session["last_active_rule"] = "title"

        with caplog.at_level(_logging.INFO):  # type: ignore[attr-defined]
            build_assessments([session])

        assert "flipped active->inactive" in caplog.text  # type: ignore[attr-defined]
        assert "was rule=title" in caplog.text  # type: ignore[attr-defined]

    @patch(_SAVE)
    @patch(_GIT_STATUS, return_value="Clean")
    @patch(_GATHER)
    @patch(_SNAP)
    @patch(_USERNAME, return_value="testuser")
    @patch(_IGNORE, return_value=set())
    def test_no_transition_log_on_none_prior(
        self,
        mock_ignore: object,
        mock_username: object,
        mock_snap: object,
        mock_gather: Mock,
        mock_git: object,
        mock_save: object,
        caplog: object,
    ) -> None:
        """A None prior baseline is a blind spot, never logged as a flip."""
        import logging as _logging

        mock_gather.return_value = make_signals(folder_exists=True)  # miss -> inactive
        session = make_session_at("C:/work/a", 1)
        session["last_active"] = None

        with caplog.at_level(_logging.INFO):  # type: ignore[attr-defined]
            build_assessments([session])

        assert "flipped active->inactive" not in caplog.text  # type: ignore[attr-defined]

    @patch(_SAVE)
    @patch(_GIT_STATUS, return_value="Clean")
    @patch(_GATHER)
    @patch(_SNAP)
    @patch(_USERNAME, return_value="testuser")
    @patch(_IGNORE, return_value=set())
    def test_decision_line_logged(
        self,
        mock_ignore: object,
        mock_username: object,
        mock_snap: object,
        mock_gather: Mock,
        mock_git: object,
        mock_save: object,
        caplog: object,
    ) -> None:
        """Each assessed session logs a one-glance verdict/action decision line."""
        import logging as _logging

        mock_gather.return_value = make_signals(title_match=True)
        session = make_session_at("C:/work/a", 1)

        with caplog.at_level(_logging.INFO):  # type: ignore[attr-defined]
            build_assessments([session])

        assert "assess #1" in caplog.text  # type: ignore[attr-defined]
        assert "rule=title" in caplog.text  # type: ignore[attr-defined]
        assert "action=keep_active" in caplog.text  # type: ignore[attr-defined]
