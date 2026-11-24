"""Tests for toolkit_rows: per-action verify items, global items, depth rows."""

import re
from collections.abc import Callable, Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.verify_render import SectionBuilder
from mcp_coder.cli.commands.verify_toolkit_rows import _requests, toolkit_rows
from mcp_coder.toolkits.command import CommandToolkit
from mcp_coder.utils.toolkit import (
    ActionRequest,
    ActionResult,
    Toolkit,
    ToolkitInfo,
    VerifyItem,
)
from mcp_coder.utils.toolkit_runner import DEFAULT_BINDINGS, verify_toolkit

_SYMBOLS = {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}
_VERIFY_TOOLKIT = "mcp_coder.cli.commands.verify_toolkit_rows.verify_toolkit"
_TOOLKIT_CLASS = "mcp_coder.utils.toolkit_runner._toolkit_class"
_SCHEMA = {"type": "object", "properties": {}, "additionalProperties": False}

# Every depth the default bindings request
_ALL_DEPTHS: dict[str, list[str]] = {
    "format": ["apply"],
    "check": ["quick", "standard"],
    "test": ["quick", "standard", "unattended"],
}

_ONLY_CHECK = (
    'implement_task = ["check@quick"]\n'
    'implement_final = ["check@standard"]\n'
    "commit = []\n"
    'rebase = ["check@standard"]\n'
    'rebase_automated = ["check@standard"]\n'
)

VerifyResult = list[VerifyItem] | Exception


def _toolkit(actions: dict[str, list[str]]) -> type[Toolkit]:
    """Return a toolkit class declaring *actions*."""

    class _Fake(Toolkit):
        def describe(self) -> ToolkitInfo:
            return ToolkitInfo(actions=actions, params_schema=_SCHEMA)

        def run(self, request: ActionRequest) -> ActionResult:
            return ActionResult("ok", "")

    return _Fake


def _verify(
    per_action: dict[str, VerifyResult], calls: list[str]
) -> Callable[[object, Path, str], list[VerifyItem]]:
    """Return a verify_toolkit stand-in answering per action and recording calls."""

    def _fake(_loaded: object, _project_dir: Path, action: str) -> list[VerifyItem]:
        calls.append(action)
        result = per_action.get(action, [])
        if isinstance(result, Exception):
            raise result
        return list(result)

    return _fake


class _Run:
    """Result of one toolkit_rows run."""

    def __init__(self, ok: bool, lines: list[str], calls: list[str]) -> None:
        self.ok = ok
        self.lines = lines
        self.calls = calls

    def row(self, label: str) -> str:
        """Return the single row whose label field is *label*."""
        matches = [line for line in self.lines if line.strip().startswith(label + " ")]
        assert len(matches) == 1, f"expected exactly one {label!r} row, got {matches!r}"
        return matches[0]

    def has_row(self, label: str) -> bool:
        """Return True if any row's label field is *label*."""
        return any(line.strip().startswith(label + " ") for line in self.lines)


@pytest.fixture
def run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Callable[..., _Run]:
    """Run toolkit_rows for a fake toolkit with the given bindings and verify items."""

    def _run(
        *,
        bindings: str = "",
        actions: dict[str, list[str]] | None = None,
        verify: dict[str, VerifyResult] | None = None,
        format_code: bool = True,
    ) -> _Run:
        toml = '[tool.mcp-coder.toolkit]\ntoolkit = "fake"\n'
        if bindings:
            toml += "[tool.mcp-coder.toolkit.bindings]\n" + bindings
        (tmp_path / "mcp-coder.toml").write_text(toml, encoding="utf-8")
        if not format_code:
            (tmp_path / "pyproject.toml").write_text(
                "[tool.mcp-coder]\nformat_code = false\n", encoding="utf-8"
            )
        calls: list[str] = []
        cls = _toolkit(_ALL_DEPTHS if actions is None else actions)
        with (
            patch(_TOOLKIT_CLASS, lambda _name: cls),
            patch(_VERIFY_TOOLKIT, _verify(verify or {}, calls)),
        ):
            ok = toolkit_rows(tmp_path, _SYMBOLS, SectionBuilder())
        return _Run(ok, capsys.readouterr().out.splitlines(), calls)

    return _run


