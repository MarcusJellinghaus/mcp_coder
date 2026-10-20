"""Unit tests for tools/tach_docs.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

_TOOL_PY = Path(__file__).resolve().parents[2] / "tools" / "tach_docs.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("tach_docs", _TOOL_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tach_docs = _load()


def test_main_writes_no_crlf_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Generated HTML has LF-only bytes even if the generators emit CRLF."""
    monkeypatch.setattr(tach_docs, "__file__", str(tmp_path / "tools" / "tach_docs.py"))
    monkeypatch.setattr(tach_docs, "get_mermaid_diagram", lambda: "graph")
    monkeypatch.setattr(
        tach_docs,
        "generate_graph_html",
        lambda _diagram: "<html>\r\ngraph\r\n</html>\r\n",
    )
    monkeypatch.setattr(tach_docs, "get_dependency_report", lambda _module: "report")
    monkeypatch.setattr(
        tach_docs,
        "generate_report_html",
        lambda _reports: "<html>\r\nreport\r\n</html>\r\n",
    )

    assert tach_docs.main() == 0

    out = tmp_path / "docs" / "architecture"
    for name in ("dependency_graph.html", "dependency_report.html"):
        assert b"\r" not in (out / name).read_bytes()
