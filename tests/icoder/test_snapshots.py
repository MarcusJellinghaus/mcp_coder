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
import time
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.commands.display import register_display
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.input_area import InputArea

_TOOL_RESPONSE: list[list[dict[str, object]]] = [
    [
        {"type": "text_delta", "text": "Let me read the file.\n"},
        {
            "type": "tool_use_start",
            "name": "mcp__mcp-workspace__read_file",
            "args": {"file_path": "src/main.py"},
        },
        {
            "type": "tool_result",
            "name": "mcp__mcp-workspace__read_file",
            "output": "def main():\n    print('hello')\n    return 0",
        },
        {"type": "done"},
    ]
]

pytestmark = [
    pytest.mark.skipif(
        sys.platform != "win32",
        reason="Snapshot tests are Windows-only to avoid baseline drift",
    ),
    pytest.mark.textual_integration,
]


class _FixedDatetime(datetime):
    """``datetime`` subclass with a frozen ``now()`` for stable snapshots.

    The detail modal footer renders a unit's wall-clock timestamp, which is
    captured via ``datetime.now()`` at unit creation. Freezing it keeps the
    modal snapshot deterministic (mirrors ``_test_runtime_info`` pinning
    versions for the same reason).
    """

    @classmethod
    def now(cls, tz: Any = None) -> "_FixedDatetime":
        return cls(2026, 1, 1, 12, 0, 0)


class _FrozenClock:
    """Pin ``stream_renderer``'s monotonic clock so tool durations render
    as a constant ``0ms`` (the wall-clock analogue of ``_FixedDatetime``).

    The renderer reads ``time.monotonic()`` at tool start and at tool result
    to compute ``duration_ms``; pinning it removes that timing jitter from
    the snapshot. Non-``monotonic`` attribute access delegates to the real
    ``time`` module so nothing else in the renderer breaks.
    """

    @staticmethod
    def monotonic() -> float:
        return 1000.0

    def __getattr__(self, name: str) -> Any:
        return getattr(time, name)