def test_requests_default_bindings() -> None:
    """One entry per distinct request, naming every requesting binding."""
    requests = _requests(DEFAULT_BINDINGS, formatting=True)
    assert requests == {
        ("check", "quick"): ["implement_task"],
        ("check", "standard"): ["implement_final", "rebase", "rebase_automated"],
        ("test", "quick"): ["implement_final"],
        ("format", "apply"): ["commit"],
        ("test", "standard"): ["rebase"],
        ("test", "unattended"): ["rebase_automated"],
    }


def test_requests_commit_only_while_formatting() -> None:
    """``commit`` requests are dropped while format_code is off."""
    assert ("format", "apply") not in _requests(DEFAULT_BINDINGS, formatting=False)


class TestDepthRows:
    """One row per requested depth the toolkit doesn't declare."""

    def test_one_row_per_request_names_every_binding(
        self, run: Callable[..., _Run]
    ) -> None:
        result = run(actions={"format": ["apply"], "check": ["quick"], "test": []})
        row = result.row("check@standard")
        assert "[WARN]" in row
        assert (
            "not declared; runs quick"
            " (requested by implement_final, rebase, rebase_automated)"
        ) in row

    def test_undeclared_full_runs_standard(self, run: Callable[..., _Run]) -> None:
        result = run(bindings='implement_task = ["check@full"]\n')
        assert result.ok is True
        row = result.row("check@full")
        assert "[WARN]" in row
        assert "not declared; runs standard (requested by implement_task)" in row

    def test_undeclared_unattended_is_error(self, run: Callable[..., _Run]) -> None:
        actions = {**_ALL_DEPTHS, "test": ["quick", "standard"]}
        result = run(actions=actions)
        assert result.ok is False
        row = result.row("test@unattended")
        assert "[ERR]" in row
        assert "not declared (requested by rebase_automated)" in row

    def test_declared_depth_has_ok_row(self, run: Callable[..., _Run]) -> None:
        result = run()
        assert result.ok is True
        depth_rows = [line for line in result.lines if "@" in line]
        assert len(depth_rows) == 6
        assert all("[OK]" in line for line in depth_rows)
        assert "requested by implement_final, rebase, rebase_automated" in result.row(
            "check@standard"
        )

    def test_undeclared_action_is_error_and_not_verified(
        self, run: Callable[..., _Run]
    ) -> None:
        actions = {k: v for k, v in _ALL_DEPTHS.items() if k != "test"}
        result = run(actions=actions)
        assert result.ok is False
        assert "test" not in result.calls
        for depth, binding in (
            ("quick", "implement_final"),
            ("standard", "rebase"),
            ("unattended", "rebase_automated"),
        ):
            row = result.row(f"test@{depth}")
            assert "[ERR]" in row
            assert (
                f"action not declared by toolkit 'fake' (requested by {binding})" in row
            )


class TestGlobalItems:
    """Items shared by every returning action are shown once, under Toolkit."""

    def test_shared_error_shown_once(self, run: Callable[..., _Run]) -> None:
        env = VerifyItem("environment", "error", "no interpreter")
        result = run(bindings="commit = []\n", verify={"check": [env], "test": [env]})
        assert result.ok is False
        row = result.row("environment")
        assert row.startswith("      environment ")
        assert "[ERR]" in row

    def test_check_only_error_is_warning(self, run: Callable[..., _Run]) -> None:
        result = run(
            bindings="commit = []\n",
            verify={"check": [VerifyItem("ruff", "error", "missing")]},
        )
        assert result.ok is True
        row = result.row("ruff")
        assert row.startswith("        ruff ")
        assert "[WARN]" in row

    def test_format_error_keeps_severity(self, run: Callable[..., _Run]) -> None:
        result = run(verify={"format": [VerifyItem("black", "error", "missing")]})
        assert result.ok is False
        assert "[ERR]" in result.row("black")

    def test_one_action_returning_keeps_severity(
        self, run: Callable[..., _Run]
    ) -> None:
        result = run(
            bindings=_ONLY_CHECK,
            verify={"check": [VerifyItem("ruff", "error", "missing")]},
        )
        assert result.calls == ["check"]
        assert result.ok is False
        assert "[ERR]" in result.row("ruff")


