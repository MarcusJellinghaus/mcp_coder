"""Tests for iCoder CLI command wiring."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.main import create_parser
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.utils.mcp_verification import MCPServerInfo


def test_icoder_parser_registered() -> None:
    """Test parser is registered (icoder appears in subcommands)."""
    parser = create_parser()
    args = parser.parse_args(["icoder"])
    assert args.command == "icoder"


def test_icoder_llm_method_flag() -> None:
    """Test parser accepts --llm-method flag."""
    parser = create_parser()
    args = parser.parse_args(["icoder", "--llm-method", "langchain"])
    assert args.llm_method == "langchain"


def test_icoder_project_dir_flag() -> None:
    """Test parser accepts --project-dir flag."""
    parser = create_parser()
    args = parser.parse_args(["icoder", "--project-dir", "/tmp/test"])
    assert args.project_dir == "/tmp/test"


def test_icoder_mcp_config_flag() -> None:
    """Test parser accepts --mcp-config flag."""
    parser = create_parser()
    args = parser.parse_args(["icoder", "--mcp-config", "/tmp/.mcp.json"])
    assert args.mcp_config == "/tmp/.mcp.json"


def test_icoder_execution_dir_flag() -> None:
    """Test parser accepts --execution-dir flag."""
    parser = create_parser()
    args = parser.parse_args(["icoder", "--execution-dir", "/tmp/exec"])
    assert args.execution_dir == "/tmp/exec"


def test_icoder_default_values() -> None:
    """Test parser default values."""
    parser = create_parser()
    args = parser.parse_args(["icoder"])
    assert args.llm_method is None
    assert args.project_dir is None
    assert args.mcp_config is None
    assert args.execution_dir is None


def test_icoder_no_format_tools_flag() -> None:
    """Test parser accepts --no-format-tools flag."""
    parser = create_parser()
    args = parser.parse_args(["icoder", "--no-format-tools"])
    assert args.no_format_tools is True


def test_icoder_no_format_tools_default() -> None:
    """Test --no-format-tools defaults to False (formatting on)."""
    parser = create_parser()
    args = parser.parse_args(["icoder"])
    assert args.no_format_tools is False


def test_execute_icoder_importable() -> None:
    """Test execute_icoder is importable and callable."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    assert callable(execute_icoder)


