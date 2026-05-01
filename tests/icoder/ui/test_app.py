"""End-to-end pipeline tests for tool output visibility in ICoderApp."""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from unittest.mock import patch

import pytest
from textual.widgets import Static

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.services.branch_info_service import BranchInfoService
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.branch_info_bar import BranchInfoBar
from mcp_coder.icoder.ui.widgets.busy_indicator import BusyIndicator
from mcp_coder.icoder.ui.widgets.output_log import OutputLog
from mcp_coder.llm.types import StreamEvent
from mcp_coder.services.branch_info import BranchInfo

pytestmark = pytest.mark.textual_integration


@pytest.fixture
def make_icoder_app(
    event_log: EventLog,
) -> Callable[..., ICoderApp]:
    """Factory to create ICoderApp with custom FakeLLM responses."""

    def _factory(
        *,
        responses: list[list[StreamEvent]] | None = None,
        runtime_info: RuntimeInfo | None = None,
    ) -> ICoderApp:
        llm = FakeLLMService(responses=responses or [])
        return ICoderApp(
            AppCore(
                llm_service=llm,
                event_log=event_log,
                runtime_info=runtime_info,
            ),
        )

    return _factory


async def test_tool_output_list_directory(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """List directory tool output lines appear in recorded output."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__workspace__list_directory",
                "args": {},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__workspace__list_directory",
                "output": '{"result": ["file1.py", "file2.py", "src/"]}',
            }
        )
        lines = app.query_one(OutputLog).recorded_lines
        joined = "\n".join(lines)
        assert "file1.py" in joined
        assert "file2.py" in joined
        assert "src/" in joined
        assert "└ done" in joined


async def test_tool_output_read_file(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Read file tool output lines appear in recorded output."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__workspace__read_file",
                "output": '{"result": "line1\\nline2\\nline3"}',
            }
        )
        lines = app.query_one(OutputLog).recorded_lines
        joined = "\n".join(lines)
        assert "line1" in joined
        assert "line2" in joined
        assert "line3" in joined
        assert "└ done" in joined


async def test_tool_output_truncated(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Truncated tool output shows truncation marker."""
    long_content = "\\n".join(f"line{i}" for i in range(30))
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__workspace__read_file",
                "args": {"file_path": "big.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__workspace__read_file",
                "output": '{"result": "' + long_content + '"}',
            }
        )
        lines = app.query_one(OutputLog).recorded_lines
        joined = "\n".join(lines)
        assert "truncated" in joined
        assert "skipped" in joined


async def test_tool_output_empty(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Empty tool output still shows done footer."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__workspace__read_file",
                "args": {"file_path": "empty.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__workspace__read_file",
                "output": "",
            }
        )
        lines = app.query_one(OutputLog).recorded_lines
        joined = "\n".join(lines)
        assert "└ done" in joined


async def test_busy_indicator_thinking_after_tool_result(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Busy indicator shows 'Thinking about ...' after tool result is rendered."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app._handle_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__workspace__read_file",
                "output": '{"result": "hello"}',
            }
        )
        indicator = app.query_one(BusyIndicator)
        assert "Thinking about workspace > read_file..." in indicator.label_text


async def test_banner_renders_mcp_coder_utils_version(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """on_mount banner includes the mcp-coder-utils version line."""
    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir="/tmp/proj",
        env_vars={},
        mcp_servers=[],
    )
    app = make_icoder_app(responses=[], runtime_info=runtime_info)
    async with app.run_test() as pilot:
        await pilot.pause()
        joined = "\n".join(app.query_one(OutputLog).recorded_lines)
        assert any(
            line.startswith("mcp-coder-utils 1.2.3") for line in joined.splitlines()
        ), joined