@pytest.fixture(autouse=True)
def _freeze_dynamic_ui(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neutralize time-driven UI motion so snapshots are deterministic.

    Two independent runtime-variable sources are frozen here:

    1. **Branch-info polling.** ``ICoderApp.on_mount`` kicks off git/gh polling
       for the bottom ``BranchInfoBar``: it calls
       ``run_worker(self._tick_branch_full, ...)`` once and registers
       ``set_interval`` timers for ``_tick_branch_quick`` /
       ``_tick_branch_full``. Those worker threads later call
       ``BranchInfoBar.update_state(view)``, mutating the bottom bar at a
       nondeterministic point. Tests that ``pilot.pause(delay=0.5)`` give the
       workers time to fire, so the bar text varies run-to-run.

    2. **Input cursor blink.** ``InputArea`` (a ``TextArea``) has a blinking
       text cursor driven by an internal timer. With the input focused, the
       0.5s pauses land the blink at a nondeterministic phase, so the cursor
       cell flips between drawn and blank between runs.

    Freezing the bar at its deterministic initial placeholder (the
    ``update_state(None)`` state set in ``on_mount``) requires neutralizing
    every path that can populate ``_last_branch_info`` without user
    interaction:

    * the two tick methods (``on_mount`` calls ``run_worker(_tick_branch_full)``
      once and registers ``set_interval`` timers for both),
    * the two worker bodies they spawn, and
    * the ``BranchInfoService`` data-layer fetches the workers call.

    Patching all three layers makes the branch freeze robust regardless of
    thread scheduling: even if a worker thread is already in flight when a
    patch is applied, the fetch it performs reaches the bar only via methods
    that are now no-ops, so the bar can never advance past the ``… … … …``
    placeholder. The cursor blink is disabled by forcing ``cursor_blink`` off
    on ``InputArea`` so the cursor cell is always drawn.

    Autouse so it applies to ALL snapshot tests (mirrors the intent of
    ``_frozen_clocks``, which freezes the wall-clock/monotonic sources).
    """
    monkeypatch.setattr(ICoderApp, "_tick_branch_full", lambda self: None)
    monkeypatch.setattr(ICoderApp, "_tick_branch_quick", lambda self: None)
    monkeypatch.setattr(ICoderApp, "_branch_full_work", lambda self: None)
    monkeypatch.setattr(ICoderApp, "_branch_quick_work", lambda self: None)
    monkeypatch.setattr(ICoderApp, "_render_branch_state", lambda self: None)
    monkeypatch.setattr(InputArea, "cursor_blink", False)


@pytest.fixture()
def _frozen_clocks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Freeze wall-clock and monotonic sources for deterministic snapshots.

    Tool tiers render ``duration_ms`` and the modal footer renders a
    wall-clock timestamp; both are runtime-variable. Pinning them keeps the
    rendered SVG stable across runs and environments.
    """
    monkeypatch.setattr("mcp_coder.icoder.ui.app.datetime", _FixedDatetime)
    monkeypatch.setattr("mcp_coder.llm.formatting.stream_renderer.time", _FrozenClock())


def _test_runtime_info() -> RuntimeInfo:
    """Return RuntimeInfo with fixed version for stable snapshots."""
    return RuntimeInfo(
        mcp_coder_version="0.0.0-test",
        mcp_coder_utils_version="0.0.0-test",
        python_version="3.12.0",
        claude_code_version="0.0.0",
        tool_env_path="/test/tool",
        project_venv_path="/test/.venv",
        project_dir="/test/project",
        env_vars={},
        mcp_servers=[],
    )


@pytest.fixture()
def icoder_app(tmp_path: Path) -> Iterator[ICoderApp]:
    """Create ICoderApp with FakeLLM; uses context manager for EventLog."""
    fake_llm = FakeLLMService()
    with EventLog(logs_dir=tmp_path) as event_log:
        app_core = AppCore(
            llm_service=fake_llm,
            event_log=event_log,
            runtime_info=_test_runtime_info(),
        )
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


def test_snapshot_autocomplete_all_commands(
    snap_compare: Any, icoder_app: ICoderApp
) -> None:
    """Snapshot: dropdown visible with all commands (user typed '/')."""

    async def type_slash(pilot: Any) -> None:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/")
        await pilot.pause()

    assert snap_compare(icoder_app, run_before=type_slash)


def test_snapshot_autocomplete_filtered(
    snap_compare: Any, icoder_app: ICoderApp
) -> None:
    """Snapshot: dropdown filtered to single match (user typed '/he')."""

    async def type_prefix(pilot: Any) -> None:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/he")
        await pilot.pause()

    assert snap_compare(icoder_app, run_before=type_prefix)


def test_snapshot_autocomplete_no_match(
    snap_compare: Any, icoder_app: ICoderApp
) -> None:
    """Snapshot: dropdown showing '(no matching commands)' (user typed '/xyz')."""

    async def type_bad_prefix(pilot: Any) -> None:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/xyz")
        await pilot.pause()

    assert snap_compare(icoder_app, run_before=type_bad_prefix)


def test_snapshot_default_tier(
    snap_compare: Any, tmp_path: Path, _frozen_clocks: None
) -> None:
    """Snapshot: a completed tool block in the default (compressed) tier."""
    fake_llm = FakeLLMService(responses=_TOOL_RESPONSE)
    with EventLog(logs_dir=tmp_path) as event_log:
        app_core = AppCore(
            llm_service=fake_llm,
            event_log=event_log,
            runtime_info=_test_runtime_info(),
        )
        register_display(app_core.registry, app_core)
        app = ICoderApp(app_core)

        async def run(pilot: Any) -> None:
            input_area = app.query_one(InputArea)
            input_area.focus()
            await pilot.pause()
            input_area.insert("read main")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause(delay=0.5)

        assert snap_compare(app, run_before=run)


def test_snapshot_after_display_oneline(
    snap_compare: Any, tmp_path: Path, _frozen_clocks: None
) -> None:
    """Snapshot: the same tool block after /display oneline (tier-1)."""
    fake_llm = FakeLLMService(responses=_TOOL_RESPONSE)
    with EventLog(logs_dir=tmp_path) as event_log:
        app_core = AppCore(
            llm_service=fake_llm,
            event_log=event_log,
            runtime_info=_test_runtime_info(),
        )
        register_display(app_core.registry, app_core)
        app = ICoderApp(app_core)

        async def run(pilot: Any) -> None:
            input_area = app.query_one(InputArea)
            input_area.focus()
            await pilot.pause()
            input_area.insert("read main")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause(delay=0.5)
            input_area.insert("/display oneline")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

        assert snap_compare(app, run_before=run)


def test_snapshot_modal_over_tool(
    snap_compare: Any, tmp_path: Path, _frozen_clocks: None
) -> None:
    """Snapshot: the detail modal opened (F2) over a tool block."""
    fake_llm = FakeLLMService(responses=_TOOL_RESPONSE)
    with EventLog(logs_dir=tmp_path) as event_log:
        app_core = AppCore(
            llm_service=fake_llm,
            event_log=event_log,
            runtime_info=_test_runtime_info(),
        )
        register_display(app_core.registry, app_core)
        app = ICoderApp(app_core)

        async def run(pilot: Any) -> None:
            input_area = app.query_one(InputArea)
            input_area.focus()
            await pilot.pause()
            input_area.insert("read main")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause(delay=0.5)
            await pilot.press("f2")
            await pilot.pause()

        assert snap_compare(app, run_before=run)


def test_snapshot_multi_chunk_streaming(snap_compare: Any, tmp_path: Path) -> None:
    """Snapshot: multi-chunk streaming response with line breaks."""
    responses: list[list[dict[str, object]]] = [
        [
            {"type": "text_delta", "text": "Hello "},
            {"type": "text_delta", "text": "world!\n"},
            {"type": "text_delta", "text": "Second line."},
            {"type": "done"},
        ]
    ]
    fake_llm = FakeLLMService(responses=responses)
    with EventLog(logs_dir=tmp_path) as event_log:
        app_core = AppCore(
            llm_service=fake_llm,
            event_log=event_log,
            runtime_info=_test_runtime_info(),
        )
        app = ICoderApp(app_core)

        async def send_message(pilot: Any) -> None:
            input_area = app.query_one(InputArea)
            input_area.focus()
            await pilot.pause()
            input_area.insert("test streaming")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause(delay=0.5)

        assert snap_compare(app, run_before=send_message)