def test_main_routes_icoder(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() dispatches 'icoder' to execute_icoder."""
    called: dict[str, object] = {}

    def mock_execute(args):  # type: ignore[no-untyped-def]
        called["args"] = args
        return 0

    monkeypatch.setattr("sys.argv", ["mcp-coder", "icoder"])

    with patch("mcp_coder.cli.main.execute_icoder", mock_execute):
        from mcp_coder.cli.main import main

        result = main()

    assert result == 0
    args_obj = called["args"]
    assert getattr(args_obj, "command") == "icoder"


# --- env_setup integration tests ---

_FAKE_RUNTIME_INFO = RuntimeInfo(
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


def _make_args(tmp_path: Path) -> MagicMock:
    """Create a mock args namespace for execute_icoder."""
    args = MagicMock()
    args.execution_dir = None
    args.project_dir = str(tmp_path)
    args.llm_method = None
    args.mcp_config = None
    args.session_id = None
    args.continue_session = False
    args.continue_session_from = None
    return args


@patch("mcp_coder.icoder.ui.app.ICoderApp.run")
@patch("mcp_coder.cli.commands.icoder.setup_icoder_environment")
def test_execute_icoder_calls_env_setup(
    mock_setup: MagicMock,
    _mock_run: MagicMock,
    tmp_path: Path,
) -> None:
    """Verify setup_icoder_environment is called with project_dir."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    mock_setup.return_value = _FAKE_RUNTIME_INFO
    (tmp_path / "logs").mkdir()
    args = _make_args(tmp_path)

    execute_icoder(args)

    mock_setup.assert_called_once_with(tmp_path)


@patch("mcp_coder.icoder.ui.app.ICoderApp.run")
@patch("mcp_coder.cli.commands.icoder.setup_icoder_environment")
def test_execute_icoder_emits_session_start(
    mock_setup: MagicMock,
    _mock_run: MagicMock,
    tmp_path: Path,
) -> None:
    """Verify session_start event is emitted to EventLog."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    mock_setup.return_value = _FAKE_RUNTIME_INFO
    (tmp_path / "logs").mkdir()
    args = _make_args(tmp_path)

    result = execute_icoder(args)

    assert result == 0
    # Check session_start event was written to log file
    log_files = list((tmp_path / "logs").glob("*.jsonl"))
    assert len(log_files) >= 1
    import json

    events = [
        json.loads(line) for f in log_files for line in f.read_text().splitlines()
    ]
    session_starts = [e for e in events if e.get("event") == "session_start"]
    assert len(session_starts) == 1
    assert session_starts[0]["mcp_coder_version"] == "0.42.0"


@pytest.mark.parametrize(
    "exc_type",
    [FileNotFoundError, RuntimeError, PackageNotFoundError],
)
@patch("mcp_coder.cli.commands.icoder.setup_icoder_environment")
def test_execute_icoder_env_setup_failure_returns_1(
    mock_setup: MagicMock,
    exc_type: type,
    tmp_path: Path,
) -> None:
    """Verify execute_icoder returns 1 on env_setup failure."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    mock_setup.side_effect = exc_type("setup failed")
    args = _make_args(tmp_path)

    result = execute_icoder(args)

    assert result == 1


@patch("mcp_coder.icoder.ui.app.ICoderApp.run")
@patch(
    "mcp_coder.icoder.services.llm_service.RealLLMService.__init__",
    return_value=None,
)
@patch("mcp_coder.cli.commands.icoder.setup_icoder_environment")
def test_execute_icoder_passes_env_vars_to_llm_service(
    mock_setup: MagicMock,
    mock_llm_init: MagicMock,
    _mock_run: MagicMock,
    tmp_path: Path,
) -> None:
    """Verify env_vars from RuntimeInfo are passed to RealLLMService."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    mock_setup.return_value = _FAKE_RUNTIME_INFO
    (tmp_path / "logs").mkdir()
    args = _make_args(tmp_path)

    execute_icoder(args)

    _, kwargs = mock_llm_init.call_args
    assert kwargs["env_vars"] == _FAKE_RUNTIME_INFO.env_vars


def test_execute_icoder_creates_registry_with_skills(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """execute_icoder creates registry, loads skills, and passes to AppCore."""
    from mcp_coder.cli.commands.icoder import execute_icoder
    from mcp_coder.icoder.core.command_registry import CommandRegistry
    from mcp_coder.icoder.core.types import Command, Response

    (tmp_path / "logs").mkdir()

    # Fake skill that register_skill_commands would create
    fake_skill_command = Command(
        name="/test_skill",
        description="A test skill",
        handler=lambda args: Response(send_to_llm=True),
        show_in_help=False,
    )

    def fake_register(
        registry: CommandRegistry,
        skills: list[object],
        provider: str,
    ) -> list[object]:
        registry.add_command(fake_skill_command)
        return []

    # Capture the AppCore instance
    captured_app_core: list[object] = []

    from mcp_coder.icoder.ui.app import ICoderApp

    def capturing_init(self: object, app_core: object, **kwargs: object) -> None:
        captured_app_core.append(app_core)

    monkeypatch.setattr(ICoderApp, "__init__", capturing_init)
    monkeypatch.setattr(ICoderApp, "run", lambda self: None)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.setup_icoder_environment",
        lambda _: _FAKE_RUNTIME_INFO,
    )
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
        fake_register,
    )

    args = _make_args(tmp_path)
    result = execute_icoder(args)

    assert result == 0
    assert len(captured_app_core) == 1
    from mcp_coder.icoder.core.app_core import AppCore

    core: AppCore = captured_app_core[0]  # type: ignore[assignment]
    # Verify skill is registered
    command_names = [c.name for c in core.registry.get_all()]
    assert "/test_skill" in command_names


def test_execute_icoder_passes_format_tools_to_app(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify format_tools=False is passed to ICoderApp when --no-format-tools is set."""
    from mcp_coder.cli.commands.icoder import execute_icoder
    from mcp_coder.icoder.ui.app import ICoderApp

    (tmp_path / "logs").mkdir()

    captured_kwargs: list[dict[str, object]] = []

    def capturing_init(self: object, app_core: object, **kwargs: object) -> None:
        captured_kwargs.append(kwargs)

    monkeypatch.setattr(ICoderApp, "__init__", capturing_init)
    monkeypatch.setattr(ICoderApp, "run", lambda self: None)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.setup_icoder_environment",
        lambda _: _FAKE_RUNTIME_INFO,
    )
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

    args = _make_args(tmp_path)
    args.no_format_tools = True
    result = execute_icoder(args)

    assert result == 0
    assert len(captured_kwargs) == 1
    assert captured_kwargs[0]["format_tools"] is False