async def test_busy_indicator_resets_on_error_only_stream(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Busy indicator shows ready after stream yields only an error event (no done)."""
    error_only: list[list[StreamEvent]] = [
        [{"type": "error", "message": "something went wrong"}],
    ]
    app = make_icoder_app(responses=error_only)
    async with app.run_test() as pilot:
        # Type input and press enter to trigger _stream_llm
        await pilot.press("h", "i")
        await pilot.press("enter")
        # Allow the background worker to finish
        await pilot.pause(delay=0.5)
        indicator = app.query_one(BusyIndicator)
        assert indicator.label_text == "✓ Ready"


# ---------------------------------------------------------------------------
# BranchInfoBar integration tests (Step 4)
# ---------------------------------------------------------------------------


def _make_branch_info(
    *,
    branch: Optional[str] = "main",
    is_dirty: bool = False,
    issue_number: Optional[int] = None,
    issue_title: Optional[str] = None,
    status_label: Optional[str] = None,
) -> BranchInfo:
    return BranchInfo(
        is_git_repo=True,
        branch_name=branch,
        is_dirty=is_dirty,
        issue_number=issue_number,
        issue_title=issue_title,
        issue_status_label=status_label,
        cache_last_checked=datetime.now(tz=timezone.utc),
    )


def _branch_zone(app: ICoderApp, zone: str) -> str:
    bar = app.query_one(BranchInfoBar)
    widget = bar.query_one(f"#branch-info-{zone}", Static)
    return str(widget.render())


async def test_branch_info_bar_present_in_compose(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """BranchInfoBar is composed into the app and queryable."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    with patch.object(
        BranchInfoService, "fetch_info", return_value=_make_branch_info()
    ):
        async with app.run_test() as pilot:
            await pilot.pause()
            bar = app.query_one(BranchInfoBar)
            assert bar is not None


