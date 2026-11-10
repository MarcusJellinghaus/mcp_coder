"""Tests for the toolkit registry and runner in toolkit_runner."""

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import pytest

from mcp_coder.utils import toolkit_runner
from mcp_coder.utils.toolkit import (
    ActionRequest,
    ActionResult,
    Toolkit,
    ToolkitInfo,
    VerifyItem,
)
from mcp_coder.utils.toolkit_runner import (
    LoadedToolkit,
    _resolve_depth,
    get_fragment,
    load_toolkit,
    load_toolkit_config,
    run_binding,
    run_request,
    verify_toolkit,
)

# Captured at import, before the autouse conftest patch replaces it
_REAL_TOOLKIT_CLASS = toolkit_runner._toolkit_class

CLOSED_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}
PARAMS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"markers": {"type": "string"}, "verbose": {"type": "boolean"}},
    "additionalProperties": False,
}
DEFAULT_ACTIONS: dict[str, list[str]] = {
    "format": ["apply", "check"],
    "check": ["quick", "standard"],
    "test": ["quick", "standard", "unattended"],
}


class FakeToolkit(Toolkit):
    """Configurable fake; class attributes are overridden per test."""

    actions: dict[str, list[str]] = DEFAULT_ACTIONS
    schema: dict[str, Any] = CLOSED_SCHEMA
    result: ActionResult = ActionResult("ok", "fine")
    fragments: dict[str, str] = {}
    fail_init = False
    fail_describe = False
    fail_run = False
    fail_verify = False
    fail_fragments = False

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        if self.fail_init:
            raise RuntimeError("ctor boom")
        super().__init__(config)
        self.requests: list[ActionRequest] = []
        self.verify_calls: list[tuple[Path, str | None]] = []

    def describe(self) -> ToolkitInfo:
        if self.fail_describe:
            raise RuntimeError("describe boom")
        return ToolkitInfo(actions=self.actions, params_schema=self.schema)

    def run(self, request: ActionRequest) -> ActionResult:
        self.requests.append(request)
        if self.fail_run:
            raise RuntimeError("run boom")
        return self.result

    def prompt_fragments(self) -> dict[str, str]:
        if self.fail_fragments:
            raise RuntimeError("fragments boom")
        return self.fragments

    def verify(self, project_dir: Path, action: str | None = None) -> list[VerifyItem]:
        self.verify_calls.append((project_dir, action))
        if self.fail_verify:
            raise RuntimeError("verify boom")
        return [VerifyItem("fake", "ok", "all good")]


def _fake_class(**attrs: Any) -> type[FakeToolkit]:
    return cast(type[FakeToolkit], type("Fake", (FakeToolkit,), attrs))


def _register(monkeypatch: pytest.MonkeyPatch, cls: type[Toolkit]) -> list[str]:
    """Make _toolkit_class return cls; returns the names it was asked for."""
    asked: list[str] = []

    def _lookup(name: str) -> type[Toolkit]:
        asked.append(name)
        return cls

    monkeypatch.setattr(toolkit_runner, "_toolkit_class", _lookup)
    return asked


def _write_config(project_dir: Path, body: str = "") -> None:
    (project_dir / "pyproject.toml").write_text(
        f'[tool.mcp-coder.toolkit]\ntoolkit = "fake"\n{body}', encoding="utf-8"
    )


def _loaded(project_dir: Path, toolkit: Toolkit) -> LoadedToolkit:
    return LoadedToolkit(
        "fake", toolkit, toolkit.describe(), load_toolkit_config(project_dir)
    )


