"""Unit tests for the pure dependency-check module ``mcp_coder._depcheck``.

These tests exercise ``find_missing_dependencies`` and ``ensure_dependencies``
using a single patch seam: ``mcp_coder._depcheck.requires``. The real
``importlib.metadata.version`` lookup is relied on to report a bogus
distribution as absent, so no import-name<->dist-name map is needed.
"""

from importlib.metadata import PackageNotFoundError

import pytest

from mcp_coder import _depcheck


def test_missing_metadata_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """``requires`` raising ``PackageNotFoundError`` -> ``[]`` (fail-open)."""

    def _raise(_name: str) -> list[str]:
        raise PackageNotFoundError("mcp-coder")

    monkeypatch.setattr(_depcheck, "requires", _raise)
    assert _depcheck.find_missing_dependencies() == []


def test_requires_none_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """``requires`` returning ``None`` -> ``[]`` (nothing to enumerate)."""
    monkeypatch.setattr(_depcheck, "requires", lambda _name: None)
    assert _depcheck.find_missing_dependencies() == []


def test_absent_dependency_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    """A declared, genuinely-absent distribution is reported as missing."""
    monkeypatch.setattr(
        _depcheck, "requires", lambda _name: ["definitely-absent-xyz>=1"]
    )
    assert _depcheck.find_missing_dependencies() == ["definitely-absent-xyz"]


def test_extra_marker_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    """An ``extra`` marker evaluates ``False`` via explicit ``extra=""``.

    This must hold regardless of the installed ``packaging`` version, so it
    guards against the fail-open regression rather than silently erroring.
    """
    monkeypatch.setattr(
        _depcheck, "requires", lambda _name: ["some-pkg; extra == 'dev'"]
    )
    assert _depcheck.find_missing_dependencies() == []


def test_invalid_spec_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unparseable spec is skipped; a genuinely-missing dep is still found."""
    monkeypatch.setattr(
        _depcheck,
        "requires",
        lambda _name: ["not a valid spec!!!", "definitely-absent-xyz>=1"],
    )
    assert _depcheck.find_missing_dependencies() == ["definitely-absent-xyz"]


def test_ensure_dependencies_healthy_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No missing deps -> ``ensure_dependencies`` returns ``None``, no exit."""
    monkeypatch.setattr(_depcheck, "find_missing_dependencies", lambda: [])
    # Returns without raising SystemExit on a healthy env.
    _depcheck.ensure_dependencies()


def test_ensure_dependencies_exits_on_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing deps -> ``SystemExit(1)`` with a friendly stderr message."""
    monkeypatch.setattr(
        _depcheck,
        "find_missing_dependencies",
        lambda: ["python-jenkins", "textual"],
    )
    with pytest.raises(SystemExit) as exc_info:
        _depcheck.ensure_dependencies()
    assert exc_info.value.code == 1

    stderr = capsys.readouterr().err
    assert "mcp-coder " in stderr
    assert "Installation incomplete" in stderr
    assert "python-jenkins" in stderr
    assert "textual" in stderr
    assert "pip install mcp-coder" in stderr
