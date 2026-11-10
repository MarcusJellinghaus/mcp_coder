"""Launch-time writers for a session on an untrusted issue body."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.detection import (
    DetectionSnapshot,
    _title_binds,
)
from mcp_coder.workflows.vscodeclaude.workspace import (
    create_startup_script,
    create_status_file,
    create_workspace_file,
)

WORKSPACE = "mcp_coder.workflows.vscodeclaude.workspace"
ISSUE_URL = "https://github.com/owner/repo/issues/123"


@pytest.fixture
def _windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the Windows launcher path (no MCP config file required)."""
    monkeypatch.setattr(f"{WORKSPACE}.platform.system", lambda: "Windows")


def _read_spec_json(folder: Path) -> dict[str, object]:
    spec: dict[str, object] = json.loads(
        (folder / ".vscodeclaude_session.json").read_text(encoding="utf-8")
    )
    return spec


@pytest.mark.usefixtures("_windows", "mock_vscodeclaude_config")
class TestStartupScriptUntrusted:
    """``create_startup_script`` records the flag and the blank title."""

    def test_untrusted_spec_has_blank_title_and_flag(self, tmp_path: Path) -> None:
        create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="",
            status="status-07:code-review",
            repo_name="repo",
            issue_url=ISSUE_URL,
            is_intervention=False,
            mcp_coder_install_path=tmp_path,
            untrusted_body=True,
        )
        spec = _read_spec_json(tmp_path)
        assert spec["title"] == ""
        assert spec["untrusted_body"] is True

    def test_default_is_trusted(self, tmp_path: Path) -> None:
        create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Add feature",
            status="status-07:code-review",
            repo_name="repo",
            issue_url=ISSUE_URL,
            is_intervention=False,
            mcp_coder_install_path=tmp_path,
        )
        spec = _read_spec_json(tmp_path)
        assert spec["title"] == "Add feature"
        assert spec["untrusted_body"] is False


@pytest.mark.usefixtures("mock_vscodeclaude_config")
class TestStatusFileUntrusted:
    """``create_status_file`` uses the untrusted template."""

    def _create(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        *,
        note: str | None = None,
        is_intervention: bool = False,
    ) -> str:
        monkeypatch.setattr(f"{WORKSPACE}._fetch_marked_comment", lambda *_args: note)
        create_status_file(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="",
            status="status-07:code-review",
            repo_full_name="owner/repo",
            branch_name="SECRET-BRANCH-123",
            issue_url=ISSUE_URL,
            is_intervention=is_intervention,
            untrusted_body=True,
        )
        return (tmp_path / ".vscodeclaude_status.txt").read_text(encoding="utf-8")

    def test_no_title_no_branch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        content = self._create(tmp_path, monkeypatch)
        assert "Issue #123" in content
        assert ISSUE_URL in content
        assert "Branch:" not in content
        assert "SECRET-BRANCH-123" not in content
        assert "Issue #123 -" not in content
        assert "INTERVENTION" not in content

    def test_note_still_appended(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        content = self._create(tmp_path, monkeypatch, note="## ❌ Failed\ndetail")
        assert "❌ Last automated note:" in content
        assert "## ❌ Failed\ndetail" in content

    def test_intervention_line_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        content = self._create(tmp_path, monkeypatch, is_intervention=True)
        assert "INTERVENTION" in content


@pytest.mark.usefixtures("mock_vscodeclaude_config")
def test_workspace_title_blank_still_detectable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A blank title keeps the ``[#N ... - repo`` shape detection relies on."""
    workspace_path = create_workspace_file(
        workspace_base=str(tmp_path),
        folder_name="repo_123",
        issue_number=123,
        issue_title="",
        status="status-07:code-review",
        repo_name="repo",
    )
    window_title = json.loads(workspace_path.read_text(encoding="utf-8"))["settings"][
        "window.title"
    ]
    assert window_title.startswith("[#123 ")
    assert window_title.endswith("- repo")

    monkeypatch.setattr("mcp_coder.workflows.vscodeclaude.detection.HAS_WIN32GUI", True)
    snapshot = DetectionSnapshot(
        processes=(),
        window_titles=((1, f"{window_title} - Visual Studio Code"),),
        pids=frozenset(),
        window_enum_ok=True,
        captured_at=datetime.now(UTC),
    )
    assert _title_binds(snapshot, 123, "owner/repo") is True