async def test_initial_state_renders_loading_placeholder(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Before workers complete, the bar shows the '…' placeholder."""
    block = threading.Event()

    def slow_fetch(self: BranchInfoService) -> BranchInfo:
        block.wait(timeout=5)
        return _make_branch_info()

    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    with patch.object(BranchInfoService, "fetch_info", slow_fetch):
        async with app.run_test() as pilot:
            await pilot.pause()
            assert _branch_zone(app, "branch") == "…"
            block.set()
            await pilot.pause(delay=0.3)


async def test_refresh_issue_button_triggers_state_update(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Clicking the refresh-issue button updates the rendered branch zone."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="123-foo", issue_number=123, issue_title="Foo")
    with patch.object(BranchInfoService, "fetch_info", return_value=info):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            await pilot.click("#branch-refresh-issue")
            await pilot.pause(delay=0.3)
            assert "123-foo" in _branch_zone(app, "branch")


async def test_pr_button_disabled_off_dashes_pr_zone(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """With PR toggle off, the PR zone renders '—'."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="42-x", issue_number=42, issue_title="t")
    with patch.object(BranchInfoService, "fetch_info", return_value=info):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            assert _branch_zone(app, "pr") == "—"


async def test_toggle_pr_enables_lookup(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Clicking PR toggle flips the service flag and triggers a PR fetch."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="42-x", issue_number=42, issue_title="t")
    with (
        patch.object(BranchInfoService, "fetch_info", return_value=info),
        patch.object(BranchInfoService, "fetch_pr", return_value=77),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            await pilot.click("#branch-toggle-pr")
            await pilot.pause(delay=0.3)
            assert app._branch_service.pr_enabled is True
            assert _branch_zone(app, "pr") == "PR #77"


async def test_pr_result_dropped_when_toggle_flipped_off_during_refresh_pr_button_fetch(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Refresh-PR worker drops its result if toggle was flipped off mid-fetch."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="42-x", issue_number=42, issue_title="t")

    def fetch_pr_with_toggle_off(self: BranchInfoService, _issue: int) -> int:
        # Mid-call: user toggles off, bumping the generation.
        self.set_pr_enabled(False)
        return 42

    with (
        patch.object(BranchInfoService, "fetch_info", return_value=info),
        patch.object(BranchInfoService, "fetch_pr", fetch_pr_with_toggle_off),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            # Toggle PR on first
            await pilot.click("#branch-toggle-pr")
            await pilot.pause(delay=0.3)
            # Now click refresh-PR; the patched fetch_pr will toggle off mid-way
            await pilot.click("#branch-refresh-pr")
            await pilot.pause(delay=0.5)
            # PR zone must NOT show "PR #42" — toggle is off, gen mismatched
            assert "PR #42" not in _branch_zone(app, "pr")
            assert _branch_zone(app, "pr") == "—"


async def test_branch_change_kicks_pr_fetch(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """When branch changes during a 2s tick and toggle is on, PR fetch fires."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)

    fetched: list[str] = []

    def varying_fetch(self: BranchInfoService) -> BranchInfo:
        fetched.append("info")
        if len(fetched) <= 1:
            return _make_branch_info(branch="main", issue_number=None)
        return _make_branch_info(branch="123-foo", issue_number=123, issue_title="Foo")

    pr_calls: list[int] = []

    def record_pr(self: BranchInfoService, issue_number: int) -> int:
        pr_calls.append(issue_number)
        return 99

    with (
        patch.object(BranchInfoService, "fetch_info", varying_fetch),
        patch.object(BranchInfoService, "fetch_pr", record_pr),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            # Toggle PR on so branch-change triggers PR fetch
            app._branch_service.set_pr_enabled(True)
            # Drive the 2s tick directly
            app._tick_branch_quick()
            await pilot.pause(delay=0.5)
            assert 123 in pr_calls


async def test_failed_fetch_shows_question_mark(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """A fetch_info exception leaves the issue zone in a failed state."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)

    def boom(self: BranchInfoService) -> BranchInfo:
        raise RuntimeError("network down")

    with patch.object(BranchInfoService, "fetch_info", boom):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            await pilot.click("#branch-refresh-issue")
            await pilot.pause(delay=0.5)
            assert "issue" in app._branch_failed


async def test_pr_fetch_race_stale_result_dropped(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Stale PR worker result (from generation A) is dropped after toggle off+on+refresh."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="42-x", issue_number=42, issue_title="t")

    block = threading.Event()
    call_count = {"n": 0}

    def fetch_pr_blocking(self: BranchInfoService, _issue: int) -> int:
        call_count["n"] += 1
        n = call_count["n"]
        if n == 1:
            block.wait(timeout=5)
            return 42
        return 99

    with (
        patch.object(BranchInfoService, "fetch_info", return_value=info),
        patch.object(BranchInfoService, "fetch_pr", fetch_pr_blocking),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            # Toggle on, then launch worker A (blocks) via the refresh-PR handler
            app.on_branch_info_bar_toggle_pr(BranchInfoBar.TogglePR())
            await pilot.pause(delay=0.2)
            app.on_branch_info_bar_refresh_pr(BranchInfoBar.RefreshPR())
            await pilot.pause(delay=0.2)
            # Toggle off (gen bumps, in_flight cleared), then on
            app.on_branch_info_bar_toggle_pr(BranchInfoBar.TogglePR())
            await pilot.pause(delay=0.1)
            app.on_branch_info_bar_toggle_pr(BranchInfoBar.TogglePR())
            await pilot.pause(delay=0.1)
            # Launch worker B → PR #99
            app.on_branch_info_bar_refresh_pr(BranchInfoBar.RefreshPR())
            await pilot.pause(delay=0.5)
            # Worker B's result wins
            assert _branch_zone(app, "pr") == "PR #99"
            # Unblock worker A; its stale result must NOT replace #99
            block.set()
            await pilot.pause(delay=0.5)
            assert _branch_zone(app, "pr") == "PR #99"


async def test_pr_fetch_race_via_2s_tick_dropped_on_toggle_off(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """A PR worker spawned by the 2s tick is invalidated by a subsequent toggle-off."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="123-foo", issue_number=123, issue_title="Foo")

    block = threading.Event()

    def blocking_fetch_pr(self: BranchInfoService, _issue: int) -> int:
        block.wait(timeout=5)
        return 42

    with (
        patch.object(BranchInfoService, "fetch_info", return_value=info),
        patch.object(BranchInfoService, "fetch_pr", blocking_fetch_pr),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            app._branch_service.set_pr_enabled(True)
            # Drive the 2s tick: branch changes (None → 123-foo), kicks PR fetch
            app._tick_branch_quick()
            await pilot.pause(delay=0.3)
            # User toggles PR off via the handler (which re-renders)
            app.on_branch_info_bar_toggle_pr(BranchInfoBar.TogglePR())
            await pilot.pause(delay=0.1)
            block.set()
            await pilot.pause(delay=0.5)
            # PR zone must remain "—" (toggle off + worker dropped via gen check)
            assert _branch_zone(app, "pr") == "—"
            assert app._last_pr_number is None


def _make_runtime_info(project_dir: Path) -> RuntimeInfo:
    return RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir=str(project_dir),
        env_vars={},
        mcp_servers=[],
    )
