"""Shared fixtures for iCoder UI tests."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.llm.types import StreamEvent


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
