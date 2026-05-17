"""Unit tests for tools/install.py — the unified installer entry point.

These tests cover the logic previously exercised by
``tests/workflows/vscodeclaude/test_build_github_install_section.py``
(deleted when its functions moved into install.py). They lean on
install.py's ``--check`` dry-run mode, which prints every command it
would run without executing anything; tests capture stdout and assert
on the emitted ``> uv pip install ...`` lines.

Shell-quoting note: the deleted POSIX tests verified ``shlex.quote``
on metacharacter-laced package specs. install.py uses
``subprocess.run([...])`` with an argv list (no shell), so shell
injection is impossible by construction. That coverage is no longer
needed; correctness is enforced by the argv API itself.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

# Load install.py as a module without adding it to sys.path globally.
# (Pytest's pythonpath = ["src"]; tools/install.py lives outside that.)
_INSTALL_PY = Path(__file__).resolve().parents[2] / "tools" / "install.py"


def _load_install_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("install_py", _INSTALL_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


install = _load_install_module()


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


class TestGithubOverridesParser:
    """Parsing [tool.mcp-coder.install-from-github] from pyproject.toml."""

    def test_returns_packages_and_packages_no_deps(self, tmp_path: Path) -> None:
        _write_pyproject(
            tmp_path,
            packages=[
                "pkg1 @ git+https://github.com/org/pkg1.git",
                "pkg2 @ git+https://github.com/org/pkg2.git",
            ],
            packages_no_deps=["pkg3 @ git+https://github.com/org/pkg3.git"],
        )
        pkgs, pkgs_no_deps = install.github_overrides(tmp_path)
        assert pkgs == [
            "pkg1 @ git+https://github.com/org/pkg1.git",
            "pkg2 @ git+https://github.com/org/pkg2.git",
        ]
        assert pkgs_no_deps == ["pkg3 @ git+https://github.com/org/pkg3.git"]

    def test_empty_lists_when_section_missing(self, tmp_path: Path) -> None:
        # pyproject.toml exists but has no [tool.mcp-coder.install-from-github]
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\nversion = "0.1.0"\n', encoding="utf-8"
        )
        pkgs, pkgs_no_deps = install.github_overrides(tmp_path)
        assert pkgs == []
        assert pkgs_no_deps == []

    def test_empty_lists_when_pyproject_missing(self, tmp_path: Path) -> None:
        pkgs, pkgs_no_deps = install.github_overrides(tmp_path)
        assert pkgs == []
        assert pkgs_no_deps == []

    def test_only_packages_field(self, tmp_path: Path) -> None:
        _write_pyproject(
            tmp_path,
            packages=["pkg1 @ git+https://github.com/org/pkg1.git"],
        )
        pkgs, pkgs_no_deps = install.github_overrides(tmp_path)
        assert pkgs == ["pkg1 @ git+https://github.com/org/pkg1.git"]
        assert pkgs_no_deps == []

    def test_only_packages_no_deps_field(self, tmp_path: Path) -> None:
        _write_pyproject(
            tmp_path,
            packages_no_deps=["pkg3 @ git+https://github.com/org/pkg3.git"],
        )
        pkgs, pkgs_no_deps = install.github_overrides(tmp_path)
        assert pkgs == []
        assert pkgs_no_deps == ["pkg3 @ git+https://github.com/org/pkg3.git"]


def _run_install_check(argv: list[str], capsys: pytest.CaptureFixture[str]) -> str:
    """Invoke install.main([...]) with --check appended and return stdout."""
    install.main([*argv, "--check"])
    return capsys.readouterr().out


def _emitted_commands(stdout: str) -> list[str]:
    """Extract the `> ...` command lines run() prints in --check mode."""
    return [line[2:].rstrip() for line in stdout.splitlines() if line.startswith("> ")]


class TestPhaseOverridesDryRun:
    """End-to-end coverage of _phase_overrides via main(--check).

    Verifies the commands install.py *would* run for a given
    pyproject.toml, without spawning any subprocesses.
    """

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
        out = _run_install_check(
            [
                str(tmp_path),
                "--source",
                "local",
                "--local-path",
                str(tmp_path),
                "--extras",
                "",
                "--skip-templates",
            ],
            capsys,
        )
        cmds = _emitted_commands(out)
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
        out = _run_install_check(
            [
                str(tmp_path),
                "--source",
                "local",
                "--local-path",
                str(tmp_path),
                "--extras",
                "",
                "--skip-templates",
            ],
            capsys,
        )
        cmds = _emitted_commands(out)
        joined = "\n".join(cmds)
        # --no-deps install must appear AND must include pkg3
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
        out = _run_install_check(
            [
                str(tmp_path),
                "--source",
                "local",
                "--local-path",
                str(tmp_path),
                "--extras",
                "",
                "--skip-templates",
            ],
            capsys,
        )
        cmds = _emitted_commands(out)
        # Find the override command index and the editable re-link index.
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
        out = _run_install_check(
            [
                str(tmp_path),
                "--source",
                "local",
                "--local-path",
                str(tmp_path),
                "--extras",
                "",
                "--skip-templates",
                "--skip-overrides",
            ],
            capsys,
        )
        cmds = _emitted_commands(out)
        joined = "\n".join(cmds)
        # Neither override spec must appear anywhere.
        assert "pkg1 @ git+https" not in joined
        assert "pkg3 @ git+https" not in joined

    def test_missing_pyproject_section_no_override_commands(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # pyproject without the section
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\nversion = "0.1.0"\n', encoding="utf-8"
        )
        out = _run_install_check(
            [
                str(tmp_path),
                "--source",
                "local",
                "--local-path",
                str(tmp_path),
                "--extras",
                "",
                "--skip-templates",
            ],
            capsys,
        )
        cmds = _emitted_commands(out)
        joined = "\n".join(cmds)
        # No git+https line — overrides ran but the parser returned empty lists.
        assert "git+https" not in joined

    def test_use_sync_emits_sync_command(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """With --use-sync, install.py emits `uv sync --extra dev`.

        (The editable re-link `uv pip install -e <path> --no-deps`
        also runs unconditionally inside _phase_overrides when
        is_editable=True — that's covered by
        test_editable_relink_runs_after_overrides.)
        """
        _write_pyproject(tmp_path, packages=[], packages_no_deps=[])
        out = _run_install_check(
            [
                str(tmp_path),
                "--source",
                "local",
                "--local-path",
                str(tmp_path),
                "--extras",
                "dev",
                "--use-sync",
                "--skip-templates",
            ],
            capsys,
        )
        cmds = _emitted_commands(out)
        sync_lines = [c for c in cmds if " sync " in f" {c} "]
        assert sync_lines, f"expected `uv sync` line in:\n{cmds}"
        assert any("--extra" in c and "dev" in c for c in sync_lines)


class TestUseSyncTargetGuard:
    """The --use-sync guard added to main(): target must == local_path."""

    def test_mismatch_exits_with_error_message(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        other = tmp_path / "other"
        other.mkdir()
        with pytest.raises(SystemExit) as exc_info:
            install.main(
                [
                    str(tmp_path),
                    "--source",
                    "local",
                    "--local-path",
                    str(other),
                    "--use-sync",
                    "--skip-templates",
                    "--check",
                ]
            )
        # SystemExit message goes to stderr/stdout depending on the form;
        # SystemExit("string") sets .code to that string.
        assert "--use-sync" in str(exc_info.value)
        assert "local-path" in str(exc_info.value)

    def test_matching_paths_pass_guard(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _write_pyproject(tmp_path)
        # Should not raise on matching paths.
        install.main(
            [
                str(tmp_path),
                "--source",
                "local",
                "--local-path",
                str(tmp_path),
                "--use-sync",
                "--skip-templates",
                "--check",
            ]
        )
