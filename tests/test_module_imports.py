"""Import-health check: every ``mcp_coder`` module must import.

The walk runs in a fresh interpreter because test conftests inject mocks into
``sys.modules``; an in-process walk could pass against those mocks.
"""

from __future__ import annotations

import json
import os
import sys
import warnings
from collections.abc import Callable
from pathlib import Path

import pytest

import mcp_coder
from mcp_coder.utils.subprocess_runner import CommandOptions, execute_subprocess
from tests import _import_walker
from tests._import_walker import missing_optional_package, walk

STRICT_ENV_VAR = "MCP_CODER_IMPORT_TEST_STRICT"


def _absent_package() -> BaseException:
    return ModuleNotFoundError(
        "No module named 'nonexistent_pkg_xyz'", name="nonexistent_pkg_xyz"
    )


def _absent_package_submodule() -> BaseException:
    return ModuleNotFoundError(
        "No module named 'nonexistent_pkg_xyz.sub'", name="nonexistent_pkg_xyz.sub"
    )


def _submodule_of_present_package() -> BaseException:
    return ModuleNotFoundError(
        "No module named 'json.nonexistent_sub'", name="json.nonexistent_sub"
    )


def _cannot_import_name() -> BaseException:
    return ImportError("cannot import name 'foo' from 'json'", name="json")


def _import_error_from_module_not_found() -> BaseException:
    try:
        try:
            raise ModuleNotFoundError(
                "No module named 'nonexistent_pkg_xyz'", name="nonexistent_pkg_xyz"
            )
        except ModuleNotFoundError as inner:
            raise ImportError("install extra") from inner
    except ImportError as exc:
        return exc


def _import_error_with_context_module_not_found() -> BaseException:
    try:
        try:
            raise ModuleNotFoundError(
                "No module named 'nonexistent_pkg_xyz'", name="nonexistent_pkg_xyz"
            )
        except ModuleNotFoundError:
            # Implicit chaining is the point: the cause must live on __context__.
            raise ImportError(  # noqa: B904  # pylint: disable=raise-missing-from
                "install extra"
            )
    except ImportError as exc:
        return exc


def _non_import_error() -> BaseException:
    return ValueError("boom")


@pytest.mark.parametrize(
    ("build_exc", "expected"),
    [
        pytest.param(_absent_package, "nonexistent_pkg_xyz", id="absent-package"),
        pytest.param(
            _absent_package_submodule, "nonexistent_pkg_xyz", id="absent-package-sub"
        ),
        pytest.param(_submodule_of_present_package, None, id="present-package-sub"),
        pytest.param(_cannot_import_name, None, id="cannot-import-name"),
        pytest.param(
            _import_error_from_module_not_found,
            "nonexistent_pkg_xyz",
            id="cause-module-not-found",
        ),
        pytest.param(
            _import_error_with_context_module_not_found,
            "nonexistent_pkg_xyz",
            id="context-module-not-found",
        ),
        pytest.param(_non_import_error, None, id="non-import-error"),
    ],
)
def test_missing_optional_package(
    build_exc: Callable[[], BaseException], expected: str | None
) -> None:
    assert missing_optional_package(build_exc()) == expected


def test_walk_records_system_exit_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pkg_dir = tmp_path / "_walker_probe_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
    (pkg_dir / "exits.py").write_text("raise SystemExit(3)\n", encoding="utf-8")
    (pkg_dir / "ok.py").write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        report = walk("_walker_probe_pkg")

        assert [(f["module"], f["type"]) for f in report["failures"]] == [
            ("_walker_probe_pkg.exits", "SystemExit")
        ]
        assert "_walker_probe_pkg.ok" in sys.modules
    finally:
        for name in list(sys.modules):
            if name.startswith("_walker_probe_pkg"):
                sys.modules.pop(name)


def _normalised(paths: list[str]) -> list[str]:
    return [os.path.normcase(str(Path(p).resolve())) for p in paths]


def test_all_mcp_coder_modules_import(tmp_path: Path) -> None:
    report_path = tmp_path / "import_report.json"
    src_parent = str(Path(mcp_coder.__file__).resolve().parent.parent)

    result = execute_subprocess(
        [sys.executable, "-P", str(Path(_import_walker.__file__)), str(report_path)],
        CommandOptions(timeout_seconds=120, env={"PYTHONPATH": src_parent}),
    )

    assert not result.timed_out and result.return_code == 0, (
        f"Import walker failed (return code {result.return_code}, "
        f"timed out: {result.timed_out}):\n{result.stderr[-4000:]}"
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert _normalised(report["package_path"]) == _normalised(list(mcp_coder.__path__))
    failures = "\n".join(
        f"{f['module']}: {f['type']}: {f['message']}" for f in report["failures"]
    )
    assert not report["failures"], f"Modules failed to import:\n{failures}"

    if report["skips"]:
        listing = "Modules skipped (optional package missing):\n" + "\n".join(
            f"{s['module']}: missing {s['missing']}: {s['message']}"
            for s in report["skips"]
        )
        warnings.warn(listing, stacklevel=1)
        if os.environ.get(STRICT_ENV_VAR) == "1":
            pytest.fail(listing)
