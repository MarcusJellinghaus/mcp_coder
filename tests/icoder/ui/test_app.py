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
from mcp_coder.icoder.ui.widgets.branch_info_bar import BranchInfoBar, BranchInfoView
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
                "name": "mcp__mcp-workspace__list_directory",
                "args": {},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__list_directory",
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
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
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
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "big.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
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
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "empty.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
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
                "name": "mcp__mcp-workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        app._handle_stream_event(
            {
                "type": "tool_result",
                "name": "mcp__mcp-workspace__read_file",
                "output": '{"result": "hello"}',
            }
        )
        indicator = app.query_one(BusyIndicator)
        assert "Thinking about mcp-workspace > read_file..." in indicator.label_text


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
    """When branch changes during a quick tick and toggle is on, PR fetch fires."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)

    pr_calls: list[int] = []

    def record_pr(self: BranchInfoService, issue_number: int) -> int:
        pr_calls.append(issue_number)
        return 99

    with (
        patch.object(
            BranchInfoService,
            "fetch_info",
            return_value=_make_branch_info(branch="main", issue_number=None),
        ),
        patch.object(
            BranchInfoService,
            "fetch_branch_only",
            return_value=_make_branch_info(
                branch="123-foo", issue_number=123, issue_title="Foo"
            ),
        ),
        patch.object(BranchInfoService, "fetch_pr", record_pr),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            # Toggle PR on so branch-change triggers PR fetch
            app._branch_service.set_pr_enabled(True)
            # Drive the quick tick directly
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


async def test_pr_result_none_clears_stale_pr_number(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """A successful PR worker returning ``None`` clears the previously stored PR.

    Regression for the bug where ``_apply_branch_state`` only wrote the PR
    number when it was non-None — so a refresh after the PR was deleted left
    the bar showing the stale ``PR #N``.
    """
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="42-x", issue_number=42, issue_title="t")

    pr_results: list[Optional[int]] = [77, None]

    def fetch_pr(self: BranchInfoService, _issue: int) -> Optional[int]:
        return pr_results.pop(0)

    with (
        patch.object(BranchInfoService, "fetch_info", return_value=info),
        patch.object(BranchInfoService, "fetch_pr", fetch_pr),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            # Toggle PR on → first fetch returns 77.
            await pilot.click("#branch-toggle-pr")
            await pilot.pause(delay=0.3)
            assert app._last_pr_number == 77
            assert _branch_zone(app, "pr") == "PR #77"
            # Refresh-PR → second fetch returns None.
            await pilot.click("#branch-refresh-pr")
            await pilot.pause(delay=0.5)
            assert app._last_pr_number is None
            assert _branch_zone(app, "pr") == "PR —"


async def test_stale_pr_worker_exception_does_not_set_failed_flag(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Stale PR worker that raises must not mutate ``_branch_failed``.

    Regression for the bug where ``_branch_failed.add('pr')`` ran before the
    generation-token check, so an invalidated worker still flipped the flag
    that belongs to a fresher generation.
    """
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="42-x", issue_number=42, issue_title="t")

    block = threading.Event()

    def fetch_pr_blocking_then_raise(
        self: BranchInfoService, _issue: int
    ) -> Optional[int]:
        block.wait(timeout=5)
        raise RuntimeError("network down")

    with (
        patch.object(BranchInfoService, "fetch_info", return_value=info),
        patch.object(BranchInfoService, "fetch_pr", fetch_pr_blocking_then_raise),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            # Toggle PR on (gen=1, worker A in flight, blocked).
            app.on_branch_info_bar_toggle_pr(BranchInfoBar.TogglePR())
            await pilot.pause(delay=0.2)
            # Toggle off (gen=2). Worker A is now stale.
            app.on_branch_info_bar_toggle_pr(BranchInfoBar.TogglePR())
            await pilot.pause(delay=0.1)
            # Unblock worker A → it raises, but is stale → must exit silently.
            block.set()
            await pilot.pause(delay=0.5)
            assert "pr" not in app._branch_failed


async def test_stale_pr_worker_success_does_not_mutate_state(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Stale PR worker that succeeds must not write ``_last_pr_number``.

    Sibling to ``test_pr_fetch_race_stale_result_dropped`` — verifies the
    stale-worker exit path leaves all UI state untouched, not just the
    rendered PR zone.
    """
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="42-x", issue_number=42, issue_title="t")

    block = threading.Event()

    def fetch_pr_blocking(self: BranchInfoService, _issue: int) -> int:
        block.wait(timeout=5)
        return 42

    with (
        patch.object(BranchInfoService, "fetch_info", return_value=info),
        patch.object(BranchInfoService, "fetch_pr", fetch_pr_blocking),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            # Toggle PR on (gen=1, worker A blocked).
            app.on_branch_info_bar_toggle_pr(BranchInfoBar.TogglePR())
            await pilot.pause(delay=0.2)
            # Toggle off (gen=2). Worker A is stale.
            app.on_branch_info_bar_toggle_pr(BranchInfoBar.TogglePR())
            await pilot.pause(delay=0.1)
            assert app._last_pr_number is None
            # Unblock worker A → its 42 result must NOT be written.
            block.set()
            await pilot.pause(delay=0.5)
            assert app._last_pr_number is None
            assert "pr" not in app._branch_loading
            assert "pr" not in app._branch_failed


async def test_toggle_on_while_worker_in_flight_does_not_duplicate(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Toggle-on path is guarded by ``begin_pr_fetch`` like refresh-PR.

    Spawn worker A via the refresh-PR button (which sets ``_pr_in_flight``),
    then immediately toggle PR on/off/on. The toggle-on with a worker still
    in flight must not spawn a duplicate worker.
    """
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="42-x", issue_number=42, issue_title="t")

    block = threading.Event()
    pr_call_count = {"n": 0}

    def fetch_pr_blocking(self: BranchInfoService, _issue: int) -> int:
        pr_call_count["n"] += 1
        block.wait(timeout=5)
        return 77

    with (
        patch.object(BranchInfoService, "fetch_info", return_value=info),
        patch.object(BranchInfoService, "fetch_pr", fetch_pr_blocking),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            # Toggle PR on → first worker (gen=1, in_flight=True).
            app.on_branch_info_bar_toggle_pr(BranchInfoBar.TogglePR())
            await pilot.pause(delay=0.2)
            assert pr_call_count["n"] == 1
            # User clicks toggle (now off) then toggle (now on) again before
            # worker A finishes. Toggle-off resets _pr_in_flight=False, so
            # the next toggle-on is allowed to spawn a fresh worker — but
            # only one. After toggle-on, _pr_in_flight is True again, so a
            # repeated toggle-on attempt (after another off+on) while the
            # second worker is in flight must NOT add a third worker.
            app.on_branch_info_bar_toggle_pr(BranchInfoBar.TogglePR())  # off
            await pilot.pause(delay=0.05)
            app.on_branch_info_bar_toggle_pr(BranchInfoBar.TogglePR())  # on (gen=3)
            await pilot.pause(delay=0.2)
            assert pr_call_count["n"] == 2
            # Now drive a refresh-PR while worker B is still blocked: it must
            # be rejected by begin_pr_fetch and not spawn a third worker.
            app.on_branch_info_bar_refresh_pr(BranchInfoBar.RefreshPR())
            await pilot.pause(delay=0.2)
            assert pr_call_count["n"] == 2
            block.set()
            await pilot.pause(delay=0.5)


async def test_quick_tick_merges_into_prior_branch_info(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Quick-tick merge preserves issue title/label/cache_last_checked."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    full = _make_branch_info(
        branch="123-foo",
        issue_number=123,
        issue_title="T",
        status_label="status-04:plan-review",
    )
    quick = BranchInfo(
        is_git_repo=True,
        branch_name="123-foo",
        is_dirty=False,
        issue_number=123,
        issue_title=None,
        issue_status_label=None,
        cache_last_checked=None,
    )
    with (
        patch.object(BranchInfoService, "fetch_info", return_value=full),
        patch.object(BranchInfoService, "fetch_branch_only", return_value=quick),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            assert app._last_branch_info is not None
            assert app._last_branch_info.issue_title == "T"
            prior_cache = app._last_branch_info.cache_last_checked
            app._tick_branch_quick()
            await pilot.pause(delay=0.3)
            assert app._last_branch_info is not None
            assert app._last_branch_info.issue_title == "T"
            assert app._last_branch_info.issue_status_label == "status-04:plan-review"
            assert app._last_branch_info.cache_last_checked == prior_cache


async def test_quick_tick_skipped_while_busy(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """begin_quick_tick False → fetch_branch_only is not called."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    quick = _make_branch_info(branch="main")
    with (
        patch.object(BranchInfoService, "fetch_info", return_value=quick),
        patch.object(
            BranchInfoService, "fetch_branch_only", return_value=quick
        ) as quick_mock,
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            quick_mock.reset_mock()
            # Force the busy flag on, then try to drive a quick tick.
            app._branch_service._quick_tick_busy = True
            app._tick_branch_quick()
            await pilot.pause(delay=0.3)
            assert quick_mock.call_count == 0


async def test_full_tick_skipped_while_busy(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """begin_full_tick False → fetch_info is not called by the full worker."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="main")
    with (
        patch.object(BranchInfoService, "fetch_info", return_value=info) as fetch_mock,
        patch.object(BranchInfoService, "fetch_branch_only", return_value=info),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            fetch_mock.reset_mock()
            app._branch_service._full_tick_busy = True
            app._tick_branch_full()
            await pilot.pause(delay=0.3)
            assert fetch_mock.call_count == 0


async def test_quick_and_full_ticks_run_in_parallel(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Quick-tick busy must not block the full tick from running."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="main")
    with (
        patch.object(BranchInfoService, "fetch_info", return_value=info) as fetch_mock,
        patch.object(BranchInfoService, "fetch_branch_only", return_value=info),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            fetch_mock.reset_mock()
            app._branch_service._quick_tick_busy = True
            app._tick_branch_full()
            await pilot.pause(delay=0.3)
            assert fetch_mock.call_count >= 1


async def test_render_diff_skips_unchanged_view(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Identical consecutive renders must not call update_state twice."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="main", issue_number=None)
    with (
        patch.object(BranchInfoService, "fetch_info", return_value=info),
        patch.object(BranchInfoService, "fetch_branch_only", return_value=info),
    ):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            with patch.object(BranchInfoBar, "update_state") as update_mock:
                app._render_branch_state()
                app._render_branch_state()
                assert update_mock.call_count == 0


async def test_render_diff_emits_first_real_view(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """A None → view transition must emit one update_state call."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    with patch.object(BranchInfoService, "fetch_info", side_effect=RuntimeError):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            app._last_branch_info = None
            app._last_view = None
            new_info = _make_branch_info(branch="123-foo", issue_number=123)
            app._last_branch_info = new_info
            with patch.object(BranchInfoBar, "update_state") as update_mock:
                app._render_branch_state()
                assert update_mock.call_count == 1
                emitted = update_mock.call_args[0][0]
                assert isinstance(emitted, BranchInfoView)
                assert emitted.info is new_info


async def test_render_diff_emits_when_returning_to_none(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """A view → None transition must emit update_state(None)."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="main")
    with patch.object(BranchInfoService, "fetch_info", return_value=info):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            assert app._last_view is not None
            app._last_branch_info = None
            with patch.object(BranchInfoBar, "update_state") as update_mock:
                app._render_branch_state()
                assert update_mock.call_count == 1
                assert update_mock.call_args[0][0] is None


async def test_render_diff_emits_when_field_changes(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """A field change in the view must emit a fresh update_state call."""
    runtime_info = _make_runtime_info(tmp_path)
    app = make_icoder_app(runtime_info=runtime_info)
    info = _make_branch_info(branch="42-x", issue_number=42, issue_title="t")
    with patch.object(BranchInfoService, "fetch_info", return_value=info):
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.3)
            assert app._last_view is not None
            app._last_pr_number = 99
            with patch.object(BranchInfoBar, "update_state") as update_mock:
                app._render_branch_state()
                assert update_mock.call_count == 1
                emitted = update_mock.call_args[0][0]
                assert isinstance(emitted, BranchInfoView)
                assert emitted.pr_number == 99


async def test_status_version_label_has_mcp_coder_prefix(
    make_icoder_app: Callable[..., ICoderApp],
    tmp_path: Path,
) -> None:
    """Status-bar version label is prefixed with 'mcp-coder '."""
    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir=str(tmp_path),
        env_vars={},
        mcp_servers=[],
    )
    app = make_icoder_app(runtime_info=runtime_info)
    async with app.run_test() as pilot:
        await pilot.pause()
        widget = app.query_one("#status-version", Static)
        assert "mcp-coder v9.9.9" in str(widget.render())


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
