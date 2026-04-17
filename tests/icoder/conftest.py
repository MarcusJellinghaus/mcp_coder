"""Shared fixtures for iCoder tests."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.utils.mcp_verification import MCPServerInfo

FAKE_RUNTIME_INFO = RuntimeInfo(
    mcp_coder_version="0.42.0",
    python_version="3.12.0",
    claude_code_version="1.2.3",
    tool_env_path="/fake/tool",
    project_venv_path="/fake/proj/.venv",
    project_dir="/fake/proj",
    env_vars={
        "MCP_CODER_VENV_PATH": "/fake/bin",
        "MCP_CODER_VENV_DIR": "/fake/tool",
        "MCP_CODER_PROJECT_DIR": "/fake/proj",
    },
    mcp_servers=[
        MCPServerInfo(
            name="mcp-tools-py",
            path=Path("/fake/mcp-tools-py"),
            version="1.0",
        ),
    ],
)


def make_icoder_args(tmp_path: Path) -> MagicMock:
    """Create a mock args namespace for execute_icoder."""
    args = MagicMock()
    args.execution_dir = None
    args.project_dir = str(tmp_path)
    args.llm_method = None
    args.mcp_config = None
    args.session_id = None
    args.continue_session = False
    args.continue_session_from = None
    args.initial_color = None
    return args


def patch_icoder_deps(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Patch common icoder dependencies for wiring tests."""
    from mcp_coder.icoder.ui.app import ICoderApp

    monkeypatch.setattr(ICoderApp, "__init__", lambda self, app_core, **kw: None)
    monkeypatch.setattr(ICoderApp, "run", lambda self: None)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.setup_icoder_environment",
        lambda _: FAKE_RUNTIME_INFO,
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_llm_method",
        lambda _: ("langchain", None),
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.parse_llm_method_from_args",
        lambda _: "langchain",
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_mcp_config_path",
        lambda *a, **_kw: "/fake/.mcp.json",
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.find_latest_session",
        lambda **_kw: None,
    )
    monkeypatch.setattr(
        "mcp_coder.icoder.skills.load_skills",
        lambda _: [],
    )
    monkeypatch.setattr(
        "mcp_coder.icoder.skills.register_skill_commands",
        lambda registry, skills, provider: [],
    )


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
