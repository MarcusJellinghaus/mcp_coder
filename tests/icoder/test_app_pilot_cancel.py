from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest

from mcp_coder.icoder.permissions.model import PermissionFrame
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.busy_indicator import BusyIndicator
from mcp_coder.icoder.ui.widgets.output_log import OutputLog
from mcp_coder.llm.types import StreamEvent
from tests.icoder.test_app_pilot import _submit_and_wait

pytestmark = pytest.mark.textual_integration


class SlowLLMService:
    """LLM service that yields events with delays to simulate streaming."""

    def stream(
        self, question: str, *, frame: PermissionFrame | None = None
    ) -> Iterator[StreamEvent]:
        import time

        for i in range(20):
            time.sleep(0.05)
            yield {"type": "text_delta", "text": f"chunk{i} "}
        yield {"type": "done"}

    @property
    def provider(self) -> str:
        return "claude"

    @property
    def session_id(self) -> str | None:
        return None

    def reset_session(self) -> None:
        pass


async def test_escape_cancels_streaming(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Escape during streaming breaks the loop and shows cancelled marker."""
    app = make_icoder_app(llm_service=SlowLLMService())
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="hello")
        await pilot.press("escape")
        await pilot.pause(delay=0.5)
        output = app.query_one(OutputLog)
        assert "\u2014 Cancelled \u2014" in output.recorded_lines


async def test_escape_when_idle_is_noop(icoder_app: ICoderApp) -> None:
    """Escape when not streaming does nothing harmful."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        output = icoder_app.query_one(OutputLog)
        assert "\u2014 Cancelled \u2014" not in output.recorded_lines


async def test_busy_indicator_resets_after_cancel(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """After Escape cancel, busy indicator shows 'Ready'."""
    app = make_icoder_app(llm_service=SlowLLMService())
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="hello")
        await pilot.press("escape")
        indicator = app.query_one(BusyIndicator)
        # Poll: on a loaded machine the cancel can take longer than one pause.
        for _ in range(50):
            await pilot.pause(delay=0.1)
            if "Ready" in indicator.label_text:
                break
        assert "\u2713 Ready" in indicator.label_text


async def test_session_preserved_after_cancel(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """Cancel doesn't reset session -- previous session ID persists."""

    class SlowLLMServiceWithSession:
        def __init__(self) -> None:
            self._session_id: str | None = "test-session-123"

        def stream(
            self, question: str, *, frame: PermissionFrame | None = None
        ) -> Iterator[StreamEvent]:
            import time

            for i in range(20):
                time.sleep(0.05)
                yield {"type": "text_delta", "text": f"chunk{i} "}
            yield {"type": "done"}

        @property
        def provider(self) -> str:
            return "claude"

        @property
        def session_id(self) -> str | None:
            return self._session_id

        def reset_session(self) -> None:
            self._session_id = None

    svc = SlowLLMServiceWithSession()
    app = make_icoder_app(llm_service=svc)
    async with app.run_test() as pilot:
        await _submit_and_wait(app, pilot, text="hello")
        await pilot.press("escape")
        await pilot.pause(delay=0.5)
        assert svc.session_id == "test-session-123"


async def test_ctrl_c_does_not_quit(icoder_app: ICoderApp) -> None:
    """Ctrl+C should not trigger the quit confirmation dialog."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("ctrl+c")
        await pilot.pause()
        assert icoder_app.is_running
        assert len(icoder_app._notifications) == 0