# --- TUI pre-flight integration tests ---


@patch("mcp_coder.cli.commands.icoder.TuiChecker")
@patch("mcp_coder.cli.commands.icoder.setup_icoder_environment")
def test_execute_icoder_tui_preflight_abort(
    mock_setup: MagicMock,
    mock_checker_cls: MagicMock,
    tmp_path: Path,
) -> None:
    """TuiPreflightAbort is caught and returns its exit code without traceback."""
    from mcp_coder.cli.commands.icoder import execute_icoder
    from mcp_coder.utils.tui_preparation import TuiPreflightAbort

    mock_checker_cls.return_value.run_all_checks.side_effect = TuiPreflightAbort(
        "broken terminal", 1
    )
    args = _make_args(tmp_path)

    result = execute_icoder(args)

    assert result == 1
    # setup_icoder_environment should NOT have been called
    mock_setup.assert_not_called()


@patch("mcp_coder.icoder.ui.app.ICoderApp.run")
@patch("mcp_coder.cli.commands.icoder.setup_icoder_environment")
@patch("mcp_coder.cli.commands.icoder.TuiChecker")
def test_execute_icoder_tui_preflight_passes(
    mock_checker_cls: MagicMock,
    mock_setup: MagicMock,
    _mock_run: MagicMock,
    tmp_path: Path,
) -> None:
    """When TuiChecker passes, normal flow continues to setup_icoder_environment."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    mock_checker_cls.return_value.run_all_checks.return_value = None
    mock_setup.return_value = _FAKE_RUNTIME_INFO
    (tmp_path / "logs").mkdir()
    args = _make_args(tmp_path)

    result = execute_icoder(args)

    assert result == 0
    mock_setup.assert_called_once_with(tmp_path)


# --- Step 5: MCPManager wiring + /info registration tests ---


def _patch_icoder_deps(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Patch common icoder dependencies for wiring tests."""
    from mcp_coder.icoder.ui.app import ICoderApp

    monkeypatch.setattr(ICoderApp, "__init__", lambda self, app_core, **kw: None)
    monkeypatch.setattr(ICoderApp, "run", lambda self: None)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.setup_icoder_environment",
        lambda _: _FAKE_RUNTIME_INFO,
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


def test_info_command_registered_in_icoder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify /info is registered in the command registry after execute_icoder sets up."""
    from mcp_coder.cli.commands.icoder import execute_icoder
    from mcp_coder.icoder.core.app_core import AppCore
    from mcp_coder.icoder.ui.app import ICoderApp

    (tmp_path / "logs").mkdir()

    captured_app_core: list[AppCore] = []

    def capturing_init(self: object, app_core: object, **kwargs: object) -> None:
        captured_app_core.append(app_core)  # type: ignore[arg-type]

    monkeypatch.setattr(ICoderApp, "__init__", capturing_init)
    monkeypatch.setattr(ICoderApp, "run", lambda self: None)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.setup_icoder_environment",
        lambda _: _FAKE_RUNTIME_INFO,
    )
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

    args = _make_args(tmp_path)
    result = execute_icoder(args)

    assert result == 0
    assert len(captured_app_core) == 1
    command_names = [c.name for c in captured_app_core[0].registry.get_all()]
    assert "/info" in command_names


def test_mcp_manager_created_for_langchain(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MCPManager is created when provider=langchain and mcp_config is set."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    _patch_icoder_deps(monkeypatch, tmp_path)

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

    args = _make_args(tmp_path)
    result = execute_icoder(args)

    assert result == 0
    assert len(created_managers) == 1


def test_mcp_manager_not_created_for_claude(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MCPManager is NOT created when provider=claude."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    _patch_icoder_deps(monkeypatch, tmp_path)

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

    args = _make_args(tmp_path)
    result = execute_icoder(args)

    assert result == 0
    assert len(created_managers) == 0


def test_mcp_manager_closed_on_exit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MCPManager.close() is called after TUI exits normally."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    _patch_icoder_deps(monkeypatch, tmp_path)

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

    args = _make_args(tmp_path)
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
    _patch_icoder_deps(monkeypatch, tmp_path)

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

    args = _make_args(tmp_path)
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
    _patch_icoder_deps(monkeypatch, tmp_path)

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

    args = _make_args(tmp_path)
    result = execute_icoder(args)

    assert result == 0
    assert len(captured_kwargs) == 1
    assert captured_kwargs[0]["mcp_manager"] is not None