class TestVerifyRaising:
    """A raising verify() is reported in its action's group."""

    def test_check_raising_is_warning_and_excluded(
        self, run: Callable[..., _Run]
    ) -> None:
        env = VerifyItem("environment", "ok")
        result = run(
            verify={
                "check": ValueError("verify failed: boom"),
                "format": [env],
                "test": [env],
            }
        )
        assert result.ok is True
        row = result.row("verify")
        assert row.startswith("        verify ")
        assert "[WARN]" in row
        assert "boom" in row
        # Lifted as global although check returned nothing
        assert result.row("environment").startswith("      environment ")

    def test_format_raising_is_error(self, run: Callable[..., _Run]) -> None:
        result = run(verify={"format": ValueError("verify failed: boom")})
        assert result.ok is False
        assert "[ERR]" in result.row("verify")
        assert "[OK]" in result.row("Toolkit")


class TestLayout:
    """Action groups, headers and the formatter item."""

    def test_format_code_false_skips_format(self, run: Callable[..., _Run]) -> None:
        actions = {k: v for k, v in _ALL_DEPTHS.items() if k != "format"}
        result = run(actions=actions, format_code=False)
        assert result.ok is True
        assert "format" not in result.calls
        assert not result.has_row("format@apply")

    def test_formatter_item_shown(self, run: Callable[..., _Run]) -> None:
        result = run(verify={"format": [VerifyItem("formatter", "ok")]})
        assert result.ok is True
        assert result.row("formatter").startswith("        formatter ")
        assert "      format" in result.lines

    def test_every_header_has_rows(self, run: Callable[..., _Run]) -> None:
        result = run()
        assert sorted(result.calls) == ["check", "format", "test"]
        assert result.row("Toolkit").startswith("    Toolkit ")
        headers = [
            index
            for index, line in enumerate(result.lines)
            if line.strip() in ("format", "check", "test")
        ]
        assert len(headers) == 3
        for index in headers:
            assert result.lines[index + 1].startswith("        ")

    def test_global_items_not_repeated_in_groups(
        self, run: Callable[..., _Run]
    ) -> None:
        env = VerifyItem("environment", "ok")
        result = run(verify={"format": [env], "check": [env], "test": [env]})
        assert result.lines[1].startswith("      environment ")
        assert result.row("environment")

    def test_other_toolkit_unrequested_depth_has_no_row(
        self, run: Callable[..., _Run]
    ) -> None:
        actions = {**_ALL_DEPTHS, "check": ["quick", "standard", "full"]}
        result = run(actions=actions)
        assert result.ok is True
        assert not result.has_row("check@full")
        assert "[WARN]" not in "\n".join(result.lines)
        for label in (
            "format@apply",
            "check@quick",
            "check@standard",
            "test@quick",
            "test@standard",
            "test@unattended",
        ):
            assert "[OK]" in result.row(label)


_COMMAND_TOML = (
    '[tool.mcp-coder.toolkit]\ntoolkit = "command"\n'
    "[tool.mcp-coder.toolkit.command.format]\n"
    'apply = [{argv = ["fakenpm", "fmt"]}]\n'
    "[tool.mcp-coder.toolkit.command.check]\n"
    'quick = [{argv = ["fakenpm", "lint"]}]\n'
    'standard = [{argv = ["fakenpm", "lint"]}]\n'
    "[tool.mcp-coder.toolkit.command.test]\n"
    'quick = [{argv = ["fakenpm", "test"]}]\n'
    'standard = [{argv = ["fakenpm", "test"]}]\n'
    'unattended = [{argv = ["fakenpm", "test"]}]\n'
)


@pytest.fixture
def command_project(tmp_path: Path, fake_npm: Path) -> Generator[Path, None, None]:
    """A ``command`` project declaring every requested depth; no mcp-tools-py."""
    for name in ("fmt", "lint", "test"):
        (fake_npm / f"{name}.py").write_text("", encoding="utf-8")
    (tmp_path / "mcp-coder.toml").write_text(_COMMAND_TOML, encoding="utf-8")
    with (
        patch(_TOOLKIT_CLASS, lambda name: {"command": CommandToolkit}[name]),
        patch(_VERIFY_TOOLKIT, verify_toolkit),
    ):
        yield tmp_path


