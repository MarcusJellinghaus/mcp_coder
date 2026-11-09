"""Tests for registering `CommandToolkit` as entry point `command`."""

import tomllib
from pathlib import Path
from unittest.mock import patch

from mcp_coder.toolkits.command import CommandToolkit
from mcp_coder.utils.toolkit_runner import load_toolkit

_PYPROJECT = Path(__file__).resolve().parents[3] / "pyproject.toml"


def test_entry_point_declared() -> None:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    group = data["project"]["entry-points"]["mcp_coder.toolkits"]
    assert group["command"] == "mcp_coder.toolkits.command:CommandToolkit"


def test_load_toolkit_command(tmp_path: Path) -> None:
    (tmp_path / "mcp-coder.toml").write_text(
        '[tool.mcp-coder.toolkit]\ntoolkit = "command"\n', encoding="utf-8"
    )
    with patch(
        "mcp_coder.utils.toolkit_runner._toolkit_class",
        lambda _name: CommandToolkit,
    ):
        loaded = load_toolkit(tmp_path)
    assert loaded.name == "command"
    assert isinstance(loaded.toolkit, CommandToolkit)
