"""SVG snapshot tests for iCoder TUI (Windows-only)."""

from __future__ import annotations

import sys
from collections.abc import Iterator
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


@pytest.fixture()
def icoder_app(tmp_path: Path) -> Iterator[ICoderApp]:
    """Create ICoderApp with FakeLLM; closes EventLog after the test."""
    fake_llm = FakeLLMService()
    event_log = EventLog(logs_dir=tmp_path)
    app_core = AppCore(llm_service=fake_llm, event_log=event_log)
    app = ICoderApp(app_core)
    yield app
    event_log.close()


def test_snapshot_initial_state(snap_compare: Any, icoder_app: ICoderApp) -> None:
    """Snapshot: app in initial empty state."""
    assert snap_compare(icoder_app)


def test_snapshot_after_help(snap_compare: Any, icoder_app: ICoderApp) -> None:
    """Snapshot: output after /help command."""

    async def send_help(pilot: Any) -> None:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/help")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

    assert snap_compare(icoder_app, run_before=send_help)


def test_snapshot_after_conversation(snap_compare: Any, icoder_app: ICoderApp) -> None:
    """Snapshot: output after a sample conversation exchange."""

    async def send_message(pilot: Any) -> None:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("What is Python?")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(delay=0.5)

    assert snap_compare(icoder_app, run_before=send_message)
