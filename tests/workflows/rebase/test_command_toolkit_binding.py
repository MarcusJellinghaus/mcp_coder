"""Binding-level test: an npm-style project runs entirely on ``CommandToolkit``.

The project has only ``mcp-coder.toml``; every step runs a small Python script
through the ``fakenpm`` launcher, and nothing from ``mcp_coder.mcp_tools_py``
may be called.
"""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder import mcp_tools_py
from mcp_coder.toolkits.command import CommandToolkit
from mcp_coder.utils.toolkit_runner import load_toolkit, run_binding
from mcp_coder.workflow_steps.commit import run_formatters
from mcp_coder.workflows.rebase_checks import _run_all_checks

_CONFIG = """\
[tool.mcp-coder.toolkit]
toolkit = "command"

[tool.mcp-coder.toolkit.command]
format.apply = [{ argv = ["fakenpm", "format"] }]
check.quick = [{ argv = ["fakenpm", "lint"], name = "lint" }]
check.standard = [
    { argv = ["fakenpm", "lint"], name = "lint" },
    { argv = ["fakenpm", "types"], name = "types" },
]
test.standard = [{ argv = ["fakenpm", "unit"], name = "unit" }]
"""


def _script(scripts: Path, name: str, code: int, output: str) -> None:
    (scripts / f"{name}.py").write_text(
        f"import sys\nprint({output!r})\nsys.exit({code})\n", encoding="utf-8"
    )


@pytest.fixture
def project(tmp_path: Path, fake_npm: Path) -> Path:
    """An npm-style project whose ``types`` step reports a failure."""
    (tmp_path / "mcp-coder.toml").write_text(_CONFIG, encoding="utf-8")
    _script(fake_npm, "format", 0, "formatted")
    _script(fake_npm, "lint", 0, "lint clean")
    _script(fake_npm, "types", 1, "src/app.ts:2 type error TS2322")
    _script(fake_npm, "unit", 0, "3 passed")
    return tmp_path


@pytest.fixture(autouse=True)
def command_toolkit_only() -> Generator[MagicMock, None, None]:
    """Resolve every toolkit to ``CommandToolkit``; forbid the Python wrappers."""
    forbidden = MagicMock()
    with (
        patch(
            "mcp_coder.utils.toolkit_runner._toolkit_class",
            lambda _name: CommandToolkit,
        ),
        patch.multiple(mcp_tools_py, **dict.fromkeys(mcp_tools_py.__all__, forbidden)),
    ):
        yield forbidden
    forbidden.assert_not_called()


def test_run_formatters(project: Path) -> None:
    """``format@apply`` runs the format script and succeeds."""
    assert run_formatters(project) is True


def test_implement_final_runs_check_standard_and_test_quick(project: Path) -> None:
    """``implement_final`` runs ``check@standard`` then ``test@quick``.

    The config declares no ``test.quick`` and ``quick`` has no lower depth to
    fall back to, so that request is an ``error`` result.
    """
    results = run_binding(load_toolkit(project), project, "implement_final")

    assert [(request, r.status) for request, r in results] == [
        ("check@standard", "findings"),
        ("test@quick", "error"),
    ]


def test_run_all_checks_reports_keys_and_fix_texts(project: Path) -> None:
    """The failing ``types`` step becomes a key and a ``check`` fix text."""
    keys, fix_texts = _run_all_checks(project)

    assert keys == {"check: types"}
    assert set(fix_texts) == {"check"}
    assert "src/app.ts:2 type error TS2322" in fix_texts["check"]
