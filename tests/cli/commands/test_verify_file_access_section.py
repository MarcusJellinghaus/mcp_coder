"""Tests for the FILE ACCESS section: reference lookup, rows and verify wiring."""

import json
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands import verify, verify_sections
from mcp_coder.cli.commands.verify import execute_verify
from mcp_coder.mcp_workspace import verify_file_access
from mcp_coder.utils.verify_render import SectionBuilder
from tests.cli.commands.conftest import (
    _assert_section_aligned,
    _make_args,
    _make_verify_mocks,
)

_SYMBOLS = {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}


def _write_mcp_json(path: Path, data: Any) -> str:
    """Write *data* as ``.mcp.json`` under *path*; return the file path."""
    mcp_json = path / ".mcp.json"
    mcp_json.write_text(json.dumps(data), encoding="utf-8")
    return str(mcp_json)


def _workspace_server(*args: str) -> dict[str, Any]:
    """An ``.mcp.json`` document with one mcp-workspace server using *args*."""
    return {"mcpServers": {"mcp-workspace": {"command": "x", "args": list(args)}}}


def _squash(text: str) -> str:
    """Collapse runs of whitespace, so rows compare independent of padding."""
    return " ".join(text.split())


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Workspace directory, a sibling of the reference directories."""
    ws = tmp_path / "ws"
    ws.mkdir()
    return ws


def _ref_dir(tmp_path: Path, name: str, rules: str | None = None) -> Path:
    """Create a reference directory, optionally with a rules file."""
    ref = tmp_path / name
    ref.mkdir()
    if rules is not None:
        (ref / ".mcp-file-access").write_text(rules, encoding="utf-8")
    return ref


class TestLookupReferenceProjects:
    """``_lookup_reference_projects`` reads the mcp-workspace server args."""

    def test_none_path(self, workspace: Path) -> None:
        assert verify_sections._lookup_reference_projects(workspace, None, None) == (
            [],
            [],
        )

    def test_missing_file(self, workspace: Path) -> None:
        missing = str(workspace / ".mcp.json")
        assert verify_sections._lookup_reference_projects(workspace, missing, None) == (
            [],
            [],
        )

    def test_malformed_json(self, workspace: Path) -> None:
        mcp_json = workspace / ".mcp.json"
        mcp_json.write_text("{not json", encoding="utf-8")
        assert verify_sections._lookup_reference_projects(
            workspace, str(mcp_json), None
        ) == ([], [])

    @pytest.mark.parametrize(
        "data",
        [
            [],
            {"mcpServers": []},
            {"mcpServers": {"other": {"args": ["--reference-project", "x"]}}},
            {"mcpServers": {"mcp-workspace": {"args": "--reference-project"}}},
            {"mcpServers": {"mcp-workspace": []}},
        ],
        ids=["not-object", "servers-list", "no-server", "args-str", "server-list"],
    )
    def test_no_usable_server(self, workspace: Path, data: Any) -> None:
        path = _write_mcp_json(workspace, data)
        assert verify_sections._lookup_reference_projects(workspace, path, None) == (
            [],
            [],
        )

    def test_separate_value_form(self, tmp_path: Path, workspace: Path) -> None:
        ref = _ref_dir(tmp_path, "a")
        path = _write_mcp_json(
            workspace, _workspace_server("--reference-project", f"name=a,path={ref}")
        )
        assert verify_sections._lookup_reference_projects(workspace, path, None) == (
            [("a", ref.resolve())],
            [],
        )

    def test_equals_form_and_order(self, tmp_path: Path, workspace: Path) -> None:
        refs = [_ref_dir(tmp_path, n) for n in ("a", "b", "c")]
        path = _write_mcp_json(
            workspace,
            _workspace_server(
                "--reference-project",
                f"name=a,path={refs[0]}",
                f"--reference-project=name=b,path={refs[1]}",
                "--reference-project",
                f"name=c,path={refs[2]}",
            ),
        )
        accepted, rejected = verify_sections._lookup_reference_projects(
            workspace, path, None
        )
        assert accepted == [(n, r.resolve()) for n, r in zip("abc", refs, strict=True)]
        assert rejected == []

    def test_placeholder_resolved(self, tmp_path: Path, workspace: Path) -> None:
        ref = _ref_dir(tmp_path, "a")
        path = _write_mcp_json(
            workspace,
            _workspace_server("--reference-project", "name=a,path=${REF_DIR}"),
        )
        assert verify_sections._lookup_reference_projects(
            workspace, path, {"REF_DIR": str(ref)}
        ) == ([("a", ref.resolve())], [])

    def test_other_args_ignored(self, tmp_path: Path, workspace: Path) -> None:
        ref = _ref_dir(tmp_path, "a")
        path = _write_mcp_json(
            workspace,
            _workspace_server(
                "--project-dir",
                str(tmp_path / "elsewhere"),
                "--log-level",
                "DEBUG",
                "--reference-project",
                f"name=a,path={ref}",
            ),
        )
        assert verify_sections._lookup_reference_projects(workspace, path, None) == (
            [("a", ref.resolve())],
            [],
        )

    def test_missing_path_without_url_rejected(
        self, tmp_path: Path, workspace: Path
    ) -> None:
        path = _write_mcp_json(
            workspace,
            _workspace_server(
                "--reference-project", f"name=a,path={tmp_path / 'missing'}"
            ),
        )
        assert verify_sections._lookup_reference_projects(workspace, path, None) == (
            [],
            [("a", "path not found")],
        )

    def test_same_directory_as_workspace_rejected(self, workspace: Path) -> None:
        path = _write_mcp_json(
            workspace,
            _workspace_server("--reference-project", f"name=a,path={workspace}"),
        )
        assert verify_sections._lookup_reference_projects(workspace, path, None) == (
            [],
            [("a", "same directory as workspace")],
        )


@pytest.fixture
def real_file_access() -> Generator[None, None, None]:
    """Use the real ``verify_file_access`` instead of the conftest default."""
    with patch(f"{verify.__name__}.verify_file_access", verify_file_access):
        yield


def _section(workspace: Path, capsys: pytest.CaptureFixture[str]) -> tuple[bool, str]:
    """Run the FILE ACCESS printer; return its result and the printed text."""
    ok = verify._print_file_access_section(
        workspace, "/fake/.mcp.json", {}, _SYMBOLS, SectionBuilder()
    )
    return ok, capsys.readouterr().out


def _rows(text: str) -> list[str]:
    """Marker-bearing lines, whitespace-squashed."""
    return [
        _squash(line)
        for line in text.splitlines()
        if any(m in line for m in _SYMBOLS.values())
    ]


@pytest.mark.usefixtures("real_file_access")
class TestPrintFileAccessSection:
    """``_print_file_access_section`` renders the mcp-workspace verify rows."""

    def test_workspace_without_rules_file(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, text = _section(workspace, capsys)
        assert ok is True
        assert "=== FILE ACCESS" in text
        assert _rows(text) == ["workspace [OK] absent - gitignore only"]

    def test_workspace_valid_rules(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (workspace / ".mcp-file-access").write_text(
            "read-write /.scratch/\n", encoding="utf-8"
        )
        ok, text = _section(workspace, capsys)
        assert ok is True
        assert _rows(text) == ["workspace [OK] 1 rules"]

    def test_workspace_invalid_rules(
        self, workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (workspace / ".mcp-file-access").write_text("writable /x\n", encoding="utf-8")
        ok, text = _section(workspace, capsys)
        assert ok is False
        assert _squash(text).count("workspace [ERR] invalid (") == 1

    def test_accepted_ref_valid_rules(
        self,
        tmp_path: Path,
        workspace: Path,
        capsys: pytest.CaptureFixture[str],
        _mock_lookup_reference_projects: MagicMock,
    ) -> None:
        ref = _ref_dir(tmp_path, "ref", "read-write /.scratch/\n")
        _mock_lookup_reference_projects.return_value = ([("myref", ref)], [])
        ok, text = _section(workspace, capsys)
        assert ok is True
        assert _rows(text)[1] == "myref [OK] 1 rules"

    def test_accepted_ref_invalid_rules(
        self,
        tmp_path: Path,
        workspace: Path,
        capsys: pytest.CaptureFixture[str],
        _mock_lookup_reference_projects: MagicMock,
    ) -> None:
        ref = _ref_dir(tmp_path, "ref", "writable /x\n")
        _mock_lookup_reference_projects.return_value = ([("myref", ref)], [])
        ok, text = _section(workspace, capsys)
        assert ok is False
        assert "myref [ERR] invalid (" in _squash(text)

    def test_accepted_ref_missing_path(
        self,
        tmp_path: Path,
        workspace: Path,
        capsys: pytest.CaptureFixture[str],
        _mock_lookup_reference_projects: MagicMock,
    ) -> None:
        _mock_lookup_reference_projects.return_value = (
            [("gone", tmp_path / "missing")],
            [],
        )
        ok, text = _section(workspace, capsys)
        assert ok is True
        assert _rows(text)[1] == "gone [WARN] path not found"

    def test_rejected_ref(
        self,
        workspace: Path,
        capsys: pytest.CaptureFixture[str],
        _mock_lookup_reference_projects: MagicMock,
    ) -> None:
        _mock_lookup_reference_projects.return_value = ([], [("bad", "missing path")])
        ok, text = _section(workspace, capsys)
        assert ok is False
        assert _rows(text)[1] == "bad [ERR] rejected: missing path"

    def test_lookup_raises(
        self,
        workspace: Path,
        capsys: pytest.CaptureFixture[str],
        _mock_lookup_reference_projects: MagicMock,
    ) -> None:
        _mock_lookup_reference_projects.side_effect = ValueError("URL mismatch")
        ok, text = _section(workspace, capsys)
        assert ok is False
        assert _rows(text) == [
            "workspace [OK] absent - gitignore only",
            "reference projects [ERR] URL mismatch",
        ]

    def test_order_and_alignment(
        self,
        tmp_path: Path,
        workspace: Path,
        capsys: pytest.CaptureFixture[str],
        _mock_lookup_reference_projects: MagicMock,
    ) -> None:
        second = _ref_dir(tmp_path, "second", "read-write /.scratch/\n")
        first = _ref_dir(tmp_path, "first")
        _mock_lookup_reference_projects.return_value = (
            [("zeta", second), ("alpha", first), ("gone", tmp_path / "missing")],
            [("bad", "missing path")],
        )
        ok, text = _section(workspace, capsys)
        assert ok is False
        assert [row.split()[0] for row in _rows(text)] == [
            "workspace",
            "zeta",
            "alpha",
            "gone",
            "bad",
        ]
        assert _assert_section_aligned(text) == 5


class TestExecuteVerifyFileAccess:
    """execute_verify prints FILE ACCESS and feeds it into the exit code."""

    def test_section_order(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with _make_verify_mocks():
            execute_verify(_make_args(project_dir=str(tmp_path)))
        lines = capsys.readouterr().out.splitlines()

        def _header(prefix: str) -> int:
            return next(i for i, line in enumerate(lines) if line.startswith(prefix))

        assert (
            _header("=== PROJECT ") < _header("=== FILE ACCESS ") < _header("=== GIT ")
        )

    def test_rejected_reference_exits_1(
        self, tmp_path: Path, _mock_lookup_reference_projects: MagicMock
    ) -> None:
        _mock_lookup_reference_projects.return_value = ([], [("bad", "missing path")])
        with _make_verify_mocks():
            assert execute_verify(_make_args(project_dir=str(tmp_path))) == 1

    def test_missing_reference_path_exits_0(
        self, tmp_path: Path, _mock_lookup_reference_projects: MagicMock
    ) -> None:
        _mock_lookup_reference_projects.return_value = (
            [("gone", tmp_path / "missing")],
            [],
        )
        with _make_verify_mocks():
            assert execute_verify(_make_args(project_dir=str(tmp_path))) == 0

    def test_lookup_arguments(
        self, tmp_path: Path, _mock_lookup_reference_projects: MagicMock
    ) -> None:
        with _make_verify_mocks():
            execute_verify(_make_args(project_dir=str(tmp_path)))
        _mock_lookup_reference_projects.assert_called_once_with(
            tmp_path.resolve(), "/fake/.mcp.json", {"K": "V"}
        )
