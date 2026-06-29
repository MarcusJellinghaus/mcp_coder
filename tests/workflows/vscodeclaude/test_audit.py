"""Tests for the persisted audit trail (``audit.py``).

One global file, one run-block per invocation, last-50 ring buffer, written only
by ``apply()`` runs. The serializer is the ONE shared
:meth:`SessionAssessment.to_audit_record`, so these tests assert delegation (not a
second flattening) and the ring-buffer / atomic-write discipline.
"""

import json
from pathlib import Path
from typing import Any

from mcp_coder.workflows.vscodeclaude.audit import (
    MAX_AUDIT_RUNS,
    append_run,
    assessment_to_record,
    get_audit_file_path,
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
)

_AUDIT_PATH = "mcp_coder.workflows.vscodeclaude.audit.get_audit_file_path"


def _session(
    folder: str = "C:/work/issue-38", issue_number: int = 38
) -> VSCodeClaudeSession:
    """A minimal session backing an audit record."""
    return VSCodeClaudeSession(
        folder=folder,
        repo="owner/repo",
        issue_number=issue_number,
        status="status-05:bot-pickup",
        vscode_pid=None,
        vscode_pid_create_time=None,
        started_at="2026-06-26T00:00:00",
        is_intervention=False,
        last_active=None,
        last_active_rule=None,
    )


def _assessment(
    *,
    folder: str = "C:/work/issue-38",
    active: bool = False,
    rule: LivenessRule = LivenessRule.NO_MATCH,
    action: SessionAction = SessionAction.DELETE,
    destructive: bool = True,
    reason: str = "stale (status-05:bot-pickup)",
) -> SessionAssessment:
    """A frozen SessionAssessment shaped for audit-record tests (defaults #38)."""
    signals = DetectionSignals(
        folder_exists=True,
        title_match=False,
        cmdline_match=False,
        pid_alive=False,
        found_pid=None,
        age_seconds=120.0,
        within_grace=False,
        directory_empty=False,
    )
    return SessionAssessment(
        folder=folder,
        signals=signals,
        verdict=LivenessVerdict(active=active, rule=rule),
        issue_state=IssueState(
            is_open=True,
            is_stale=True,
            is_blocked=False,
            is_unassigned=False,
            is_eligible=False,
            stale_target="status-05:bot-pickup",
        ),
        transition=Transition(flipped_to_inactive=False),
        decision=Decision(action=action, reason=reason, destructive=destructive),
        pid_needs_refresh=False,
        found_pid=None,
    )


class TestGetAuditFilePath:
    """The global audit file path (sibling of sessions.json)."""

    def test_filename_and_cache_dir(self) -> None:
        path = get_audit_file_path()
        assert path.name == "vscodeclaude_audit.json"
        assert path.parent.name == "coordinator_cache"


class TestAppendRun:
    """Ring-buffer append discipline."""

    def test_creates_file_and_parents(self, tmp_path: Path, monkeypatch: Any) -> None:
        """append_run mkdirs the parent and writes a single run-block."""
        audit_file = tmp_path / "nested" / "vscodeclaude_audit.json"
        monkeypatch.setattr(_AUDIT_PATH, lambda: audit_file)

        append_run([{"folder": "a"}])

        assert audit_file.exists()
        data = json.loads(audit_file.read_text(encoding="utf-8"))
        assert len(data["runs"]) == 1
        assert data["runs"][0]["records"] == [{"folder": "a"}]
        assert "run_at" in data["runs"][0]

    def test_ring_buffer_keeps_only_last_50(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Writing 51 runs trims to the newest 50 (ring buffer)."""
        audit_file = tmp_path / "vscodeclaude_audit.json"
        monkeypatch.setattr(_AUDIT_PATH, lambda: audit_file)

        for i in range(MAX_AUDIT_RUNS + 1):
            append_run([{"run_index": i}])

        data = json.loads(audit_file.read_text(encoding="utf-8"))
        assert len(data["runs"]) == MAX_AUDIT_RUNS
        # The very first run (index 0) was dropped; the newest (index 50) is kept.
        assert data["runs"][0]["records"] == [{"run_index": 1}]
        assert data["runs"][-1]["records"] == [{"run_index": MAX_AUDIT_RUNS}]

    def test_custom_max_runs(self, tmp_path: Path, monkeypatch: Any) -> None:
        """max_runs override controls the ring-buffer size."""
        audit_file = tmp_path / "vscodeclaude_audit.json"
        monkeypatch.setattr(_AUDIT_PATH, lambda: audit_file)

        for i in range(5):
            append_run([{"i": i}], max_runs=2)

        data = json.loads(audit_file.read_text(encoding="utf-8"))
        assert len(data["runs"]) == 2
        assert [r["records"][0]["i"] for r in data["runs"]] == [3, 4]

    def test_appends_to_existing_runs(self, tmp_path: Path, monkeypatch: Any) -> None:
        """A second append preserves earlier runs (newest last)."""
        audit_file = tmp_path / "vscodeclaude_audit.json"
        monkeypatch.setattr(_AUDIT_PATH, lambda: audit_file)

        append_run([{"folder": "a"}])
        append_run([{"folder": "b"}])

        data = json.loads(audit_file.read_text(encoding="utf-8"))
        assert [r["records"][0]["folder"] for r in data["runs"]] == ["a", "b"]

    def test_corrupt_file_resets_to_empty(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """A corrupt audit file is treated as empty rather than raising."""
        audit_file = tmp_path / "vscodeclaude_audit.json"
        audit_file.write_text("{not valid json", encoding="utf-8")
        monkeypatch.setattr(_AUDIT_PATH, lambda: audit_file)

        append_run([{"folder": "a"}])

        data = json.loads(audit_file.read_text(encoding="utf-8"))
        assert len(data["runs"]) == 1


class TestAssessmentToRecord:
    """The thin serializer wrapper delegating to to_audit_record."""

    def test_delegates_to_the_one_serializer(self) -> None:
        """assessment_to_record returns exactly assessment.to_audit_record(session)."""
        assessment = _assessment()
        session = _session()
        assert assessment_to_record(assessment, session) == assessment.to_audit_record(
            session
        )

    def test_38_shaped_record_is_greppable(self) -> None:
        """A #38-shaped record exposes rule=no_match/action=delete/destructive=true."""
        record = assessment_to_record(_assessment(), _session())
        assert record["verdict"]["rule"] == "no_match"
        assert record["decision"]["action"] == "delete"
        assert record["decision"]["destructive"] is True
        assert record["repo"] == "owner/repo"
        assert record["issue_number"] == 38
