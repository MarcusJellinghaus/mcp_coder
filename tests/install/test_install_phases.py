"""Unit tests for mcp_coder.install._phases and the install() driver.

These tests lean on ``--check`` dry-run mode, which logs every command the
installer would run without executing anything; they read the log records
and assert on the emitted ``> uv pip install ...`` lines.

Shell-quoting note: the installer uses ``subprocess.run([...])`` with an argv
list (no shell), so shell injection is impossible by construction.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.install import InstallConfig, _env, _phases, install
from mcp_coder.install._env import REPORT_BINARIES, UV_TRANSIENT_SIGNATURES, exe
from mcp_coder.utils.log_utils import OUTPUT

from .conftest import namespace as _namespace

# Stands in for a real uv binary wherever the installer looks one up.
_STUB_UV = "/stub/bin/uv"


@pytest.fixture(autouse=True)
def _capture_install_output(caplog: pytest.LogCaptureFixture) -> None:
    """Let caplog see install's OUTPUT records; the root level (WARNING) drops them."""
    caplog.set_level(OUTPUT, logger="mcp_coder.install")


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


def _run_install_check(caplog: pytest.LogCaptureFixture, **overrides: Any) -> list[str]:
    """Run install() in dry-run mode and return the emitted `> ...` lines."""
    install(InstallConfig.from_args(_namespace(check=True, **overrides)))
    return [m[2:].rstrip() for m in caplog.messages if m.startswith("> ")]


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
        monkeypatch.setattr(shutil, "which", lambda _: _STUB_UV)

    def test_with_deps_packages_emit_install_command(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        _write_pyproject(
            tmp_path,
            packages=[
                "pkg1 @ git+https://github.com/org/pkg1.git",
                "pkg2 @ git+https://github.com/org/pkg2.git",
            ],
        )
        cmds = _run_install_check(
            caplog,
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
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        _write_pyproject(
            tmp_path,
            packages_no_deps=["pkg3 @ git+https://github.com/org/pkg3.git"],
        )
        cmds = _run_install_check(
            caplog,
            target=tmp_path,
            source="local",
            local_path=tmp_path,
            extras="",
        )
        joined = "\n".join(cmds)
        no_deps_pkg = [c for c in cmds if "--no-deps" in c and "pkg3" in c]
        assert no_deps_pkg, f"expected --no-deps line with pkg3 in:\n{joined}"

    def test_editable_relink_runs_after_overrides(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
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
            caplog,
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
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        _write_pyproject(
            tmp_path,
            packages=["pkg1 @ git+https://github.com/org/pkg1.git"],
            packages_no_deps=["pkg3 @ git+https://github.com/org/pkg3.git"],
        )
        cmds = _run_install_check(
            caplog,
            target=tmp_path,
            source="local",
            local_path=tmp_path,
            extras="",
            skip_overrides=True,
        )
        joined = "\n".join(cmds)
        assert any(" -e " in f" {c} " for c in cmds), (
            f"no editable install in:\n{joined}"
        )
        assert "pkg1 @ git+https" not in joined
        assert "pkg3 @ git+https" not in joined

    def test_missing_pyproject_section_no_override_commands(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        _write_pyproject(tmp_path)
        cmds = _run_install_check(
            caplog,
            target=tmp_path,
            source="local",
            local_path=tmp_path,
            extras="",
        )
        assert any(" -e " in f" {c} " for c in cmds), f"no editable install in:\n{cmds}"
        # No git+https line — overrides ran but the reader returned empty lists.
        assert "git+https" not in "\n".join(cmds)

    def test_absent_overrides_are_reported(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
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
        out = "\n".join(caplog.messages)
        assert "skipping GitHub overrides" in out
        assert "install-from-github" in out
        # One record = one line: no message carries its own leading blank line.
        assert "--- installed versions" in caplog.messages
        assert (
            f"OK  mcp-coder install complete: {tmp_path.resolve()}" in caplog.messages
        )
        assert not [m for m in caplog.messages if m.startswith("\n")]

    def test_use_sync_emits_sync_command(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """With --use-sync, the installer emits `uv sync --extra dev`.

        (The editable re-link `uv pip install -e <path> --no-deps`
        also runs unconditionally inside phase_overrides when
        is_editable=True — that's covered by
        test_editable_relink_runs_after_overrides.)
        """
        _write_pyproject(tmp_path, packages=[], packages_no_deps=[])
        cmds = _run_install_check(
            caplog,
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
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        _write_pyproject(tmp_path)
        cmds = _run_install_check(
            caplog,
            target=tmp_path,
            source="local",
            local_path=tmp_path,
            extras="",
            extra_packages="langchain mlflow",
        )
        joined = "\n".join(cmds)
        assert "langchain" in joined
        assert "mlflow" in joined

    def test_non_table_install_from_github_raises(self, tmp_path: Path) -> None:
        """A non-table install-from-github is a ValueError naming file and key."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            "[tool.mcp-coder]\ninstall-from-github = 1\n", encoding="utf-8"
        )
        config = InstallConfig.from_args(
            _namespace(
                check=True,
                target=tmp_path,
                source="local",
                local_path=tmp_path,
                extras="",
            )
        )
        with pytest.raises(ValueError) as exc_info:
            _phases.phase_overrides(
                config, _STUB_UV, tmp_path / "python", is_editable=False
            )
        message = str(exc_info.value)
        assert str(pyproject) in message
        assert "'install-from-github'" in message
        assert "expected a table" in message


class TestBootstrapSkippedOnlyForLocalSync:
    """Regression test for the Windows uv.exe write-then-delete race.

    The local+use_sync path runs `uv sync`, which reconciles the venv to
    the lockfile and strips pip/uv right back out since they are not
    project dependencies. Bootstrapping them first (phase_bootstrap_pip_uv)
    therefore only writes uv.exe for `uv sync` to delete a moment later --
    on Windows that delete can lose a race with an AV scan of the
    freshly-written exe and fail the whole install. install() skips the
    bootstrap phase for exactly this one config; every other source/sync
    combination still needs it.
    """

    @pytest.fixture(autouse=True)
    def _stub_uv_lookup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "mcp_coder.install.ensure_system_uv", lambda: _STUB_UV, raising=True
        )
        monkeypatch.setattr(shutil, "which", lambda _: _STUB_UV)

    def test_skipped_for_local_use_sync(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[object] = []
        monkeypatch.setattr(
            "mcp_coder.install.phase_bootstrap_pip_uv",
            lambda *a, **_k: calls.append(a),
            raising=True,
        )
        install(
            InstallConfig.from_args(
                _namespace(
                    check=True,
                    target=tmp_path,
                    source="local",
                    local_path=tmp_path,
                    use_sync=True,
                )
            )
        )
        assert calls == []

    @pytest.mark.parametrize("source", ["git", "pypi", "local"])
    def test_runs_for_every_other_source(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source: str
    ) -> None:
        calls: list[object] = []
        monkeypatch.setattr(
            "mcp_coder.install.phase_bootstrap_pip_uv",
            lambda *a, **_k: calls.append(a),
            raising=True,
        )
        overrides: dict[str, Any] = {
            "check": True,
            "target": tmp_path,
            "source": source,
        }
        if source == "local":
            # use_sync defaults to False -- this is the editable-install path.
            overrides["local_path"] = tmp_path
        install(InstallConfig.from_args(_namespace(**overrides)))
        assert len(calls) == 1


def _is_uv_install(cmd: list[str]) -> bool:
    """True for a system-uv ``pip install`` or ``sync`` command."""
    return cmd[0] == _STUB_UV and (cmd[1:3] == ["pip", "install"] or cmd[1] == "sync")


class TestRetryCallSites:
    """Exactly the uv install/sync commands opt into the transient-error retry.

    Every other command (venv creation, the in-venv pip fallback, the
    version report) must keep the plain inherited-stdio path.
    """

    @pytest.mark.parametrize(
        ("overrides", "which", "pyproject"),
        [
            pytest.param({"source": "git"}, _STUB_UV, False, id="git"),
            pytest.param({"source": "pypi"}, _STUB_UV, False, id="pypi"),
            pytest.param(
                {"source": "local", "extra_packages": "langchain"},
                _STUB_UV,
                True,
                id="local-editable-overrides-extra-packages",
            ),
            pytest.param(
                {"source": "local", "use_sync": True},
                _STUB_UV,
                False,
                id="local-use-sync",
            ),
            pytest.param({"source": "git"}, None, False, id="git-no-uv-on-path"),
        ],
    )
    def test_retry_on_only_for_uv_install_and_sync(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        overrides: dict[str, Any],
        which: str | None,
        pyproject: bool,
    ) -> None:
        calls: list[tuple[list[str], dict[str, Any]]] = []

        def _rec(cmd: list[str], **kwargs: Any) -> int:
            calls.append((cmd, kwargs))
            return 0

        monkeypatch.setattr("mcp_coder.install._phases.run", _rec, raising=True)
        monkeypatch.setattr("mcp_coder.install.run", _rec, raising=True)
        monkeypatch.setattr(
            "mcp_coder.install.ensure_system_uv", lambda: _STUB_UV, raising=True
        )
        monkeypatch.setattr(shutil, "which", lambda _: which)
        if pyproject:
            _write_pyproject(
                tmp_path,
                packages=["pkg1 @ git+https://github.com/org/pkg1.git"],
                packages_no_deps=["pkg3 @ git+https://github.com/org/pkg3.git"],
            )
        if overrides["source"] == "local":
            overrides = {**overrides, "local_path": tmp_path}

        install(
            InstallConfig.from_args(
                _namespace(target=tmp_path, check=False, **overrides)
            )
        )

        assert any(_is_uv_install(cmd) for cmd, _ in calls), calls
        assert any(not _is_uv_install(cmd) for cmd, _ in calls), calls
        for cmd, kwargs in calls:
            assert (
                kwargs.get("retry_on") == UV_TRANSIENT_SIGNATURES
            ) == _is_uv_install(cmd), cmd


class TestEnsureSystemUv:
    """Auto-install fallback for missing system uv."""

    def test_uv_already_on_path_returns_immediately(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Happy path: shutil.which finds uv, no subprocess attempted."""
        monkeypatch.setattr(shutil, "which", lambda _: "/fake/path/to/uv")

        def _no_subprocess(*args: object, **kwargs: object) -> None:
            raise AssertionError("subprocess.run should not be called")

        monkeypatch.setattr(subprocess, "run", _no_subprocess)
        assert _env.ensure_system_uv() == "/fake/path/to/uv"

    def test_auto_install_succeeds_and_uv_appears_on_path(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """pip install succeeds, then shutil.which finds the new uv."""
        which_results = iter([None, "/home/user/.venv/bin/uv"])
        monkeypatch.setattr(shutil, "which", lambda _: next(which_results))

        called: list[list[str]] = []

        def _fake_run(cmd: list[str], **_kwargs: object) -> object:
            called.append(cmd)
            return type("R", (), {"returncode": 0})()

        monkeypatch.setattr(subprocess, "run", _fake_run)

        result = _env.ensure_system_uv()
        assert result == "/home/user/.venv/bin/uv"
        assert any("pip" in c and "install" in c and "uv" in c for c in called)

    def test_auto_install_fails_exits_with_helpful_message(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """pip install raises CalledProcessError → SystemExit with the docs URL."""
        monkeypatch.setattr(shutil, "which", lambda _: None)

        def _fake_run(cmd: list[str], **_kwargs: object) -> object:
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd)

        monkeypatch.setattr(subprocess, "run", _fake_run)

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
        monkeypatch.setattr(shutil, "which", lambda _: None)

        def _fake_run(cmd: list[str], **_kwargs: object) -> object:
            raise FileNotFoundError("pip not found")

        monkeypatch.setattr(subprocess, "run", _fake_run)

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
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        bin_dir = self._make_bin_dir(tmp_path, ["mcp-coder"])
        self._run(monkeypatch, tmp_path, bin_dir)  # must not raise
        for name in REPORT_BINARIES:
            if name != "mcp-coder":
                assert f"  (not installed: {name})" in caplog.messages

    def test_present_binaries_are_queried(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        bin_dir = self._make_bin_dir(tmp_path, list(REPORT_BINARIES))
        calls = self._run(monkeypatch, tmp_path, bin_dir)
        assert "--- installed versions" in caplog.messages
        assert not [m for m in caplog.messages if "not installed" in m]
        version_calls = [c for c in calls if c[-1] == "--version"]
        assert len(version_calls) == len(REPORT_BINARIES)

    def test_check_mode_skips_the_report(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        bin_dir = self._make_bin_dir(tmp_path, [])
        monkeypatch.setattr(_phases, "run", lambda *_a, **_kw: 0)
        config = InstallConfig.from_args(_namespace(target=tmp_path, check=True))
        _phases.phase_report_versions(config, bin_dir, "uv", bin_dir / exe("python"))
        assert "  (skipped in --check mode)" in caplog.messages
