"""Unit tests for tools/check_forbidden_calls.py.

Fixture strings only; these tests do not scan the repository.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

_TOOL_PY = Path(__file__).resolve().parents[2] / "tools" / "check_forbidden_calls.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_forbidden_calls", _TOOL_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_forbidden_calls = _load()
find_violations = check_forbidden_calls.find_violations
scan = check_forbidden_calls.scan


def test_git_argv_single_line() -> None:
    hits = find_violations("src/mcp_coder/x.py", 'execute_command(["git", "status"])\n')
    assert len(hits) == 1
    assert hits[0].startswith("src/mcp_coder/x.py:1: [git]")


def test_git_argv_multi_line_reports_bracket_line() -> None:
    text = 'import os\n\ncmd = [\n    "git",\n    "fetch",\n]\n'
    hits = find_violations("src/mcp_coder/x.py", text)
    assert len(hits) == 1
    assert hits[0].startswith("src/mcp_coder/x.py:3: [git]")


def test_git_operations_import_excluded_in_shim() -> None:
    text = "from mcp_workspace.git_operations.core import X\n"
    assert find_violations("src/mcp_coder/mcp_workspace_git.py", text) == []


def test_git_operations_import_elsewhere_is_hit() -> None:
    text = "from mcp_workspace.git_operations.core import X\n"
    hits = find_violations("src/mcp_coder/other.py", text)
    assert len(hits) == 1
    assert "[workspace-git-direct-import]" in hits[0]


def test_github_operations_import_excluded_in_shim() -> None:
    text = "from mcp_workspace.github_operations.pr_manager import X\n"
    assert find_violations("src/mcp_coder/mcp_workspace_github.py", text) == []


def test_github_operations_import_elsewhere_is_hit() -> None:
    text = "from mcp_workspace.github_operations.pr_manager import X\n"
    hits = find_violations("src/mcp_coder/other.py", text)
    assert len(hits) == 1
    assert "[workspace-github-direct-import]" in hits[0]


def test_path_outside_src_is_not_scanned() -> None:
    assert find_violations("tests/test_x.py", 'run(["git", "init"])\n') == []


def test_clean_file() -> None:
    assert (
        find_violations("src/mcp_coder/x.py", "def f() -> int:\n    return 1\n") == []
    )


def test_scan_empty_src_tree(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    assert scan(tmp_path) == []


def test_scan_finds_offending_file(tmp_path: Path) -> None:
    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "clean.py").write_text("x = 1\n", encoding="utf-8")
    (pkg / "bad.py").write_text('cmd = ["git", "log"]\n', encoding="utf-8")
    hits = scan(tmp_path)
    assert hits == [
        "src/pkg/bad.py:1: [git] use `mcp_coder.mcp_workspace_git`",
    ]


def test_main_exit_codes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "src").mkdir()
    monkeypatch.setattr(check_forbidden_calls, "_repo_root", lambda: tmp_path)
    assert check_forbidden_calls.main() == 0

    (tmp_path / "src" / "bad.py").write_text('["git", "x"]\n', encoding="utf-8")
    assert check_forbidden_calls.main() == 1