class TestLoadToolkit:
    """Registry lookup, construction, describe and params validation."""

    def test_constructor_receives_section(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The toolkit's own section reaches the constructor."""
        asked = _register(monkeypatch, _fake_class())
        _write_config(tmp_path, "[tool.mcp-coder.toolkit.fake]\nlevel = 3\n")
        loaded = load_toolkit(tmp_path)
        assert asked == ["fake"]
        assert loaded.name == "fake"
        assert dict(loaded.toolkit.config) == {"level": 3}
        assert loaded.info.actions == DEFAULT_ACTIONS
        assert loaded.config.toolkit == "fake"

    def test_unregistered_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No matching entry point → ValueError naming the toolkit."""
        monkeypatch.setattr(toolkit_runner, "_toolkit_class", _REAL_TOOLKIT_CLASS)
        monkeypatch.setattr(toolkit_runner, "entry_points", lambda **_: [])
        _write_config(tmp_path)
        with pytest.raises(ValueError, match="'fake'"):
            load_toolkit(tmp_path)

    def test_constructor_raising(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A constructor exception becomes ValueError."""
        _register(monkeypatch, _fake_class(fail_init=True))
        _write_config(tmp_path)
        with pytest.raises(ValueError, match="ctor boom"):
            load_toolkit(tmp_path)

    def test_describe_raising(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A describe() exception becomes ValueError."""
        _register(monkeypatch, _fake_class(fail_describe=True))
        _write_config(tmp_path)
        with pytest.raises(ValueError, match="describe boom"):
            load_toolkit(tmp_path)

    def test_params_for_undeclared_action(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Params for an action the toolkit doesn't declare → ValueError."""
        _register(monkeypatch, _fake_class(schema=PARAMS_SCHEMA))
        _write_config(tmp_path, "[tool.mcp-coder.toolkit.params]\nlint = {x = 1}\n")
        with pytest.raises(ValueError, match="lint"):
            load_toolkit(tmp_path)

    def test_params_failing_schema(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Params the schema rejects → ValueError."""
        _register(monkeypatch, _fake_class(schema=PARAMS_SCHEMA))
        _write_config(
            tmp_path, '[tool.mcp-coder.toolkit.params]\ntest = {colour = "red"}\n'
        )
        with pytest.raises(ValueError, match="colour"):
            load_toolkit(tmp_path)

    def test_params_reach_request(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Depth table overrides the action table in ActionRequest.params."""
        _register(monkeypatch, _fake_class(schema=PARAMS_SCHEMA))
        _write_config(
            tmp_path,
            "[tool.mcp-coder.toolkit.params.test]\n"
            'markers = "a"\nverbose = true\nquick = {markers = "b"}\n',
        )
        loaded = load_toolkit(tmp_path)
        run_request(loaded, tmp_path, "test@quick")
        run_request(loaded, tmp_path, "test@standard")
        assert isinstance(loaded.toolkit, FakeToolkit)
        # pylint does not narrow on isinstance; mypy does
        requests = loaded.toolkit.requests  # pylint: disable=no-member
        assert dict(requests[0].params) == {"markers": "b", "verbose": True}
        assert dict(requests[1].params) == {"markers": "a", "verbose": True}


@pytest.mark.parametrize(
    ("declared", "depth", "expected"),
    [
        (["quick", "standard"], "standard", "standard"),
        (["quick"], "standard", "quick"),
        (["quick", "standard"], "full", "standard"),
        (["standard"], "quick", None),
        (["quick", "standard"], "unattended", None),
        (["apply"], "check", None),
        (["quick"], "apply", None),
        (["quick"], "mutation", None),
        (["mutation"], "mutation", "mutation"),
    ],
)
def test_resolve_depth(declared: list[str], depth: str, expected: str | None) -> None:
    """Declared runs; standard depths fall back downward; others don't."""
    assert _resolve_depth(declared, depth) == expected


class TestRunRequest:
    """run_request depth fallback and error wrapping."""

    def test_fallback_logs(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An undeclared standard depth runs the nearest lower one, with a log line."""
        toolkit = _fake_class()()
        loaded = _loaded(tmp_path, toolkit)
        with caplog.at_level(logging.INFO, logger=toolkit_runner.__name__):
            result = run_request(loaded, tmp_path, "check@full")
        assert result.status == "ok"
        assert toolkit.requests[0].depth == "standard"
        assert toolkit.requests[0].action == "check"
        assert toolkit.requests[0].project_dir == tmp_path
        assert "depth full not declared, running standard" in caplog.text

    def test_undeclared_action(self, tmp_path: Path) -> None:
        """An action the toolkit doesn't declare → error result, run not called."""
        toolkit = _fake_class()()
        result = run_request(_loaded(tmp_path, toolkit), tmp_path, "lint@quick")
        assert result.status == "error"
        assert "lint@quick" in result.summary
        assert not toolkit.requests

    def test_undeclared_depth(self, tmp_path: Path) -> None:
        """A non-standard undeclared depth → error result."""
        toolkit = _fake_class()()
        result = run_request(_loaded(tmp_path, toolkit), tmp_path, "check@unattended")
        assert result.status == "error"
        assert not toolkit.requests

    def test_run_raising(self, tmp_path: Path) -> None:
        """An exception from run() → error result carrying the message."""
        toolkit = _fake_class(fail_run=True)()
        result = run_request(_loaded(tmp_path, toolkit), tmp_path, "check@quick")
        assert result.status == "error"
        assert "run boom" in result.summary


class TestRunBinding:
    """run_binding over configured entries."""

    def test_order_preserved(self, tmp_path: Path) -> None:
        """Results come back in binding order with their request strings."""
        _write_config(
            tmp_path,
            "[tool.mcp-coder.toolkit.bindings]\n"
            'rebase = ["test@standard", "check@quick"]\n',
        )
        toolkit = _fake_class()()
        results = run_binding(_loaded(tmp_path, toolkit), tmp_path, "rebase")
        assert [r for r, _ in results] == ["test@standard", "check@quick"]
        assert [(q.action, q.depth) for q in toolkit.requests] == [
            ("test", "standard"),
            ("check", "quick"),
        ]
        assert all(res.status == "ok" for _, res in results)

    def test_empty_binding(self, tmp_path: Path) -> None:
        """An empty binding runs nothing."""
        _write_config(
            tmp_path, "[tool.mcp-coder.toolkit.bindings]\nimplement_task = []\n"
        )
        toolkit = _fake_class()()
        assert not run_binding(_loaded(tmp_path, toolkit), tmp_path, "implement_task")
        assert not toolkit.requests


class TestVerifyToolkit:
    """verify_toolkit passes action through and wraps exceptions."""

    def test_passes_action(self, tmp_path: Path) -> None:
        """The action reaches verify() and its items are returned."""
        toolkit = _fake_class()()
        items = verify_toolkit(_loaded(tmp_path, toolkit), tmp_path, "format")
        assert toolkit.verify_calls == [(tmp_path, "format")]
        assert [i.name for i in items] == ["fake"]

    def test_raising(self, tmp_path: Path) -> None:
        """A verify() exception becomes ValueError."""
        toolkit = _fake_class(fail_verify=True)()
        with pytest.raises(ValueError, match="verify boom"):
            verify_toolkit(_loaded(tmp_path, toolkit), tmp_path, None)


class TestGetFragment:
    """get_fragment lookup."""

    def test_present(self, tmp_path: Path) -> None:
        """A contributed fragment is returned."""
        toolkit = _fake_class(fragments={"language_context": "Python"})()
        assert get_fragment(_loaded(tmp_path, toolkit), "language_context") == "Python"

    def test_absent(self, tmp_path: Path) -> None:
        """A missing fragment → empty string."""
        toolkit = _fake_class()()
        assert get_fragment(_loaded(tmp_path, toolkit), "language_context") == ""

    def test_raising(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """prompt_fragments() raising → empty string and a warning."""
        toolkit = _fake_class(fail_fragments=True)()
        with caplog.at_level(logging.WARNING, logger=toolkit_runner.__name__):
            assert get_fragment(_loaded(tmp_path, toolkit), "x") == ""
        assert "fragments boom" in caplog.text


def test_real_toolkit_test_unattended(tmp_path: Path) -> None:
    """PythonToolkit reports the failing test as the single finding."""
    from mcp_tools_py.toolkit import PythonToolkit

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_fail.py").write_text(
        "def test_pass():\n    assert True\n\n\ndef test_fail():\n    assert False\n",
        encoding="utf-8",
    )
    toolkit = PythonToolkit()
    loaded = LoadedToolkit(
        "mcp-tools-py", toolkit, toolkit.describe(), load_toolkit_config(tmp_path)
    )
    result = run_request(loaded, tmp_path, "test@unattended")
    assert result.status == "findings", result.summary
    assert [f.key for f in result.findings] == ["tests/test_fail.py::test_fail"]
