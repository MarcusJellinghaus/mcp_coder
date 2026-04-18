"""Tests for iCoder CLI execute_icoder wiring."""

from __future__ import annotations

import json
import logging
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from tests.icoder.conftest import FAKE_RUNTIME_INFO, make_icoder_args

# --- env_setup integration tests ---


@patch("mcp_coder.icoder.ui.app.ICoderApp.run")
@patch("mcp_coder.cli.commands.icoder.setup_icoder_environment")
def test_execute_icoder_calls_env_setup(
    mock_setup: MagicMock,
    _mock_run: MagicMock,
    tmp_path: Path,
) -> None:
    """Verify setup_icoder_environment is called with project_dir."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    mock_setup.return_value = FAKE_RUNTIME_INFO
    (tmp_path / "logs").mkdir()
    args = make_icoder_args(tmp_path)

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

    mock_setup.return_value = FAKE_RUNTIME_INFO
    (tmp_path / "logs").mkdir()
    args = make_icoder_args(tmp_path)

    result = execute_icoder(args)

    assert result == 0
    # Check session_start event was written to log file
    log_files = list((tmp_path / "logs").glob("*.jsonl"))
    assert len(log_files) >= 1
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
    args = make_icoder_args(tmp_path)

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

    mock_setup.return_value = FAKE_RUNTIME_INFO
    (tmp_path / "logs").mkdir()
    args = make_icoder_args(tmp_path)

    execute_icoder(args)

    _, kwargs = mock_llm_init.call_args
    assert kwargs["env_vars"] == FAKE_RUNTIME_INFO.env_vars


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
        lambda _: FAKE_RUNTIME_INFO,
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

    args = make_icoder_args(tmp_path)
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
        lambda _: FAKE_RUNTIME_INFO,
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

    args = make_icoder_args(tmp_path)
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
    args = make_icoder_args(tmp_path)

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
    mock_setup.return_value = FAKE_RUNTIME_INFO
    (tmp_path / "logs").mkdir()
    args = make_icoder_args(tmp_path)

    result = execute_icoder(args)

    assert result == 0
    mock_setup.assert_called_once_with(tmp_path)


# --- /info and /color registration tests ---


def _patch_all_icoder_deps(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> list[AppCore]:
    """Patch deps and return list that will capture AppCore instances."""
    from mcp_coder.icoder.ui.app import ICoderApp

    captured_app_core: list[AppCore] = []

    def capturing_init(self: object, app_core: object, **kwargs: object) -> None:
        captured_app_core.append(app_core)  # type: ignore[arg-type]

    monkeypatch.setattr(ICoderApp, "__init__", capturing_init)
    monkeypatch.setattr(ICoderApp, "run", lambda self: None)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.setup_icoder_environment",
        lambda _: FAKE_RUNTIME_INFO,
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
    return captured_app_core


def test_info_command_registered_in_icoder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify /info is registered in the command registry after execute_icoder sets up."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    captured_app_core = _patch_all_icoder_deps(monkeypatch, tmp_path)

    args = make_icoder_args(tmp_path)
    result = execute_icoder(args)

    assert result == 0
    assert len(captured_app_core) == 1
    command_names = [c.name for c in captured_app_core[0].registry.get_all()]
    assert "/info" in command_names


def test_color_command_registered_in_icoder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify /color is registered in the command registry after execute_icoder sets up."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    captured_app_core = _patch_all_icoder_deps(monkeypatch, tmp_path)

    args = make_icoder_args(tmp_path)
    result = execute_icoder(args)

    assert result == 0
    assert len(captured_app_core) == 1
    command_names = [c.name for c in captured_app_core[0].registry.get_all()]
    assert "/color" in command_names


# --- --initial-color wiring tests ---


def test_execute_icoder_initial_color_applied(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Valid --initial-color sets prompt_color on app_core."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    captured_app_core = _patch_all_icoder_deps(monkeypatch, tmp_path)

    args = make_icoder_args(tmp_path)
    args.initial_color = "red"
    result = execute_icoder(args)

    assert result == 0
    assert len(captured_app_core) == 1
    assert captured_app_core[0].prompt_color == "#ef4444"


def test_execute_icoder_initial_color_invalid_warns(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Invalid --initial-color logs warning and keeps default color."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    captured_app_core = _patch_all_icoder_deps(monkeypatch, tmp_path)

    args = make_icoder_args(tmp_path)
    args.initial_color = "not_a_color"

    with caplog.at_level(logging.WARNING):
        result = execute_icoder(args)

    assert result == 0
    assert len(captured_app_core) == 1
    assert captured_app_core[0].prompt_color == "#666666"
    assert "Invalid --initial-color" in caplog.text
