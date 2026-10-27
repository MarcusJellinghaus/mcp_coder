from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from textual.pilot import Pilot

from mcp_coder.icoder.permissions.approval import ApprovalDecision, ApprovalEngine
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.approval_modal import ApprovalModal
from mcp_coder.llm.types import StreamEvent

_APPROVAL_TOOL = "mcp__srv__do_it"


def _approval_event(
    approval_id: str = "a1", tool_name: str = _APPROVAL_TOOL
) -> StreamEvent:
    """Build the ``approval_request`` event the engine would emit for the tool."""
    return {
        "type": "approval_request",
        "approval_id": approval_id,
        "tool_name": tool_name,
        "args": {"path": "a.txt"},
        "source": "project",
    }


class _RecordingEngine(ApprovalEngine):
    """Engine stub recording what the UI sends it (subclassed, so the type holds)."""

    def __init__(self) -> None:
        super().__init__()
        self.resolved: list[tuple[str, ApprovalDecision]] = []
        self.cancel_calls = 0

    def resolve_pending(self, approval_id: str, decision: ApprovalDecision) -> None:
        self.resolved.append((approval_id, decision))

    def cancel_all(self) -> None:
        self.cancel_calls += 1


def _isolate_user_layer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the ``user`` layer at an empty dir under ``tmp_path``.

    ``_discover_layers`` reads a real machine path otherwise, so any
    ``load_permission_config(tmp_path)`` assertion would be environment-bound.
    """
    user_root = tmp_path / "user"
    user_root.mkdir(exist_ok=True)
    monkeypatch.setattr(
        "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
        lambda _app: user_root,
    )


def _author_project_ask(tmp_path: Path) -> None:
    """Write a ``project`` layer that gates the approval tool on ``ask``."""
    icoder = tmp_path / ".icoder"
    icoder.mkdir(exist_ok=True)
    (icoder / "settings.json").write_text(
        json.dumps({"ask": [_APPROVAL_TOOL]}), encoding="utf-8"
    )


async def _open_modal_and_press(
    app: ICoderApp,
    pilot: Pilot[Any],
    key: str,
    tool_name: str = _APPROVAL_TOOL,
) -> None:
    """Push the modal through the stream branch, then press ``key`` on it."""
    await pilot.pause()
    app._handle_stream_event(_approval_event(tool_name=tool_name))
    await pilot.pause()
    assert isinstance(app.screen, ApprovalModal)
    await pilot.press(key)
    await pilot.pause()
