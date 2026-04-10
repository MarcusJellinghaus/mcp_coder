"""Shared fixtures for iCoder tests."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.services.llm_service import FakeLLMService


@pytest.fixture(autouse=True)
def _no_store_session() -> Generator[None, None, None]:
    """Prevent store_session from writing to disk in all icoder tests."""
    with patch(
        "mcp_coder.icoder.core.app_core.store_session",
        return_value="/fake/path.json",
    ):
        yield


@pytest.fixture
def fake_llm() -> FakeLLMService:
    """Provide a FakeLLMService instance."""
    return FakeLLMService()


@pytest.fixture
def event_log(tmp_path: Path) -> Generator[EventLog, None, None]:
    """Provide an EventLog writing to a temp directory."""
    with EventLog(logs_dir=tmp_path) as log:
        yield log


@pytest.fixture
def app_core(fake_llm: FakeLLMService, event_log: EventLog) -> AppCore:
    """Provide an AppCore with fake dependencies."""
    return AppCore(llm_service=fake_llm, event_log=event_log, runtime_info=None)
