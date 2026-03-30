"""SVG snapshot tests for iCoder TUI (Windows-only)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.input_area import InputArea

pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="Snapshot tests are Windows-only to avoid baseline drift",
)


def _create_app(tmp_path: Path) -> ICoderApp:
    """Create ICoderApp with FakeLLM for deterministic snapshots."""
    fake_llm = FakeLLMService()
    event_log = EventLog(logs_dir=tmp_path)
    app_core = AppCore(llm_service=fake_llm, event_log=event_log)
    return ICoderApp(app_core)


def test_snapshot_initial_state(snap_compare: Any, tmp_path: Path) -> None:
    """Snapshot: app in initial empty state."""
    app = _create_app(tmp_path)
    assert snap_compare(app)


def test_snapshot_after_help(snap_compare: Any, tmp_path: Path) -> None:
    """Snapshot: output after /help command."""
    app = _create_app(tmp_path)

    async def send_help(pilot: Any) -> None:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/help")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

    assert snap_compare(app, run_before=send_help)


def test_snapshot_after_conversation(snap_compare: Any, tmp_path: Path) -> None:
    """Snapshot: output after a sample conversation exchange."""
    app = _create_app(tmp_path)

    async def send_message(pilot: Any) -> None:
        input_area = app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("What is Python?")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(delay=0.5)

    assert snap_compare(app, run_before=send_message)