def test_command_project_passes(
    command_project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every requested depth declared → no error, without mcp-tools-py."""
    assert toolkit_rows(command_project, _SYMBOLS, SectionBuilder()) is True
    lines = capsys.readouterr().out.splitlines()
    assert not any("[ERR]" in line for line in lines)
    depth_rows = [line for line in lines if re.match(r"\s+[a-z]+@[a-z]+ ", line)]
    assert len(depth_rows) == 6
    assert all("[OK]" in line for line in depth_rows)


# Default-binding depths plus depths no binding requests
_DECLARED_TOML = (
    '[tool.mcp-coder.toolkit]\ntoolkit = "command"\n'
    "[tool.mcp-coder.toolkit.command.check]\n"
    'quick = [{argv = ["fakenpm", "lint"]}]\n'
    'standard = [{argv = ["fakenpm", "lint"]}]\n'
    'full = [{argv = ["fakenpm", "lint"]}]\n'
    "[tool.mcp-coder.toolkit.command.test]\n"
    'quick = [{argv = ["fakenpm", "test"]}]\n'
    'unattended = [{argv = ["fakenpm", "test"]}]\n'
    'mutation = [{argv = ["fakenpm", "mutate"]}]\n'
    "[tool.mcp-coder.toolkit.command.format]\n"
    'apply = [{argv = ["fakenpm", "fmt"]}]\n'
    'check = [{argv = ["fakenpm", "fmt"]}]\n'
)


@pytest.fixture
def declared_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> Callable[..., _Run]:
    """Run toolkit_rows for a command toolkit declaring unrequested depths."""

    def _run(*, format_code: bool = True) -> _Run:
        (tmp_path / "mcp-coder.toml").write_text(_DECLARED_TOML, encoding="utf-8")
        if not format_code:
            (tmp_path / "pyproject.toml").write_text(
                "[tool.mcp-coder]\nformat_code = false\n", encoding="utf-8"
            )
        calls: list[str] = []
        with (
            patch(_TOOLKIT_CLASS, lambda name: {"command": CommandToolkit}[name]),
            patch(_VERIFY_TOOLKIT, _verify({}, calls)),
        ):
            ok = toolkit_rows(tmp_path, _SYMBOLS, SectionBuilder())
        return _Run(ok, capsys.readouterr().out.splitlines(), calls)

    return _run


class TestDeclaredDepths:
    """One row per depth the command toolkit declares."""

    @pytest.mark.parametrize(
        ("label", "entries"),
        [
            ("check@quick", "implement_task"),
            ("check@standard", "implement_final, rebase, rebase_automated"),
            ("test@quick", "implement_final, rebase"),
            ("test@unattended", "rebase_automated"),
            ("format@apply", "commit"),
        ],
    )
    def test_requested_depth_is_ok(
        self, declared_run: Callable[..., _Run], label: str, entries: str
    ) -> None:
        row = declared_run().row(label)
        assert "[OK]" in row
        assert row.endswith(f"requested by {entries}")

    @pytest.mark.parametrize("label", ["check@full", "test@mutation"])
    def test_unrequested_depth_warns(
        self, declared_run: Callable[..., _Run], label: str
    ) -> None:
        result = declared_run()
        assert result.ok is True
        row = result.row(label)
        assert "[WARN]" in row
        assert row.endswith(
            "not requested by any binding; delete it or add it to a binding"
        )

    def test_unrequestable_depth_warns(self, declared_run: Callable[..., _Run]) -> None:
        row = declared_run().row("format@check")
        assert "[WARN]" in row
        assert row.endswith("no binding can request it; delete it")

    def test_fallback_warning_unchanged(
        self, declared_run: Callable[..., _Run]
    ) -> None:
        row = declared_run().row("test@standard")
        assert "[WARN]" in row
        assert "not declared; runs quick (requested by rebase)" in row

    def test_format_code_off(self, declared_run: Callable[..., _Run]) -> None:
        result = declared_run(format_code=False)
        assert result.ok is True
        assert "format" not in result.calls
        assert "      format" in result.lines
        apply_row = result.row("format@apply")
        assert "[WARN]" in apply_row
        assert apply_row.endswith("unused while format_code is off")
        assert result.row("format@check").endswith(
            "no binding can request it; delete it"
        )
