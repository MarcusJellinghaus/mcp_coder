"""Round-trip tests for SessionSpec write/read helpers."""

import json
from pathlib import Path

from mcp_coder.workflows.vscodeclaude.types import (
    SESSION_SPEC_FILENAME,
    SessionSpec,
    read_session_spec,
    write_session_spec,
)


def _make_spec(commands: list[str]) -> SessionSpec:
    return SessionSpec(
        issue_number=123,
        title="Fix the bug",
        repo="owner/repo",
        status="status-07:code-review",
        issue_url="https://github.com/owner/repo/issues/123",
        emoji="🔧",
        commands=commands,
        timeout=300,
        mcp_config=".mcp.json",
        install_script_path="/coord/tools/install.py",
        mcp_coder_install_path="/coord",
        skip_github_install=False,
        is_intervention=False,
    )


class TestSessionSpecRoundTrip:
    """SessionSpec survives write_session_spec -> read_session_spec unchanged."""

    def test_round_trip_multi_commands(self, tmp_path: Path) -> None:
        """A multi-command spec round-trips exactly."""
        spec = _make_spec(["mcp-coder implement", "mcp-coder commit"])
        write_session_spec(tmp_path, spec)
        assert read_session_spec(tmp_path) == spec

    def test_round_trip_empty_commands(self, tmp_path: Path) -> None:
        """A spec with no commands round-trips exactly."""
        spec = _make_spec([])
        write_session_spec(tmp_path, spec)
        loaded = read_session_spec(tmp_path)
        assert loaded == spec
        assert loaded.commands == []

    def test_round_trip_single_command(self, tmp_path: Path) -> None:
        """A single-command spec round-trips exactly."""
        spec = _make_spec(["mcp-coder implement"])
        write_session_spec(tmp_path, spec)
        assert read_session_spec(tmp_path) == spec

    def test_round_trip_intervention_and_skip_flags(self, tmp_path: Path) -> None:
        """Both boolean flags round-trip as True."""
        spec = SessionSpec(
            issue_number=1,
            title="Intervene",
            repo="owner/repo",
            status="status-99:blocked",
            issue_url="https://github.com/owner/repo/issues/1",
            emoji="⚠️",
            commands=[],
            timeout=600,
            mcp_config=".mcp.linux.json",
            install_script_path="/coord/tools/install.py",
            mcp_coder_install_path="/coord",
            skip_github_install=True,
            is_intervention=True,
        )
        write_session_spec(tmp_path, spec)
        loaded = read_session_spec(tmp_path)
        assert loaded == spec
        assert loaded.skip_github_install is True
        assert loaded.is_intervention is True


class TestSessionSpecFile:
    """The persisted file has the expected name and holds valid JSON."""

    def test_write_returns_expected_path(self, tmp_path: Path) -> None:
        """write_session_spec returns the path to the named JSON file."""
        spec = _make_spec(["cmd"])
        path = write_session_spec(tmp_path, spec)
        assert path == tmp_path / SESSION_SPEC_FILENAME
        assert path.name == ".vscodeclaude_session.json"

    def test_file_contains_valid_json(self, tmp_path: Path) -> None:
        """The written file parses as JSON with the spec's fields."""
        spec = _make_spec(["cmd"])
        path = write_session_spec(tmp_path, spec)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["issue_number"] == 123
        assert data["commands"] == ["cmd"]
        assert data["mcp_config"] == ".mcp.json"
