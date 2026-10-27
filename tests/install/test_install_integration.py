"""Real-subprocess integration tests for ``mcp_coder.install``.

Unlike ``test_install_phases.py`` (``--check`` dry-run only), these tests
call ``install()`` for real against a throwaway local fixture package, so
an actual ``uv venv`` / ``uv sync`` / ``uv pip install`` runs. The fixture
declares no dependencies and ``skip_overrides=True`` keeps the GitHub
overrides phase a no-op, so nothing beyond uv's own build backend needs
the network.

Scope: confirms the local+use_sync optimization (skipping
``phase_bootstrap_pip_uv``, see ``mcp_coder.install.install``) leaves the
final venv in the same shape ``uv sync`` would leave it in anyway, while
the local, non-sync (editable) path -- which nothing reconciles against a
lockfile -- still needs and keeps the bootstrapped pip/uv.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.install import InstallConfig, _env, install

from .conftest import namespace as _base_namespace

pytestmark = pytest.mark.install_integration


def _namespace(**overrides: Any) -> argparse.Namespace:
    """Build the Namespace add_install_parser would produce.

    Layers this module's local+sync-by-default needs on top of the
    shared helper's git/editable defaults.
    """
    local_defaults: dict[str, Any] = {
        "source": "local",
        "extras": "",
        "skip_overrides": True,
    }
    local_defaults.update(overrides)
    return _base_namespace(**local_defaults)


def _write_fixture_project(path: Path) -> None:
    """Write a trivial, dependency-free local package to install."""
    (path / "pyproject.toml").write_text(
        "[build-system]\n"
        'requires = ["setuptools>=61.0"]\n'
        'build-backend = "setuptools.build_meta"\n'
        "\n"
        "[project]\n"
        'name = "install-integration-fixture"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.11"\n'
        "\n"
        "[tool.setuptools]\n"
        'py-modules = ["install_integration_fixture"]\n',
        encoding="utf-8",
    )
    (path / "install_integration_fixture.py").write_text(
        "VALUE = 42\n", encoding="utf-8"
    )


def _import_value(py_v: Path) -> str:
    """Run `<py_v> -c "import <fixture>; print(VALUE)"` and return the output."""
    result = subprocess.run(
        [str(py_v), "-c", "import install_integration_fixture as m; print(m.VALUE)"],
        capture_output=True,
        text=True,
        check=True,
    )
    return str(result.stdout).strip()


@pytest.fixture(autouse=True)
def _require_system_uv() -> None:
    """Skip rather than let ensure_system_uv() auto-install uv onto PATH."""
    if shutil.which("uv") is None:
        pytest.skip("uv not on PATH")


class TestLocalInstallPaths:
    """Real ``uv`` runs for both local install flows."""

    def test_use_sync_installs_and_strips_pip_uv(self, tmp_path: Path) -> None:
        _write_fixture_project(tmp_path)
        install(
            InstallConfig.from_args(
                _namespace(target=tmp_path, local_path=tmp_path, use_sync=True)
            )
        )
        bin_dir = _env.venv_bin(tmp_path / ".venv")
        py_v = bin_dir / _env.exe("python")
        assert py_v.exists()
        assert _import_value(py_v) == "42"
        # uv sync reconciles the venv to the lockfile; pip/uv are not
        # declared dependencies of the fixture, so both end up absent.
        assert not (bin_dir / _env.exe("pip")).exists()
        assert not (bin_dir / _env.exe("uv")).exists()

    def test_editable_install_keeps_bootstrapped_pip_uv(self, tmp_path: Path) -> None:
        _write_fixture_project(tmp_path)
        install(
            InstallConfig.from_args(
                _namespace(target=tmp_path, local_path=tmp_path, use_sync=False)
            )
        )
        bin_dir = _env.venv_bin(tmp_path / ".venv")
        py_v = bin_dir / _env.exe("python")
        assert py_v.exists()
        assert _import_value(py_v) == "42"
        # Nothing here reconciles the venv against a lockfile, so the
        # bootstrapped pip/uv survive -- this path still needs
        # phase_bootstrap_pip_uv.
        assert (bin_dir / _env.exe("pip")).exists()
        assert (bin_dir / _env.exe("uv")).exists()
