"""Tests for iCoder MCPManager wiring in execute_icoder."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tests.icoder.conftest import FAKE_RUNTIME_INFO, make_icoder_args, patch_icoder_deps


def test_mcp_manager_created_for_langchain(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MCPManager is created when provider=langchain and mcp_config is set."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    patch_icoder_deps(monkeypatch, tmp_path)

    created_managers: list[object] = []
    fake_server_config = {"server1": {"command": "echo", "args": []}}

    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder._load_mcp_server_config",
        lambda *_a, **_kw: fake_server_config,
    )

    def tracking_init(self: object, server_config: object) -> None:
        created_managers.append(self)
        # Don't start real threads — just set minimal attrs
        object.__setattr__(self, "_server_names", [])
        object.__setattr__(self, "_server_config", server_config)
        object.__setattr__(self, "_cached_tools", None)
        object.__setattr__(self, "_client", None)
        object.__setattr__(self, "_tool_counts", {})
        object.__setattr__(self, "_loop", None)
        object.__setattr__(self, "_thread", None)

    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.MCPManager.__init__", tracking_init
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.MCPManager.close", lambda self: None
    )

    args = make_icoder_args(tmp_path)
    result = execute_icoder(args)

    assert result == 0
    assert len(created_managers) == 1


def test_mcp_manager_not_created_for_claude(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MCPManager is NOT created when provider=claude."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    patch_icoder_deps(monkeypatch, tmp_path)

    # Override to claude provider
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_llm_method",
        lambda _: ("claude", None),
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.parse_llm_method_from_args",
        lambda _: "claude",
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_mcp_config_path",
        lambda *a, **_kw: None,
    )

    created_managers: list[object] = []

    def tracking_init(self: object, server_config: object) -> None:
        created_managers.append(self)

    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.MCPManager.__init__", tracking_init
    )

    args = make_icoder_args(tmp_path)
    result = execute_icoder(args)

    assert result == 0
    assert len(created_managers) == 0


def test_mcp_manager_closed_on_exit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MCPManager.close() is called after TUI exits normally."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    patch_icoder_deps(monkeypatch, tmp_path)

    close_called: list[bool] = []
    fake_server_config = {"server1": {"command": "echo", "args": []}}

    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder._load_mcp_server_config",
        lambda *_a, **_kw: fake_server_config,
    )

    def fake_init(self: object, server_config: object) -> None:
        object.__setattr__(self, "_server_names", [])
        object.__setattr__(self, "_server_config", server_config)
        object.__setattr__(self, "_cached_tools", None)
        object.__setattr__(self, "_client", None)
        object.__setattr__(self, "_tool_counts", {})
        object.__setattr__(self, "_loop", None)
        object.__setattr__(self, "_thread", None)

    monkeypatch.setattr("mcp_coder.cli.commands.icoder.MCPManager.__init__", fake_init)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.MCPManager.close",
        lambda self: close_called.append(True),
    )

    args = make_icoder_args(tmp_path)
    result = execute_icoder(args)

    assert result == 0
    assert len(close_called) == 1


def test_mcp_manager_closed_on_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MCPManager.close() is still called when TUI raises an exception."""
    from mcp_coder.cli.commands.icoder import execute_icoder
    from mcp_coder.icoder.ui.app import ICoderApp

    (tmp_path / "logs").mkdir()
    patch_icoder_deps(monkeypatch, tmp_path)

    close_called: list[bool] = []
    fake_server_config = {"server1": {"command": "echo", "args": []}}

    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder._load_mcp_server_config",
        lambda *_a, **_kw: fake_server_config,
    )

    def fake_init(self: object, server_config: object) -> None:
        object.__setattr__(self, "_server_names", [])
        object.__setattr__(self, "_server_config", server_config)
        object.__setattr__(self, "_cached_tools", None)
        object.__setattr__(self, "_client", None)
        object.__setattr__(self, "_tool_counts", {})
        object.__setattr__(self, "_loop", None)
        object.__setattr__(self, "_thread", None)

    monkeypatch.setattr("mcp_coder.cli.commands.icoder.MCPManager.__init__", fake_init)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.MCPManager.close",
        lambda self: close_called.append(True),
    )

    # Make ICoderApp.run raise
    def raise_boom(self: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(ICoderApp, "run", raise_boom)

    args = make_icoder_args(tmp_path)
    result = execute_icoder(args)

    # Should still return (caught by top-level handler) and close was called
    assert result == 1
    assert len(close_called) == 1


def test_mcp_manager_passed_to_llm_service(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MCPManager instance is passed to RealLLMService constructor."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    patch_icoder_deps(monkeypatch, tmp_path)

    fake_server_config = {"server1": {"command": "echo", "args": []}}
    captured_kwargs: list[dict[str, object]] = []

    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder._load_mcp_server_config",
        lambda *_a, **_kw: fake_server_config,
    )

    def fake_manager_init(self: object, server_config: object) -> None:
        object.__setattr__(self, "_server_names", [])
        object.__setattr__(self, "_server_config", server_config)
        object.__setattr__(self, "_cached_tools", None)
        object.__setattr__(self, "_client", None)
        object.__setattr__(self, "_tool_counts", {})
        object.__setattr__(self, "_loop", None)
        object.__setattr__(self, "_thread", None)

    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.MCPManager.__init__", fake_manager_init
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.MCPManager.close", lambda self: None
    )

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.RealLLMService.__init__",
        lambda self, **kw: captured_kwargs.append(kw),
    )

    args = make_icoder_args(tmp_path)
    result = execute_icoder(args)

    assert result == 0
    assert len(captured_kwargs) == 1
    assert captured_kwargs[0]["mcp_manager"] is not None
