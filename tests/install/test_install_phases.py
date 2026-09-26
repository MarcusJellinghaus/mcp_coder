"""Unit tests for mcp_coder.install._phases and the install() driver.

These tests lean on ``--check`` dry-run mode, which prints every command the
installer would run without executing anything; they capture stdout and
assert on the emitted ``> uv pip install ...`` lines.

Shell-quoting note: the installer uses ``subprocess.run([...])`` with an argv
list (no shell), so shell injection is impossible by construction.

Subprocess note: ``_env.subprocess`` is reached as a module attribute on
purpose. The ``subprocess_isolation`` import-linter contract grants
``tests.install`` no exemption, so a bare ``import subprocess`` here would
break it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.install import InstallConfig, _env, _phases, install
from mcp_coder.install._env import REPORT_BINARIES, exe

# Reached through getattr rather than `_env.shutil` / `_env.subprocess`:
# mypy's no-implicit-reexport rejects the attribute form, and importing
# subprocess here directly would break the subprocess_isolation contract,
# which grants tests.install no exemption.
_shutil = getattr(_env, "shutil")
_subprocess = getattr(_env, "subprocess")

# Stands in for a real uv binary wherever the installer looks one up.
_STUB_UV = "/stub/bin/uv"


def _namespace(**overrides: Any) -> argparse.Namespace:
    """Build the Namespace add_install_parser would produce."""
    defaults: dict[str, Any] = {
        "target": Path("."),
        "source": "git",
        "ref": "main",
        "local_path": None,
        "extras": None,
        "extra_packages": "",
        "use_sync": False,
        "skip_overrides": False,
        "refresh": False,
        "clean": False,
        "python": sys.executable,
        "check": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _write_pyproject(
    tmp_path: Path,
    packages: list[str] | None = None,
    packages_no_deps: list[str] | None = None,
) -> None:
    """Write a pyproject.toml with [tool.mcp-coder.install-from-github] section."""
    lines = ['[project]\nname = "test-project"\nversion = "0.1.0"\n']
    if packages is not None or packages_no_deps is not None:
        lines.append("[tool.mcp-coder.install-from-github]\n")
        if packages is not None:
            items = ", ".join(f'"{p}"' for p in packages)
            lines.append(f"packages = [{items}]\n")
        if packages_no_deps is not None:
            items = ", ".join(f'"{p}"' for p in packages_no_deps)
            lines.append(f"packages-no-deps = [{items}]\n")
    (tmp_path / "pyproject.toml").write_text("\n".join(lines), encoding="utf-8")


def _run_install_check(
    capsys: pytest.CaptureFixture[str], **overrides: Any
) -> list[str]:
    """Run install() in dry-run mode and return the emitted `> ...` lines."""
    install(InstallConfig.from_args(_namespace(check=True, **overrides)))
    stdout = capsys.readouterr().out
    return [line[2:].rstrip() for line in stdout.splitlines() if line.startswith("> ")]


class TestPhaseOverridesDryRun:
    """End-to-end coverage of phase_overrides via install(check=True).

    Verifies the commands the installer *would* run for a given
    pyproject.toml, without spawning any subprocesses.
    """

    @pytest.fixture(autouse=True)
    def _stub_uv_lookup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Keep the dry run hermetic by pinning every uv probe.

        ``--check`` suppresses the phase commands but not the lookups around
        them: ``install()`` calls ``ensure_system_uv`` before the first phase,
        which shells out to ``pip install uv`` and may ``sys.exit`` when uv is
        absent, and the first two phases branch on ``shutil.which('uv')``.
        Unstubbed, these tests would touch the real environment and emit
        different commands depending on whether uv happens to be on PATH.
        """
        monkeypatch.setattr(
            "mcp_coder.install.ensure_system_uv", lambda: _STUB_UV, raising=True
        )
        monkeypatch.setattr(_shutil, "which", lambda _: _STUB_UV)

    def test_with_deps_packages_emit_install_command(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _write_pyproject(
            tmp_path,
            packages=[
                "pkg1 @ git+https://github.com/org/pkg1.git",
                "pkg2 @ git+https://github.com/org/pkg2.git",
            ],
        )
        cmds = _run_install_check(
            capsys,
            target=tmp_path,
            source="local",
            local_path=tmp_path,
            extras="",
        )
        # The override install line contains both with-deps specs (single uv pip install).
        joined = "\n".join(cmds)
        assert "pkg1 @ git+https://github.com/org/pkg1.git" in joined
        assert "pkg2 @ git+https://github.com/org/pkg2.git" in joined
        # No --no-deps because packages-no-deps was not set.
        no_deps_lines = [c for c in cmds if "--no-deps" in c and "pkg" in c]
        # The editable re-link uses --no-deps too, but with -e, so filter:
        no_deps_pkg_lines = [c for c in no_deps_lines if "git+https" in c]
        assert no_deps_pkg_lines == []

    def test_packages_no_deps_emit_no_deps_install(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _write_pyproject(
            tmp_path,
            packages_no_deps=["pkg3 @ git+https://github.com/org/pkg3.git"],
        )
        cmds = _run_install_check(
            capsys,
            target=tmp_path,
            source="local",
            local_path=tmp_path,
            extras="",
        )
        joined = "\n".join(cmds)
        no_deps_pkg = [c for c in cmds if "--no-deps" in c and "pkg3" in c]
        assert no_deps_pkg, f"expected --no-deps line with pkg3 in:\n{joined}"

    def test_editable_relink_runs_after_overrides(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """After overrides apply, editable install of mcp-coder must be re-linked.

        Otherwise the override step may have pulled a fresh mcp-coder wheel
        in transitively and shadowed the editable install.
        """
        _write_pyproject(
            tmp_path,
            packages=["pkg1 @ git+https://github.com/org/pkg1.git"],
        )
        cmds = _run_install_check(
            capsys,
            target=tmp_path,
            source="local",
            local_path=tmp_path,
            extras="",
        )
        override_idx = next(
            (i for i, c in enumerate(cmds) if "pkg1 @ git+https" in c), None
        )
        relink_idx = next(
            (
                i
                for i, c in enumerate(cmds)
                if "-e" in c and "--no-deps" in c and str(tmp_path) in c
            ),
            None,
        )
        assert override_idx is not None, f"no override command in:\n{cmds}"
        assert relink_idx is not None, f"no editable re-link command in:\n{cmds}"
        assert relink_idx > override_idx, "editable re-link must run AFTER overrides"

    def test_skip_overrides_suppresses_section(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _write_pyproject(
            tmp_path,
            packages=["pkg1 @ git+https://github.com/org/pkg1.git"],
            packages_no_deps=["pkg3 @ git+https://github.com/org/pkg3.git"],
        )
        cmds = _run_install_check(
            capsys,
            target=tmp_path,
            source="local",
            local_path=tmp_path,
            extras="",
            skip_overrides=True,
        )
        joined = "\n".join(cmds)
        assert "pkg1 @ git+https" not in joined
        assert "pkg3 @ git+https" not in joined

    def test_missing_pyproject_section_no_override_commands(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _write_pyproject(tmp_path)
        cmds = _run_install_check(
            capsys,
            target=tmp_path,
            source="local",
            local_path=tmp_path,
            extras="",
        )
        # No git+https line — overrides ran but the reader returned empty lists.
        assert "git+https" not in "\n".join(cmds)

    def test_absent_overrides_are_reported(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Declaring no overrides is announced, not passed over in silence."""
        _write_pyproject(tmp_path)
        install(
            InstallConfig.from_args(
                _namespace(
                    check=True,
                    target=tmp_path,
                    source="local",
                    local_path=tmp_path,
                    extras="",
                )
            )
        )
        out = capsys.readouterr().out
        assert "skipping GitHub overrides" in out
        assert "install-from-github" in out

    def test_use_sync_emits_sync_command(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """With --use-sync, the installer emits `uv sync --extra dev`.

        (The editable re-link `uv pip install -e <path> --no-deps`
        also runs unconditionally inside phase_overrides when
        is_editable=True — that's covered by
        test_editable_relink_runs_after_overrides.)
        """
        _write_pyproject(tmp_path, packages=[], packages_no_deps=[])
        cmds = _run_install_check(
            capsys,
            target=tmp_path,
            source="local",
            local_path=tmp_path,
            extras="dev",
            use_sync=True,
        )
        sync_lines = [c for c in cmds if " sync " in f" {c} "]
        assert sync_lines, f"expected `uv sync` line in:\n{cmds}"
        assert any("--extra" in c and "dev" in c for c in sync_lines)

    def test_extra_packages_are_installed(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _write_pyproject(tmp_path)
        cmds = _run_install_check(
            capsys,
            target=tmp_path,
            source="local",
            local_path=tmp_path,
            extras="",
            extra_packages="langchain mlflow",
        )
        joined = "\n".join(cmds)
        assert "langchain" in joined
        assert "mlflow" in joined


class TestEnsureSystemUv:
    """Auto-install fallback for missing system uv."""

    def test_uv_already_on_path_returns_immediately(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Happy path: shutil.which finds uv, no subprocess attempted."""
        monkeypatch.setattr(_shutil, "which", lambda _: "/fake/path/to/uv")

        def _no_subprocess(*args: object, **kwargs: object) -> None:
            raise AssertionError("subprocess.run should not be called")

        monkeypatch.setattr(_subprocess, "run", _no_subprocess)
        assert _env.ensure_system_uv() == "/fake/path/to/uv"

    def test_auto_install_succeeds_and_uv_appears_on_path(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """pip install succeeds, then shutil.which finds the new uv."""
        which_results = iter([None, "/home/user/.venv/bin/uv"])
        monkeypatch.setattr(_shutil, "which", lambda _: next(which_results))

        called: list[list[str]] = []

        def _fake_run(cmd: list[str], **_kwargs: object) -> object:
            called.append(cmd)
            return type("R", (), {"returncode": 0})()

        monkeypatch.setattr(_subprocess, "run", _fake_run)

        result = _env.ensure_system_uv()
        assert result == "/home/user/.venv/bin/uv"
        assert any("pip" in c and "install" in c and "uv" in c for c in called)

    def test_auto_install_fails_exits_with_helpful_message(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """pip install raises CalledProcessError → SystemExit with the docs URL."""
        monkeypatch.setattr(_shutil, "which", lambda _: None)

        def _fake_run(cmd: list[str], **_kwargs: object) -> object:
            raise _subprocess.CalledProcessError(returncode=1, cmd=cmd)

        monkeypatch.setattr(_subprocess, "run", _fake_run)

        with pytest.raises(SystemExit) as exc_info:
            _env.ensure_system_uv()
        msg = str(exc_info.value)
        assert "mcp-coder install" in msg
        assert "pip install uv" in msg
        assert "astral.sh" in msg

    def test_pip_missing_also_exits_cleanly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """FileNotFoundError (pip itself absent) is handled the same way."""
        monkeypatch.setattr(_shutil, "which", lambda _: None)

        def _fake_run(cmd: list[str], **_kwargs: object) -> object:
            raise FileNotFoundError("pip not found")

        monkeypatch.setattr(_subprocess, "run", _fake_run)

        with pytest.raises(SystemExit) as exc_info:
            _env.ensure_system_uv()
        assert "astral.sh" in str(exc_info.value)


class TestPhaseVersions:
    """The post-install version report never fails the install.

    Every binary in REPORT_BINARIES is reported when present and named as
    not installed when absent; only projects that ask for a given binary
    pull it in, so absence is information rather than an error.
    """

    @staticmethod
    def _make_bin_dir(tmp_path: Path, names: list[str]) -> Path:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(parents=True)
        for name in names:
            (bin_dir / exe(name)).write_text("", encoding="utf-8")
        return bin_dir

    @staticmethod
    def _run(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, bin_dir: Path
    ) -> list[list[str]]:
        """Call phase_report_versions with subprocess execution stubbed out."""
        calls: list[list[str]] = []

        def _fake_run(cmd: list[str], **_kwargs: object) -> int:
            calls.append(cmd)
            return 0

        monkeypatch.setattr(_phases, "run", _fake_run)
        config = InstallConfig.from_args(_namespace(target=tmp_path))
        _phases.phase_report_versions(config, bin_dir, "uv", bin_dir / exe("python"))
        return calls

    def test_missing_binary_is_reported_and_install_continues(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        bin_dir = self._make_bin_dir(tmp_path, ["mcp-coder"])
        self._run(monkeypatch, tmp_path, bin_dir)  # must not raise
        out = capsys.readouterr().out
        for name in REPORT_BINARIES:
            if name != "mcp-coder":
                assert f"(not installed: {name})" in out

    def test_present_binaries_are_queried(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        bin_dir = self._make_bin_dir(tmp_path, list(REPORT_BINARIES))
        calls = self._run(monkeypatch, tmp_path, bin_dir)
        assert "not installed" not in capsys.readouterr().out
        version_calls = [c for c in calls if c[-1] == "--version"]
        assert len(version_calls) == len(REPORT_BINARIES)

    def test_check_mode_skips_the_report(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        bin_dir = self._make_bin_dir(tmp_path, [])
        monkeypatch.setattr(_phases, "run", lambda *_a, **_kw: 0)
        config = InstallConfig.from_args(_namespace(target=tmp_path, check=True))
        _phases.phase_report_versions(config, bin_dir, "uv", bin_dir / exe("python"))
        assert "(skipped in --check mode)" in capsys.readouterr().out
