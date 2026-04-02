"""SVG snapshot tests for iCoder TUI (Windows-only).

Snapshot tests compare rendered TUI output against golden SVG baselines
stored in __snapshots__/. When the UI changes intentionally, regenerate
baselines with:

    pytest tests/icoder/test_snapshots.py --snapshot-update

Baselines are Windows-only to avoid cross-platform rendering drift.
Verify regenerated SVGs contain no secrets, env vars, or local paths.
"""

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

pytestmark = [
    pytest.mark.skipif(
        sys.platform != "win32",
        reason="Snapshot tests are Windows-only to avoid baseline drift",
    ),
    pytest.mark.textual_integration,
]


@pytest.fixture()
def icoder_app(tmp_path: Path) -> Iterator[ICoderApp]:
    """Create ICoderApp with FakeLLM; uses context manager for EventLog."""
    fake_llm = FakeLLMService()
    with EventLog(logs_dir=tmp_path) as event_log:
        app_core = AppCore(llm_service=fake_llm, event_log=event_log)
        yield ICoderApp(app_core)


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


def test_snapshot_long_line_wraps(snap_compare: Any, icoder_app: ICoderApp) -> None:
    """Snapshot: long user message wraps instead of scrolling horizontally."""

    async def send_long_message(pilot: Any) -> None:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert(
            "This is a very long message that should wrap across multiple"
            " lines in the output log instead of requiring horizontal"
            " scrolling to read the content"
        )
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(delay=0.5)

    assert snap_compare(icoder_app, run_before=send_long_message)


def test_snapshot_input_area_grows(snap_compare: Any, icoder_app: ICoderApp) -> None:
    """Snapshot: input area grows taller as multi-line text is inserted."""

    async def insert_multiline(pilot: Any) -> None:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("line1\nline2\nline3\nline4\nline5")
        await pilot.pause()

    assert snap_compare(icoder_app, run_before=insert_multiline)
